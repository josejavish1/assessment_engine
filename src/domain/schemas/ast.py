from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class BaseNode(BaseModel):
    """Define the base model for a node in a Document Abstract Syntax Tree (AST)."""
    type: str

class ParagraphNode(BaseNode):
    """Represents a paragraph of text within a document abstract syntax tree (AST).

    This node encapsulates the textual content and associated formatting properties
    for a single paragraph.

    Attributes:
        type: A string literal identifying the node type as 'paragraph'.
        text: The raw textual content of the paragraph.
        bold: A boolean flag indicating if the text is rendered in bold.
        italic: A boolean flag indicating if the text is rendered in italics.
        style: The style identifier for the paragraph, which maps to a predefined
            style in the target document format (e.g., 'Normal', 'List Bullet').
        space_after: The amount of vertical whitespace, in points (pt), rendered
            after the paragraph.
        text_color_rgb: An optional list of three integers representing the text color
            in the RGB color model, where each value is in the range [0, 255].
            If None, the default document text color is used.
    """
    type: Literal["paragraph"] = "paragraph"
    text: str = Field(..., description="Textual content of the paragraph.")
    bold: bool = Field(False, description="Specifies if the paragraph text is rendered in bold.")
    italic: bool = Field(False, description="Specifies if the paragraph text is rendered in italics.")
    style: str = Field("Normal", description="Identifier for the paragraph's style, corresponding to a defined document style (e.g., 'Normal', 'List Bullet').")
    space_after: int = Field(6, description="Vertical spacing after the paragraph in points (pt).")
    text_color_rgb: Optional[List[int]] = Field(None, description="Text color, specified as an RGB tuple of integers, where each value is in the range [0, 255].")
    align: str = Field("JUSTIFY", description="Horizontal alignment of the paragraph's content. Valid values are 'LEFT', 'CENTER', 'RIGHT', 'JUSTIFY'.")
    font_size: float = Field(10.5, description="Font size of the paragraph in points (pt).")

class HeadingNode(BaseNode):
    """Represents a heading element within the document's abstract syntax tree.

    Attributes:
        type: The node type, fixed to 'heading'.
        text: The textual content of the heading.
        level: The hierarchical level of the heading, an integer from 1 (highest)
            to 6 (lowest). Defaults to 1.
        primary_color_rgb: An optional list of three integers representing an RGB
            color `[R, G, B]` to override the default style. Each value must be
            in the range [0, 255].
    """
    type: Literal["heading"] = "heading"
    text: str = Field(..., description="Textual content of the heading.")
    level: int = Field(1, ge=1, le=6, description="Hierarchical heading level, an integer from 1 (highest) to 6 (lowest).")
    primary_color_rgb: Optional[List[int]] = Field(None, description="Optional six-digit hexadecimal RGB color string for overriding the default header style.")

class CellNode(BaseModel):
    """Represents a single cell within a table structure.

    This model encapsulates the content and styling properties of a table cell,
    including its text, font attributes, alignment, and color specifications.

    Attributes:
        text: The textual content of the cell.
        bold: If True, the text is rendered in a bold style. Defaults to False.
        font_size: The font size in points (pt). Defaults to 9.0.
        align: Horizontal alignment of the cell's content. Valid values are
            'LEFT', 'CENTER', 'RIGHT', or 'JUSTIFY'. Defaults to 'LEFT'.
        bg_color: The background color of the cell, specified as a six-digit
            hexadecimal RGB string (e.g., 'FF0000'). Defaults to None.
        text_color_rgb: The text color, specified as a list of three integers
            [R, G, B], where each value is in the range [0, 255]. Defaults
            to None.
    """
    text: str = Field(..., description="Textual content of the table cell.")
    bold: bool = Field(False, description="String literal content to be rendered in a bold style.")
    font_size: float = Field(9.0, description="Font size in points (pt).")
    align: str = Field("LEFT", description="Horizontal alignment of the paragraph's content. Valid values include LEFT, CENTER, RIGHT, or JUSTIFY.")
    bg_color: Optional[str] = Field(None, description="Background color of the cell, specified as a six-digit hexadecimal RGB string (e.g., 'FF0000').")
    text_color_rgb: Optional[List[int]] = Field(None, description="Optional text color override, specified as an RGB tuple of integers, where each value is in the range [0, 255].")

