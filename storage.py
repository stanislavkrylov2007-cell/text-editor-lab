"""Чтение и запись каталога в JSON и XML."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from xml.etree import ElementTree as ET

from exceptions import FormatError, ValidationError
from models import BLOCK_TYPES, Document, TextBlock
from service import DocumentCatalog


def block_to_dict(block: TextBlock) -> dict:
    result = {"id": block.id, "kind": block.kind, "text": block.text}
    if block.kind == "heading":
        result["level"] = block.level
    return result


def catalog_to_dict(catalog: DocumentCatalog) -> dict:
    return {"documents": [{"id": doc.id, "title": doc.title,
                            "blocks": [block_to_dict(block) for block in doc.blocks]}
                           for doc in catalog.list()]}


def catalog_from_dict(data: dict) -> DocumentCatalog:
    try:
        if not isinstance(data, dict) or not isinstance(data["documents"], list):
            raise FormatError("Ожидался объект с массивом documents")
        documents = []
        for item in data["documents"]:
            if not isinstance(item["blocks"], list):
                raise FormatError("blocks должен быть массивом")
            blocks = []
            for raw in item["blocks"]:
                cls = BLOCK_TYPES[raw["kind"]]
                args = {"id": raw["id"], "text": raw["text"]}
                if cls is BLOCK_TYPES["heading"]:
                    args["level"] = raw["level"]
                blocks.append(cls(**args))
            ids = [block.id for block in blocks]
            if len(ids) != len(set(ids)):
                raise FormatError("Повторяющийся ID блока")
            documents.append(Document(item["title"], item["id"], blocks))
        return DocumentCatalog(documents)
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        raise FormatError(f"Некорректная структура данных: {exc}") from exc


class Storage(ABC):
    @abstractmethod
    def load(self, path: Path) -> DocumentCatalog:
        pass

    @abstractmethod
    def save(self, path: Path, catalog: DocumentCatalog) -> None:
        pass


class JsonStorage(Storage):
    def load(self, path: Path) -> DocumentCatalog:
        try:
            return catalog_from_dict(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError as exc:
            raise FormatError(f"Некорректный JSON: {exc}") from exc

    def save(self, path: Path, catalog: DocumentCatalog) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(catalog_to_dict(catalog), ensure_ascii=False,
                                   indent=2) + "\n", encoding="utf-8")


class XmlStorage(Storage):
    def load(self, path: Path) -> DocumentCatalog:
        try:
            root = ET.parse(path).getroot()
            if root.tag != "documents":
                raise FormatError("Корневой элемент должен быть documents")
            data = {"documents": []}
            for doc in root:
                if doc.tag != "document":
                    raise FormatError("Ожидался элемент document")
                item = {"id": doc.attrib["id"], "title": doc.attrib["title"],
                        "blocks": []}
                for block in doc:
                    if block.tag != "block":
                        raise FormatError("Ожидался элемент block")
                    raw = {"id": block.attrib["id"], "kind": block.attrib["kind"],
                           "text": block.text or ""}
                    if raw["kind"] == "heading":
                        raw["level"] = int(block.attrib["level"])
                    item["blocks"].append(raw)
                data["documents"].append(item)
            return catalog_from_dict(data)
        except (ET.ParseError, KeyError, ValueError) as exc:
            raise FormatError(f"Некорректный XML: {exc}") from exc

    def save(self, path: Path, catalog: DocumentCatalog) -> None:
        root = ET.Element("documents")
        for doc in catalog.list():
            element = ET.SubElement(root, "document", id=doc.id, title=doc.title)
            for block in doc.blocks:
                attrs = {"id": block.id, "kind": block.kind}
                if block.kind == "heading":
                    attrs["level"] = str(block.level)
                ET.SubElement(element, "block", **attrs).text = block.text
        ET.indent(root, space="  ")
        path.parent.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def storage_for(path: Path) -> Storage:
    if path.suffix.lower() == ".json":
        return JsonStorage()
    if path.suffix.lower() == ".xml":
        return XmlStorage()
    raise FormatError("Поддерживаются только .json и .xml")
