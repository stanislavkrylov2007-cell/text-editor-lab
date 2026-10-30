"""Предметная модель редактора."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


class EditorError(Exception):
    """Базовая ошибка редактора."""


class ValidationError(EditorError):
    """Некорректные данные пользователя."""


class NotFoundError(EditorError):
    """Документ или блок не найден."""


class FormatError(EditorError):
    """Некорректный формат файла."""


class ConflictError(EditorError):
    """Идентификатор уже существует."""


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


class DocumentCatalog:
    def __init__(self, documents: list[Document] | None = None) -> None:
        self._documents: dict[str, Document] = {}
        for document in documents or []:
            self.add(document)

    def add(self, document: Document) -> None:
        if document.id in self._documents:
            raise ConflictError(f"Документ {document.id} уже существует")
        self._documents[document.id] = document

    def get(self, document_id: str) -> Document:
        try:
            return self._documents[document_id]
        except KeyError as exc:
            raise NotFoundError(f"Документ {document_id} не найден") from exc

    def list(self) -> list[Document]:
        return list(self._documents.values())

    def rename(self, document_id: str, title: str) -> Document:
        document = self.get(document_id)
        if not title.strip():
            raise ValidationError("Название документа не может быть пустым")
        document.title = title
        return document

    def delete(self, document_id: str) -> None:
        self.get(document_id)
        del self._documents[document_id]


class Editor:
    def __init__(self, catalog: DocumentCatalog) -> None:
        self.catalog = catalog

    def add_block(self, document_id: str, block: TextBlock) -> None:
        document = self.catalog.get(document_id)
        if any(item.id == block.id for item in document.blocks):
            raise ConflictError(f"Блок {block.id} уже существует")
        document.blocks.append(block)

    def get_block(self, document_id: str, block_id: str) -> TextBlock:
        for block in self.catalog.get(document_id).blocks:
            if block.id == block_id:
                return block
        raise NotFoundError(f"Блок {block_id} не найден")

    def update_block(self, document_id: str, block_id: str, text: str) -> TextBlock:
        if not isinstance(text, str):
            raise ValidationError("Текст должен быть строкой")
        block = self.get_block(document_id, block_id)
        block.text = text
        return block

    def delete_block(self, document_id: str, block_id: str) -> None:
        document = self.catalog.get(document_id)
        block = self.get_block(document_id, block_id)
        document.blocks.remove(block)

    def search(self, query: str) -> list[SearchResult]:
        if not query:
            raise ValidationError("Поисковый запрос не может быть пустым")
        return [SearchResult(doc.id, block.id, block.text)
                for doc in self.catalog.list() for block in doc.blocks
                if query.casefold() in block.text.casefold()]
