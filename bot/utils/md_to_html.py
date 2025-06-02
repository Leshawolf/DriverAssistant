# bot/utils/md_to_html.py
import re

_heading = re.compile(r"^#{1,6}\s*(.+)$", re.MULTILINE)
_bold = re.compile(r"\*\*(.+?)\*\*")
_italic = re.compile(r"_(.+?)_")
_code = re.compile(r"`(.+?)`")
_u_list = re.compile(r"^\s*-\s+", re.MULTILINE)


def md_to_html(text: str) -> str:
    """Превращает простейший Markdown («###», **bold**, _italic_, `code`) в HTML."""
    text = _heading.sub(r"<b>\1</b>", text)  # ### Заголовок
    text = _bold.sub(r"<b>\1</b>", text)  # **жирный**
    text = _italic.sub(r"<i>\1</i>", text)  # _курсив_
    text = _code.sub(r"<code>\1</code>", text)  # `код`
    text = _u_list.sub("• ", text)  # - список
    # Экранируем опасные < > &
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def strip_double_asterisks(text: str) -> str:
    """
    Удаляет ** … **, сохраняя содержимое.
    """
    return re.sub(r"\*\*(.*?)\*\*", r"\1", text, flags=re.DOTALL)
