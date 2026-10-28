"""
Litestream Continuous SQLite Replication Configurator — GEMA 18 (SOTA 2026).
Generates declarative litestream.yml configuration files for streaming WAL frames
to S3, MinIO, or Google Cloud Storage buckets.
Enables sub-second Recovery Point Objective (RPO) for distributed SQLite databases.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("assessment_engine.infrastructure.primitives.litestream_replication")


@dataclass
class LitestreamReplicaConfig:
    db_path: str = "app.db"
    bucket_url: str = "s3://backups-bucket/db"
    sync_interval: str = "1s"


class LitestreamReplicationPrimitive:
    """
    Generate Litestream continuous replication configuration.
    """

    def generate_config_yaml(self, config: LitestreamReplicaConfig | None = None) -> str:
        """Generate litestream.yml content."""
        cfg = config or LitestreamReplicaConfig()
        return f"""# Litestream Configuration (Continuous SQLite Streaming)
dbs:
  - path: {cfg.db_path}
    replicas:
      - url: {cfg.bucket_url}
        sync-interval: {cfg.sync_interval}
        retention: 72h
"""

    def write_config(self, target_dir: Path, config: LitestreamReplicaConfig | None = None) -> Path:
        """Write litestream.yml to the destination directory."""
        out = target_dir / "litestream.yml"
        out.write_text(self.generate_config_yaml(config), encoding="utf-8")
        logger.info(f"[Litestream] Configuración de replicación escrita en {out}")
        return out


litestream_replication = LitestreamReplicationPrimitive()
