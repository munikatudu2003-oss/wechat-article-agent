from __future__ import annotations

from html import escape


class MarkdownService:
    def markdown_to_html(self, markdown: str) -> str:
        parts: list[str] = []
        in_list = False

        for raw_line in markdown.splitlines():
            line = raw_line.strip()
            if not line:
                if in_list:
                    parts.append("</ul>")
                    in_list = False
                continue

            if line.startswith("# "):
                if in_list:
                    parts.append("</ul>")
                    in_list = False
                parts.append(f"<h1>{escape(line[2:])}</h1>")
                continue

            if line.startswith("## "):
                if in_list:
                    parts.append("</ul>")
                    in_list = False
                parts.append(f"<h2>{escape(line[3:])}</h2>")
                continue

            if line.startswith("- "):
                if not in_list:
                    parts.append("<ul>")
                    in_list = True
                parts.append(f"<li>{escape(line[2:])}</li>")
                continue

            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<p>{escape(line)}</p>")

        if in_list:
            parts.append("</ul>")

        return "\n    ".join(parts)
