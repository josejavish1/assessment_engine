from __future__ import annotations

from typing import List

from pydantic import BaseModel


class ProductOwnerAlternatives(BaseModel):
    alternatives: List[str]
    best_index: int
