from __future__ import annotations

from typing import List

from pydantic import BaseModel


class ProductOwnerAlternatives(BaseModel):
    """Model a list of string alternatives with the index of a designated best choice."""
    alternatives: List[str]
    best_index: int
