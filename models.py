"""Документы и виды текстовых блоков."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from exceptions import ValidationError


@dataclass
class TextBlock:
    text: str
    id: str = field(default_factory=lambda: uuid4().hex[:8])
    kind: str = field(default="paragraph", init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not isinstance(self.id, str) or not self.id:
            raise ValidationError("Текст должен быть строкой, ID — непустой строкой")

    def render(self) -> str:
        return self.text


@dataclass
class Paragraph(TextBlock):
    kind: str = field(default="paragraph", init=False)


@dataclass
class Heading(TextBlock):
    level: int = 1
    kind: str = field(default="heading", init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        if type(self.level) is not int or not 1 <= self.level <= 6:
            raise ValidationError("Уровень заголовка должен быть от 1 до 6")

    def render(self) -> str:
        return f"{'#' * self.level} {self.text}"


@dataclass
class Quote(TextBlock):
    kind: str = field(default="quote", init=False)

    def render(self) -> str:
        return f"> {self.text}"


@dataclass
class ListItem(TextBlock):
    kind: str = field(default="list_item", init=False)

    def render(self) -> str:
        return f"- {self.text}"


BLOCK_TYPES: dict[str, type[TextBlock]] = {
    "paragraph": Paragraph, "heading": Heading,
    "quote": Quote, "list_item": ListItem,
}


@dataclass
class Document:
    title: str
    id: str = field(default_factory=lambda: uuid4().hex[:8])
    blocks: list[TextBlock] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValidationError("Название документа не может быть пустым")
        if not isinstance(self.id, str) or not self.id:
            raise ValidationError("ID документа не может быть пустым")

    def render(self) -> str:
        return "\n\n".join(block.render() for block in self.blocks)


@dataclass(frozen=True)
class SearchResult:
    document_id: str
    block_id: str
    text: str


