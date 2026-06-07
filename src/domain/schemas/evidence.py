import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EvidenceFragment(BaseModel):
    """
    An atomic piece of information from a source document.
    """

    fragment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_uri: str
    content: str
    content_hash: str
    location_metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class EvidenceLedger(BaseModel):
    """
    A collection of all evidence fragments for a client.
    """

    client_id: str
    fragments: List[EvidenceFragment] = Field(default_factory=list)


class RaptorNode(BaseModel):
    """
    A node in the RAPTOR tree. Can be a leaf (raw fragment) or a summary node.
    """

    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    level: int  # 0 for leaves, 1+ for summaries
    content: str
    children_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RaptorTree(BaseModel):
    """
    The full hierarchical tree of knowledge.
    """

    client_id: str
    nodes: Dict[str, RaptorNode] = Field(default_factory=dict)  # node_id -> RaptorNode
    root_id: Optional[str] = None


class EvidenceAnchor(BaseModel):
    """
    A pointer from a strategic claim to an evidence fragment or summary node.
    """

    node_id: str
    confidence: float = 1.0
    quote_literal: Optional[str] = None
    reasoning: Optional[str] = None
