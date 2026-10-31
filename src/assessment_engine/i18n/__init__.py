"""Declarative i18n package."""

from assessment_engine.i18n.resolver import (
    DeclarativeI18nResolver,
    MissingLocalizationKeyError,
)

__all__ = ["DeclarativeI18nResolver", "MissingLocalizationKeyError"]
