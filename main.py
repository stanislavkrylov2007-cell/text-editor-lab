"""Консольный интерфейс. Изменения автоматически сохраняются в базе JSON."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from exceptions import EditorError
from models import BLOCK_TYPES, Document, Heading
from service import DocumentCatalog, Editor
from storage import JsonStorage, storage_for


class EditorCLI:
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(description="Текстовый редактор, вариант 16")
        self.parser.add_argument("--db", type=Path, default=Path("data/editor.json"),
                                 help="Путь к рабочей базе JSON")
        commands = self.parser.add_subparsers(dest="command", required=True)
        new = commands.add_parser("new", help="Создать документ")
        new.add_argument("title")
        commands.add_parser("list", help="Список документов")
        show = commands.add_parser("show", help="Показать документ и ID блоков")
        show.add_argument("document_id")
        rename = commands.add_parser("rename", help="Переименовать документ")
        rename.add_argument("document_id")
        rename.add_argument("title")
        delete = commands.add_parser("delete", help="Удалить документ")
        delete.add_argument("document_id")
        add = commands.add_parser("add", help="Добавить текстовый блок")
        add.add_argument("document_id")
        add.add_argument("kind", choices=BLOCK_TYPES)
        add.add_argument("text")
        add.add_argument("--level", type=int, default=1)
        edit = commands.add_parser("edit", help="Изменить текст блока")
        edit.add_argument("document_id")
        edit.add_argument("block_id")
        edit.add_argument("text")
        remove = commands.add_parser("remove", help="Удалить блок")
        remove.add_argument("document_id")
        remove.add_argument("block_id")
        search = commands.add_parser("search", help="Поиск по блокам")
        search.add_argument("query")
        export = commands.add_parser("export", help="Экспорт в JSON/XML")
        export.add_argument("path", type=Path)
        imported = commands.add_parser("import", help="Импорт JSON/XML вместо текущей базы")
        imported.add_argument("path", type=Path)

    def run(self, argv: list[str] | None = None) -> int:
        args = self.parser.parse_args(argv)
        try:
            if args.command == "import":
                catalog = storage_for(args.path).load(args.path)
                JsonStorage().save(args.db, catalog)
                print(f"Импортировано документов: {len(catalog.list())}")
                return 0
            catalog = JsonStorage().load(args.db) if args.db.exists() else DocumentCatalog()
            editor = Editor(catalog)
            changed = False
            if args.command == "new":
                doc = Document(args.title)
                catalog.add(doc)
                print(f"Создан документ {doc.id}: {doc.title}")
                changed = True
            elif args.command == "list":
                for doc in catalog.list():
                    print(f"{doc.id}\t{doc.title}\t{len(doc.blocks)} блоков")
            elif args.command == "show":
                doc = catalog.get(args.document_id)
                print(f"{doc.title} [{doc.id}]")
                for block in doc.blocks:
                    print(f"[{block.id}] {block.render()}")
            elif args.command == "rename":
                catalog.rename(args.document_id, args.title)
                changed = True
            elif args.command == "delete":
                catalog.delete(args.document_id)
                changed = True
            elif args.command == "add":
                cls = BLOCK_TYPES[args.kind]
                block = Heading(args.text, level=args.level) if cls is Heading else cls(args.text)
                editor.add_block(args.document_id, block)
                print(f"Создан блок {block.id}")
                changed = True
            elif args.command == "edit":
                editor.update_block(args.document_id, args.block_id, args.text)
                changed = True
            elif args.command == "remove":
                editor.delete_block(args.document_id, args.block_id)
                changed = True
            elif args.command == "search":
                for result in editor.search(args.query):
                    print(f"{result.document_id}/{result.block_id}\t{result.text}")
            elif args.command == "export":
                storage_for(args.path).save(args.path, catalog)
                print(f"Экспортировано: {args.path}")
            if changed:
                JsonStorage().save(args.db, catalog)
            return 0
        except (EditorError, OSError, UnicodeError) as exc:
            print(f"Ошибка: {exc}", file=sys.stderr)
            return 1


def main(argv: list[str] | None = None) -> int:
    return EditorCLI().run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
