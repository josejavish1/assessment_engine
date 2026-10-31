"""Stateful Artifact Registry managing atomic manifest and cryptographic storage."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import threading
from typing import Any, Generator

from assessment_engine.infrastructure.artifacts.domain import (
    ArtifactContext,
    ArtifactFormat,
    ArtifactIntegrityError,
    ArtifactNotFoundError,
    ArtifactVersionRecord,
    DocumentType,
)
from assessment_engine.infrastructure.artifacts.resolver import ArtifactPathResolver

logger = logging.getLogger(__name__)

_IN_MEMORY_LOCK = threading.Lock()


class ArtifactRegistry:
    """Enterprise artifact manager ensuring cryptographic tracking and atomic manifests."""

    def __init__(
        self,
        base_storage_dir: Path,
        tenant_id: str,
        assessment_id: str,
    ) -> None:
        """Initialize registry under dedicated assessment root directory."""
        self.tenant_id = ArtifactPathResolver.sanitize_token(tenant_id)
        self.assessment_id = ArtifactPathResolver.sanitize_token(assessment_id)
        self.assessment_root = (
            Path(base_storage_dir) / self.tenant_id / self.assessment_id
        )
        self.artifacts_dir = self.assessment_root / "artifacts"
        self.manifest_path = self.assessment_root / "manifest.json"
        self.lock_path = self.assessment_root / "manifest.lock"

        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _acquire_lock(self) -> Generator[None, None, None]:
        """Acquire concurrent file lock ensuring cross-process atomic manifest mutations."""
        with _IN_MEMORY_LOCK:
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_fd = None
            try:
                # Open or create lock file descriptor
                lock_fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR)
                try:
                    import fcntl
                    fcntl.flock(lock_fd, fcntl.LOCK_EX)
                except ImportError:
                    try:
                        import msvcrt
                        msvcrt.locking(lock_fd, msvcrt.LK_LOCK, 1)
                    except (ImportError, OSError):
                        pass
                yield
            finally:
                if lock_fd is not None:
                    try:
                        import fcntl
                        fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    except (ImportError, OSError):
                        try:
                            import msvcrt
                            msvcrt.locking(lock_fd, msvcrt.LK_UNLCK, 1)
                        except (ImportError, OSError):
                            pass
                    try:
                        os.close(lock_fd)
                    except OSError:
                        pass

    @staticmethod
    def compute_sha256(file_path: Path, chunk_size: int = 65536) -> str:
        """Compute streaming SHA-256 checksum to prevent OOM on large deliverable binaries."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest().lower()

    def _load_manifest_unlocked(self) -> dict[str, Any]:
        """Load manifest JSON or return clean baseline if uninitialized."""
        if not self.manifest_path.exists():
            return {
                "schema_version": "1.0.0",
                "tenant_id": self.tenant_id,
                "assessment_id": self.assessment_id,
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
                "artifacts": {},
            }
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as ex:
            if self.manifest_path.exists() and self.manifest_path.stat().st_size > 0:
                backup_corrupted = self.manifest_path.with_suffix(
                    f".corrupted.{int(datetime.now(timezone.utc).timestamp())}.json"
                )
                try:
                    shutil.copy2(self.manifest_path, backup_corrupted)
                    logger.warning(
                        "Corrupted manifest backed up to %s: %s", backup_corrupted, ex
                    )
                except OSError:
                    pass
            logger.error("Corrupted manifest found at %s: %s", self.manifest_path, ex)
            return {
                "schema_version": "1.0.0",
                "tenant_id": self.tenant_id,
                "assessment_id": self.assessment_id,
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
                "artifacts": {},
            }

    def _save_manifest_atomic_unlocked(self, manifest_data: dict[str, Any]) -> None:
        """Atomically commit manifest to disk using fsync and atomic os.replace."""
        manifest_data["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        tmp_file = self.manifest_path.with_suffix(
            f".{os.getpid()}.{threading.get_ident()}.tmp"
        )
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_file, self.manifest_path)

    def register_artifact(
        self,
        ctx: ArtifactContext,
        source_file_path: Path,
        generator_engine: str = "assessment_engine_v1",
        presentation_metadata: dict[str, Any] | None = None,
    ) -> ArtifactVersionRecord:
        """Register deliverable artifact into storage, tracking version and cryptographic hash.

        If an artifact with identical checksum already exists as the latest version,
        the registration is strictly idempotent and returns the existing record.
        """
        source_path = Path(source_file_path)
        if not source_path.exists() or source_path.stat().st_size == 0:
            raise FileNotFoundError(f"Source deliverable at {source_path} is missing or empty.")

        sha256_full = self.compute_sha256(source_path)
        size_bytes = source_path.stat().st_size
        logical_key = ArtifactPathResolver.build_logical_key(ctx)

        with self._acquire_lock():
            manifest = self._load_manifest_unlocked()
            artifacts = manifest.setdefault("artifacts", {})

            entry = artifacts.get(logical_key)
            if entry is None:
                next_version = 1
                versions_list = []
            else:
                next_version = int(entry.get("latest_version", 0)) + 1
                versions_list = entry.get("versions", [])
                # Idempotency check: if latest version has identical hash, return it directly
                if versions_list:
                    latest_rec = versions_list[-1]
                    if latest_rec.get("sha256_full") == sha256_full:
                        return ArtifactVersionRecord(
                            version=latest_rec["version"],
                            physical_filename=latest_rec["physical_filename"],
                            relative_path=latest_rec["relative_path"],
                            sha256_full=latest_rec["sha256_full"],
                            size_bytes=latest_rec["size_bytes"],
                            generated_at_utc=latest_rec["generated_at_utc"],
                            generator_engine=latest_rec["generator_engine"],
                            presentation_metadata=latest_rec.get("presentation_metadata", {}),
                        )

            # Build physical filename and copy binary into artifacts directory
            filename = ArtifactPathResolver.build_physical_filename(ctx, next_version, sha256_full)
            dest_path = self.artifacts_dir / filename
            shutil.copy2(source_path, dest_path)

            record_dict: dict[str, Any] = {
                "version": next_version,
                "physical_filename": filename,
                "relative_path": f"artifacts/{filename}",
                "sha256_full": sha256_full,
                "size_bytes": size_bytes,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "generator_engine": generator_engine,
                "presentation_metadata": presentation_metadata or {},
            }
            versions_list.append(record_dict)

            artifacts[logical_key] = {
                "logical_key": logical_key,
                "domain_unit_id": ArtifactPathResolver.sanitize_token(ctx.domain_unit_id),
                "doc_type": ctx.doc_type.value,
                "locale": ArtifactPathResolver.sanitize_token(ctx.locale),
                "extension": ctx.extension.value,
                "latest_version": next_version,
                "versions": versions_list,
            }

            self._save_manifest_atomic_unlocked(manifest)

            return ArtifactVersionRecord(
                version=next_version,
                physical_filename=filename,
                relative_path=f"artifacts/{filename}",
                sha256_full=sha256_full,
                size_bytes=size_bytes,
                generated_at_utc=record_dict["generated_at_utc"],
                generator_engine=generator_engine,
                presentation_metadata=presentation_metadata or {},
            )

    def get_latest_artifact(
        self,
        domain_unit_id: str,
        doc_type: DocumentType,
        locale: str = "en",
        extension: ArtifactFormat = ArtifactFormat.DOCX,
        verify_integrity: bool = True,
    ) -> Path:
        """Retrieve absolute Path to latest version of artifact, checking SHA-256 integrity."""
        ctx = ArtifactContext(
            tenant_id=self.tenant_id,
            assessment_id=self.assessment_id,
            period="current",
            domain_unit_id=domain_unit_id,
            doc_type=doc_type,
            locale=locale,
            extension=extension,
        )
        logical_key = ArtifactPathResolver.build_logical_key(ctx)

        with self._acquire_lock():
            manifest = self._load_manifest_unlocked()
            entry = manifest.get("artifacts", {}).get(logical_key)
            if not entry or not entry.get("versions"):
                raise ArtifactNotFoundError(
                    f"No artifact registered for logical key '{logical_key}' in assessment '{self.assessment_id}'."
                )

            latest_rec = entry["versions"][-1]
            rel_path = latest_rec["relative_path"]
            abs_path = self.assessment_root / rel_path

            if not abs_path.exists():
                raise ArtifactNotFoundError(f"Physical file missing at registered path {abs_path}.")

            if verify_integrity:
                current_sha = self.compute_sha256(abs_path)
                expected_sha = latest_rec.get("sha256_full")
                if current_sha != expected_sha:
                    raise ArtifactIntegrityError(
                        f"Cryptographic tampering detected on {abs_path}: "
                        f"expected SHA-256 {expected_sha}, found {current_sha}."
                    )

            return abs_path

    def list_artifacts(self) -> list[ArtifactVersionRecord]:
        """List latest version records for all registered deliverables in this assessment."""
        with self._acquire_lock():
            manifest = self._load_manifest_unlocked()
            results = []
            for entry in manifest.get("artifacts", {}).values():
                versions = entry.get("versions", [])
                if versions:
                    latest = versions[-1]
                    results.append(
                        ArtifactVersionRecord(
                            version=latest["version"],
                            physical_filename=latest["physical_filename"],
                            relative_path=latest["relative_path"],
                            sha256_full=latest["sha256_full"],
                            size_bytes=latest["size_bytes"],
                            generated_at_utc=latest["generated_at_utc"],
                            generator_engine=latest["generator_engine"],
                            presentation_metadata=latest.get("presentation_metadata", {}),
                        )
                    )
            return results
