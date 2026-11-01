"""Исключения текстового редактора."""

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


