import tempfile
import unittest
from pathlib import Path

from text_editor.cli import main
from text_editor.model import (ConflictError, Document, DocumentCatalog, Editor,
                               Heading, ListItem, NotFoundError, Paragraph,
                               Quote, ValidationError)
from text_editor.storage import (JsonStorage, XmlStorage, FormatError,
                                 catalog_to_dict)


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.doc = Document("Черновик", id="doc1")
        self.catalog = DocumentCatalog([self.doc])
        self.editor = Editor(self.catalog)

    def test_document_and_block_crud(self):
        block = Heading("Заголовок", id="b1", level=2)
        self.editor.add_block("doc1", block)
        self.assertEqual(self.editor.get_block("doc1", "b1").render(), "## Заголовок")
        self.editor.update_block("doc1", "b1", "Новый")
        self.assertEqual(self.doc.render(), "## Новый")
        self.editor.delete_block("doc1", "b1")
        self.assertEqual(self.doc.blocks, [])
        self.catalog.rename("doc1", "Готово")
        self.assertEqual(self.catalog.get("doc1").title, "Готово")
        self.catalog.delete("doc1")
        with self.assertRaises(NotFoundError):
            self.catalog.get("doc1")

    def test_polymorphism_and_search(self):
        for block in [Paragraph("Привет"), Quote("ПРИВЕТ"), ListItem("мир")]:
            self.editor.add_block("doc1", block)
        self.assertEqual(len(self.editor.search("привет")), 2)
        self.assertIn("> ПРИВЕТ", self.doc.render())
        self.assertIn("- мир", self.doc.render())

    def test_validation_and_conflict(self):
        with self.assertRaises(ValidationError):
            Heading("x", level=7)
        with self.assertRaises(ValidationError):
            Document(" ")
        self.editor.add_block("doc1", Paragraph("one", id="same"))
        with self.assertRaises(ConflictError):
            self.editor.add_block("doc1", Paragraph("two", id="same"))
        with self.assertRaises(ConflictError):
            self.catalog.add(Document("copy", id="doc1"))

    def test_json_xml_roundtrip(self):
        self.editor.add_block("doc1", Heading("Тест & XML", id="h", level=3))
        self.editor.add_block("doc1", Paragraph("Строка <текст>", id="p"))
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            for storage, ext in [(JsonStorage(), "json"), (XmlStorage(), "xml")]:
                path = Path(tmp) / f"sample.{ext}"
                storage.save(path, self.catalog)
                loaded = storage.load(path)
                self.assertEqual(catalog_to_dict(loaded), catalog_to_dict(self.catalog))

    def test_bad_files(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{oops", encoding="utf-8")
            with self.assertRaises(FormatError):
                JsonStorage().load(path)
            path = Path(tmp) / "bad.xml"
            path.write_text("<wrong/>", encoding="utf-8")
            with self.assertRaises(FormatError):
                XmlStorage().load(path)

    def test_cli_persistence(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            db = Path(tmp) / "db.json"
            self.assertEqual(main(["--db", str(db), "new", "Мой текст"]), 0)
            doc_id = JsonStorage().load(db).list()[0].id
            self.assertEqual(main(["--db", str(db), "add", doc_id,
                                   "paragraph", "Привет"]), 0)
            self.assertEqual(JsonStorage().load(db).list()[0].blocks[0].text, "Привет")
            self.assertEqual(main(["--db", str(db), "show", "missing"]), 1)


if __name__ == "__main__":
    unittest.main()
