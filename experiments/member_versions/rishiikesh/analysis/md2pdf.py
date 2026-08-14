#!/usr/bin/env python3
"""Markdown -> styled HTML -> PDF (via headless Chrome).

Handles GitHub-flavoured tables, fenced code, and the small amount of inline
LaTeX math used in this project's docs.

    python3 md2pdf.py INPUT.md [OUTPUT.pdf]
"""

import html as _html
import os
import re
import subprocess
import sys
import tempfile

import mistune

CHROME = next((p for p in ("/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
                           "/usr/bin/brave-browser", "/usr/bin/chromium")
               if os.path.exists(p)), None)

# ----------------------------------------------------------------- math
GREEK = {r"\lambda": "λ", r"\gamma": "γ", r"\alpha": "α", r"\beta": "β",
         r"\sigma": "σ", r"\mu": "μ", r"\times": "×", r"\approx": "≈",
         r"\le": "≤", r"\ge": "≥", r"\pm": "±", r"\rightarrow": "→",
         r"\angle": "∠", r"\cdot": "·", r"\Rightarrow": "⇒"}


def latex_to_html(m: str) -> str:
    """Render the limited LaTeX subset that appears in these documents."""
    s = m
    s = re.sub(r"\\sqrt\{([^{}]*)\}", r"√(\1)", s)
    s = re.sub(r"\\text\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\mathrm\{([^{}]*)\}", r"\1", s)
    s = s.replace(r"\lvert", "|").replace(r"\rvert", "|")
    s = s.replace(r"\exp", "exp").replace(r"\,", " ").replace(r"\;", " ")
    for k, v in GREEK.items():
        s = s.replace(k, v)
    s = _html.escape(s)
    # superscripts / subscripts, braced or single-token
    s = re.sub(r"\^\{([^{}]*)\}", r"<sup>\1</sup>", s)
    s = re.sub(r"\^(\w)", r"<sup>\1</sup>", s)
    s = re.sub(r"_\{([^{}]*)\}", r"<sub>\1</sub>", s)
    s = re.sub(r"_(\w)", r"<sub>\1</sub>", s)
    s = s.replace("{", "").replace("}", "")
    return s


def protect_math(md: str):
    """Replace math spans with placeholders so mistune leaves them alone."""
    store = []

    def grab(match, block):
        store.append((match, block))
        return f"@@MATH{len(store)-1}@@"

    md = re.sub(r"\$\$(.+?)\$\$", lambda m: grab(m.group(1), True), md, flags=re.S)
    md = re.sub(r"(?<!\\)\$([^$\n]+?)(?<!\\)\$", lambda m: grab(m.group(1), False), md)
    return md, store


def restore_math(html_str: str, store) -> str:
    for i, (expr, block) in enumerate(store):
        rendered = latex_to_html(expr)
        cls = "math-block" if block else "math"
        html_str = html_str.replace(f"@@MATH{i}@@",
                                    f'<span class="{cls}">{rendered}</span>')
    return html_str


CSS = """
@page { size: A4; margin: 14mm 13mm 15mm 13mm; }
* { box-sizing: border-box; }
body {
  font-family: "Source Sans 3","Noto Sans","DejaVu Sans",system-ui,sans-serif;
  font-size: 9.4pt; line-height: 1.45; color: #14181d; margin: 0;
  -webkit-font-smoothing: antialiased;
}
h1 { font-size: 20pt; margin: 0 0 2mm; color: #0f1419; letter-spacing: -.02em;
     border-bottom: 2.5px solid #c0392b; padding-bottom: 2.5mm; }
h2 { font-size: 13pt; margin: 8mm 0 2.5mm; color: #0f1419;
     border-bottom: 1px solid #cfd6dd; padding-bottom: 1.4mm;
     break-after: avoid; page-break-after: avoid; }
h3 { font-size: 10.8pt; margin: 5mm 0 1.8mm; color: #922b21;
     break-after: avoid; page-break-after: avoid; }
h1+p, h2+p, h3+p { margin-top: 0; }
p { margin: 0 0 2.4mm; orphans: 2; widows: 2; }
ul, ol { margin: 0 0 2.6mm; padding-left: 5.5mm; }
li { margin-bottom: 1mm; }
strong { color: #7d1a12; font-weight: 650; }
code { font-family: "JetBrains Mono","DejaVu Sans Mono",monospace; font-size: 8.3pt;
       background: #f1f3f5; padding: .4mm 1.1mm; border-radius: 2px;
       border: 1px solid #e3e7ea; color: #23303b; }
pre { background: #f7f9fa; border: 1px solid #dde3e8; border-left: 3px solid #7f8c8d;
      border-radius: 3px; padding: 2.6mm 3mm; overflow-x: auto; margin: 0 0 3mm;
      break-inside: avoid; page-break-inside: avoid; }
pre code { background: none; border: none; padding: 0; font-size: 7.9pt; line-height: 1.4; }
table { border-collapse: collapse; width: 100%; margin: 0 0 3.4mm; font-size: 8.3pt;
        break-inside: auto; }
thead { display: table-header-group; }
tr { break-inside: avoid; page-break-inside: avoid; }
th { background: #eef1f4; border: 1px solid #c8d0d8; padding: 1.5mm 2mm;
     text-align: left; font-weight: 650; color: #0f1419; }
td { border: 1px solid #d8dee4; padding: 1.4mm 2mm; vertical-align: top; }
tbody tr:nth-child(even) td { background: #fafbfc; }
blockquote { margin: 0 0 3mm; padding: 2.2mm 3mm; background: #fff8e6;
             border-left: 3px solid #d68910; border-radius: 0 3px 3px 0;
             break-inside: avoid; page-break-inside: avoid; }
blockquote p:last-child { margin-bottom: 0; }
hr { border: none; border-top: 1px solid #d8dee4; margin: 6mm 0; }
a { color: #1a5490; text-decoration: none; border-bottom: .5px solid #aac4dd; }
.math { font-family: "DejaVu Serif",Georgia,serif; font-style: italic; white-space: nowrap; }
.math sub, .math sup { font-style: normal; }
.math-block { display: block; text-align: center; margin: 2.5mm 0;
              font-family: "DejaVu Serif",Georgia,serif; font-style: italic; font-size: 11pt; }
"""


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = os.path.abspath(sys.argv[1])
    dst = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 \
        else os.path.splitext(src)[0] + ".pdf"
    if CHROME is None:
        sys.exit("No Chrome/Chromium binary found.")

    md_text = open(src, encoding="utf-8").read()
    md_text, math_store = protect_math(md_text)

    renderer = mistune.create_markdown(
        escape=False,
        plugins=["table", "strikethrough", "url", "task_lists"],
    )
    body = renderer(md_text)
    body = restore_math(body, math_store)

    title = os.path.splitext(os.path.basename(src))[0]
    page = (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{_html.escape(title)}</title><style>{CSS}</style></head>"
            f"<body>{body}</body></html>")

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(page)
        tmp_html = fh.name

    profile = tempfile.mkdtemp(prefix="chrome-md2pdf-")
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
           f"--user-data-dir={profile}", "--no-pdf-header-footer",
           "--virtual-time-budget=20000",
           f"--print-to-pdf={dst}", f"file://{tmp_html}"]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    os.unlink(tmp_html)

    if not os.path.exists(dst):
        print(res.stdout[-2000:]); print(res.stderr[-2000:])
        sys.exit("PDF was not produced.")
    print(f"{src}\n  -> {dst}  ({os.path.getsize(dst)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