class TableRowNode(BaseModel):
    """Models a row within a table structure.

    This node encapsulates an ordered sequence of `CellNode` objects and
    designates the row as either a header or a data row.

    Attributes:
        cells: The ordered sequence of `CellNode` objects that compose the row.
        is_header: A boolean that specifies whether the row functions as the
            table header. Defaults to `False`.
    """
    cells: List[CellNode] = Field(..., description="Ordered sequence of `Cell` nodes that compose the row.")
    is_header: bool = Field(False, description="Specifies whether the row functions as the table header.")

class TableNode(BaseNode):
    """Models a table structure within an abstract syntax tree (AST).

    This node defines a table consisting of an ordered sequence of rows and an
    optional header. It supports layout and style customization through an OpenXML
    style profile identifier and a flag for automatic column width adjustment.

    Attributes:
        type: The node type identifier, fixed to 'table'.
        headers: An optional list of strings for populating a simple header row.
            This serves as a convenience alternative to manually constructing the
            first `TableRowNode` as a header.
        rows: The ordered list of `TableRowNode` objects that constitute the
            table's body. If a header is required and not specified via the
            `headers` attribute, it should be the first element in this list.
        style_profile: The identifier for the OpenXML table style to be applied
            (e.g., 'TableGrid'). Defaults to 'Table Grid'.
        autofit: A boolean flag that enables automatic adjustment of column
            widths to fit content. Defaults to `True`.
    """
    type: Literal["table"] = "table"
    headers: Optional[List[str]] = Field(None, description="Optional list of strings to populate the header row, facilitating simplified table instantiation.")
    rows: List[TableRowNode] = Field(default_factory=list, description="Ordered sequence of `Row` nodes that compose the table body.")
    style_profile: str = Field("Table Grid", description="Identifier for the OpenXML table style to be applied (e.g., 'TableGrid').")
    autofit: bool = Field(True, description="Enables automatic adjustment of column widths to fit content.")

class SpacerNode(BaseNode):
    """Represents a fixed-size vertical gap within a document's layout structure.

    This node is used to introduce vertical whitespace between other layout elements.
    The size of the space is defined in typographical points.

    Attributes:
        type: A string literal 'spacer' uniquely identifying this node type.
        points: The vertical spacing magnitude in points (pt). Defaults to 12.
    """
    type: Literal["spacer"] = "spacer"
    points: int = Field(12, description="Spacing magnitude in points (pt).")

class PageBreakNode(BaseNode):
    """Represent an explicit page break within a document's abstract syntax tree."""
    type: Literal["page_break"] = "page_break"

class PictureNode(BaseNode):
    """A node representing an image embedded in a document.

    Attributes:
        type: The node type identifier, fixed to 'picture'.
        path: The filesystem path (absolute or relative) to the source image file.
        width_inches: The display width of the image in inches. Defaults to 4.5.
    """
    type: Literal["picture"] = "picture"
    path: str = Field(..., description="Filesystem path (absolute or relative) to the source image file.")
    width_inches: float = Field(4.5, description="Display width of the image in inches.")

# Defines a discriminated union of all concrete AST node types, enabling type-safe parsing, serialization, and pattern matching operations.
DocNode = Union[
    ParagraphNode,
    HeadingNode,
    TableNode,
    SpacerNode,
    PageBreakNode,
    PictureNode
]

class DocumentAST(BaseModel):
    """A unified, declarative Intermediate Representation (IR) for document structure.

    This class serves as the root of a document's abstract syntax tree (AST),
    encapsulating the entire document structure. It includes a title, global
    metadata, and a linear sequence of content nodes. As a Pydantic model, it
    provides a serializable and language-agnostic representation suitable for
    document processing, transformation, and rendering pipelines.

    Attributes:
        title (str): The primary title of the document.
        metadata (Dict[str, Any]): A key-value mapping for global document
            metadata, such as client, date, or versioning information. Defaults to
            an empty dictionary.
        nodes (List[DocNode]): An ordered sequence of `DocNode` objects that
            constitute the primary body of the document. Defaults to an empty
            list.
    """
    title: str = Field(..., description="Primary title of the document.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Global document metadata, such as client, date, and versioning information.")
    nodes: List[DocNode] = Field(default_factory=list, description="Ordered sequence of structural nodes that constitute the primary body of the document.")
