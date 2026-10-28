"""
Adaptive Multi-Scale WebP Image Pipeline Primitive — GEMA 32 (SOTA 2026).
Compiles uploaded images into multi-resolution WebP bundles (thumbnail 128px, medium 640px, full 1200px).
Strips EXIF metadata to protect user privacy.
Generates responsive HTML srcset attributes for zero-bandwidth waste on mobile screens.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.webp_image_pipeline")

try:
    from PIL import Image  # type: ignore
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


@dataclass
class ProcessedImageVariant:
    variant_name: str  # "thumb", "medium", "full"
    width: int
    height: int
    file_path: str
    file_size_bytes: int


@dataclass
class ImagePipelineResult:
    original_format: str
    variants: list[ProcessedImageVariant] = field(default_factory=list)
    srcset: str = ""


class WebPImagePipelinePrimitive:
    """
    Optimize and compress images across multiple scales into WebP format.
    """

    TARGET_WIDTHS = [
        ("thumb", 128),
        ("medium", 640),
        ("full", 1200)
    ]

    def process_image(
        self,
        source_path: Path,
        output_dir: Path,
        quality: int = 82
    ) -> ImagePipelineResult:
        """Generate optimized WebP variants while preserving the aspect ratio."""
        if not source_path.exists():
            return ImagePipelineResult(original_format="unknown")

        output_dir.mkdir(parents=True, exist_ok=True)

        if not HAS_PILLOW:
            logger.warning("[WebPImagePipeline] Pillow no disponible, devolviendo ruta original sin transformar.")
            return ImagePipelineResult(
                original_format="raw",
                variants=[ProcessedImageVariant("raw", 0, 0, str(source_path), source_path.stat().st_size)]
            )

        variants: list[ProcessedImageVariant] = []
        srcset_parts: list[str] = []

        try:
            with Image.open(source_path) as img:
                orig_format = img.format or "JPEG"
                # Convert to RGB if the image has an alpha channel or indexed palette for WebP compatibility.
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    converted = img.convert("RGBA")
                else:
                    converted = img.convert("RGB")

                orig_w, orig_h = converted.size

                for var_name, max_w in self.TARGET_WIDTHS:
                    # Do not upscale if the original image is smaller.
                    target_w = min(orig_w, max_w)
                    ratio = target_w / float(orig_w)
                    target_h = int(float(orig_h) * ratio)

                    resized = converted.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    var_filename = f"{source_path.stem}_{var_name}.webp"
                    dest_file = output_dir / var_filename

                    resized.save(dest_file, "WEBP", quality=quality, method=6)
                    size_b = dest_file.stat().st_size

                    variants.append(ProcessedImageVariant(
                        variant_name=var_name,
                        width=target_w,
                        height=target_h,
                        file_path=str(dest_file),
                        file_size_bytes=size_b
                    ))
                    srcset_parts.append(f"{var_filename} {target_w}w")

            srcset_str = ", ".join(srcset_parts)
            logger.info(f"[WebPImagePipeline] Imagen '{source_path.name}' procesada en {len(variants)} variantes WebP.")
            return ImagePipelineResult(
                original_format=orig_format,
                variants=variants,
                srcset=srcset_str
            )
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.error(f"[WebPImagePipeline] Error procesando imagen: {ex}")
            return ImagePipelineResult(original_format="error")


webp_image_pipeline = WebPImagePipelinePrimitive()
