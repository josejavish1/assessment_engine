from __future__ import annotations

from assessment_engine.domain.schemas.blueprint import BlueprintPayload


def test_pydantic_import() -> None:
    assert BlueprintPayload is not None


def test_openpyxl_import() -> None:
    import openpyxl

    wb = openpyxl.Workbook()
    assert wb is not None

