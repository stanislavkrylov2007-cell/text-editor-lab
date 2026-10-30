# Лабораторная работа №1 — вариант 16 «Текстовый редактор»

Python 3.10+. Предметная область — документы с текстовыми блоками: абзацы, заголовки, цитаты и элементы списка. Реализованы ООП (наследование, инкапсуляция, полиморфизм), CRUD документов и блоков, поиск, аннотации типов, обработка стандартных и собственных исключений, чтение и запись JSON/XML. В проекте 13 прикладных классов и 5 классов исключений. Отчёт по просьбе пользователя не включён.

## Запуск

Из корня проекта в PowerShell:

```powershell
$env:PYTHONPATH='src'
python -m text_editor --help
python -m text_editor import examples/sample.json
python -m text_editor list
python -m text_editor show example1
python -m text_editor add example1 heading 'Новый раздел' --level 2
python -m text_editor search редактор
python -m text_editor export data/backup.xml
python -m text_editor import data/backup.xml
```

Можно установить пакет: `python -m pip install -e .`, затем запускать `text-editor`. Без установки достаточно `PYTHONPATH=src`. Рабочая база по умолчанию `data/editor.json`; путь можно изменить глобальным параметром `--db путь.json` перед командой.

## Команды

| Команда | Назначение |
|---|---|
| `new "Название"` | Создать документ, вывести ID |
| `list` | Список документов |
| `show ID` | Показать документ и ID блоков |
| `rename ID "Название"` | Изменить название |
| `delete ID` | Удалить документ |
| `add ID paragraph|heading|quote|list_item "Текст" [--level N]` | Добавить блок |
| `edit ID BLOCK_ID "Текст"` | Изменить блок |
| `remove ID BLOCK_ID` | Удалить блок |
| `search "Фраза"` | Поиск без учёта регистра |
| `export файл.json|файл.xml` | Сохранить копию каталога |
| `import файл.json|файл.xml` | Заменить рабочий каталог импортированным |

Все изменения после команд автоматически сохраняются. Ошибки выводятся в stderr с ненулевым кодом выхода. При импорте некорректного файла текущая база сохраняется. Форматы содержат ID, название и упорядоченные блоки; XML экранирует специальные символы. Схема классов — [docs/classes.puml](docs/classes.puml), её можно открыть в PlantUML или редакторе диаграмм с поддержкой PlantUML.

## Тесты

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

Проверяются CRUD, полиморфизм, поиск, валидация, конфликты ID, ошибки форматов, эквивалентность при сохранении/загрузке JSON и XML, а также сохранение через CLI.
