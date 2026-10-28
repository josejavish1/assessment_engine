"""
Canonical Media, Blob & Asset Pipeline Engine — System 11 (MinIO / WebP SOTA 2026).
Consolidated asset management and image processing suite:
1. Local blob storage with streaming uploads and magic byte verification.
2. Adaptive multi-scale WebP image pipeline (thumb, medium, full) with srcset.
3. OpenGraph SVG social card generation for viral social sharing.
4. Privacy EXIF metadata stripping.
"""

from __future__ import annotations

from assessment_engine.infrastructure.primitives.blob import BlobStoragePrimitive, blob_primitive
from assessment_engine.infrastructure.primitives.webp_image_pipeline import (
    WebPImagePipelinePrimitive,
    ImagePipelineResult,
    ProcessedImageVariant,
    webp_image_pipeline
)
from assessment_engine.infrastructure.primitives.social_card_generator import SocialCardGeneratorPrimitive, social_card_generator
from assessment_engine.infrastructure.primitives.upload_streaming_guard import UploadStreamingGuardPrimitive, upload_streaming_guard

media_engine = blob_primitive
image_pipeline = webp_image_pipeline
