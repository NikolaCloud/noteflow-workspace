"""
Парсер Markdown, извлечение Wiki-ссылок [[Link]] и расчет метрик чтения.
"""

import re
from typing import List, Tuple


class MarkdownParser:
    @staticmethod
    def extract_wikilinks(text: str) -> List[str]:
        """Извлекает перекрестные ссылки формата [[Заголовок Заметки]]."""
        return re.findall(r"\[\[(.*?)\]\]", text)

    @staticmethod
    def calculate_stats(text: str) -> Tuple[int, int, int]:
        """Возвращает (слов, символов, минут чтения)."""
        if not text:
            return 0, 0, 1
        words = len(text.split())
        chars = len(text)
        reading_time = max(1, words // 180)
        return words, chars, reading_time

    @staticmethod
    def to_html(markdown_text: str) -> str:
        """Простой легковесный конвертер Markdown в HTML."""
        lines = markdown_text.split("\n")
        html_lines = []
        in_code_block = False

        for line in lines:
            line_s = line.strip()
            if line_s.startswith("```"):
                in_code_block = not in_code_block
                tag = "<pre><code>" if in_code_block else "</code></pre>"
                html_lines.append(tag)
                continue

            if in_code_block:
                html_lines.append(line)
                continue

            # Заголовки
            if line_s.startswith("### "):
                html_lines.append(f"<h3>{line_s[4:]}</h3>")
            elif line_s.startswith("## "):
                html_lines.append(f"<h2>{line_s[3:]}</h2>")
            elif line_s.startswith("# "):
                html_lines.append(f"<h1>{line_s[2:]}</h1>")
            elif line_s.startswith("- [x] "):
                html_lines.append(f"<div class='task done'>☑ {line_s[6:]}</div>")
            elif line_s.startswith("- [ ] "):
                html_lines.append(f"<div class='task'>☐ {line_s[6:]}</div>")
            elif line_s.startswith("- "):
                html_lines.append(f"<li>{line_s[2:]}</li>")
            elif line_s:
                # Wikilinks [[doc]]
                proc_line = re.sub(r"\[\[(.*?)\]\]", r"<span class='wiki-link'>\1</span>", line_s)
                html_lines.append(f"<p>{proc_line}</p>")

        return "\n".join(html_lines)

