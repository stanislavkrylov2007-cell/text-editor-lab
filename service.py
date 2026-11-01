"""Операции над документами и блоками."""

from __future__ import annotations

from exceptions import ConflictError, NotFoundError, ValidationError
from models import Document, SearchResult, TextBlock


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
