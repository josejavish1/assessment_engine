import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class EvidenceFragment(BaseModel):
    """Represents a discrete unit of information extracted from a source document.

    This data model encapsulates a piece of evidence, linking verbatim content
    to its original source URI. It includes metadata for location, integrity
    verification via a content hash, and a creation timestamp. It serves as a
    fundamental component for systems requiring information traceability.

    Attributes:
        fragment_id: A unique UUIDv4 identifier for the evidence fragment.
        source_uri: The Uniform Resource Identifier (URI) of the source document.
        content: The verbatim text or data content of the evidence fragment.
        content_hash: A cryptographic hash (e.g., SHA-256) of the `content`
            field, used to verify data integrity.
        location_metadata: A dictionary of metadata specifying the fragment's
            location within the source document. Keys are implementation-defined
            and may include 'page_number', 'line_number', or 'bounding_box'.
        timestamp: An ISO 8601 formatted UTC timestamp indicating when the
            fragment instance was created.
    """

    fragment_id: str = ""
    source_uri: str
    content: str
    content_hash: str = ""
    location_metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @model_validator(mode="before")
    @classmethod
    def generate_content_addressable_id_and_hash(cls, data: Any) -> Any:
        if isinstance(data, dict):
            content = data.get("content", "")
            # Auto-compute content_hash as SHA-256 of the content text
            if not data.get("content_hash") and content:
                import hashlib
                data["content_hash"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
            
            # Auto-compute fragment_id as SHA-256 of source_uri | content
            if not data.get("fragment_id") and content:
                import hashlib
                source_uri = data.get("source_uri", "")
                combined = f"{source_uri}|{content}"
                data["fragment_id"] = hashlib.sha256(combined.encode("utf-8")).hexdigest()
        return data


class EvidenceLedger(BaseModel):
    """Aggregates evidence fragments for a single client."""

    client_id: str
    fragments: List[EvidenceFragment] = Field(default_factory=list)


class RaptorNode(BaseModel):
    """Represents a node in a RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval) model's tree.

    A node can be either a terminal leaf, containing a raw text fragment, or an
    internal node, representing a recursive summary of its child nodes.

    Attributes:
        node_id (str): A unique identifier for the node, generated as a UUID by
            default.
        level (int): The hierarchical depth of the node within the tree. Level 0
            represents a leaf node containing a raw text fragment, while levels > 0
            denote recursively generated summary nodes.
        content (str): The text content of the node. For leaf nodes (level 0), this
            is a raw text fragment. For internal nodes (level > 0), this is a
            generated summary of its children.
        children_ids (List[str]): A list of unique identifiers for the direct
            children of this node. An empty list signifies a leaf node.
        metadata (Dict[str, Any]): A dictionary for storing arbitrary metadata
            associated with the node.
    """

    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    level: int  # The hierarchical depth of the node within the tree. By convention, level 0 represents a leaf node containing a raw text fragment, while levels > 0 denote recursively generated summary nodes.
    content: str
    children_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RaptorTree(BaseModel):
    """A data model for a RAPTOR tree, a hierarchical knowledge graph structure.

    This structure contains leaf nodes representing evidence fragments and recursively
    generated parent nodes representing summaries. The hierarchical organization
    facilitates multi-level information retrieval and querying across various
    levels of abstraction.

    Attributes:
        client_id (str): An identifier for the client that owns this tree.
        nodes (Dict[str, RaptorNode]): A mapping from unique node identifiers
            to their corresponding `RaptorNode` objects, providing an indexed
            lookup for all nodes within the tree.
        root_id (Optional[str]): The unique identifier of the tree's root node.
            This is `None` if the tree has not been constructed or is empty.
    """

    client_id: str
    nodes: Dict[str, RaptorNode] = Field(
        default_factory=dict
    )  # Provides an indexed lookup of all nodes within the tree, mapping each unique node identifier to its corresponding RaptorNode object.
    root_id: Optional[str] = None


class EvidenceAnchor(BaseModel):
    """Represents an evidential link from a claim to a specific supporting node within a hierarchical tree structure.

    This class models a directed edge, anchoring a high-level assertion to a
    concrete piece of information (e.g., a text chunk or a summary) in the tree.

    Attributes:
        node_id: The unique identifier of the target node in the tree.
        confidence: A numerical score from 0.0 to 1.0 indicating confidence in
            the evidential link. Defaults to 1.0.
        quote_literal: An optional, direct quote from the source text that serves
            as evidence.
        reasoning: An optional explanation of why the referenced node supports the
            claim.
    """

    node_id: str
    confidence: float = 1.0
    quote_literal: Optional[str] = None
    reasoning: Optional[str] = None
