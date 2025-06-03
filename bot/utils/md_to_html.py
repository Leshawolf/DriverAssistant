import re

_heading_re = re.compile(r"^#+\s*(.*)$", flags=re.MULTILINE)  # ### Заголовок
_asterisk_re = re.compile(r"\*+")  # любые * или **


def md_headings_to_html(text: str) -> str:
    text = _heading_re.sub(r"<b>\1</b>", text)  # заголовки → <b>
    text = _asterisk_re.sub("", text)  # удаляем все *
    return text
