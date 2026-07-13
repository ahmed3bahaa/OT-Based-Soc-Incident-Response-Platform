from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "OT_SOC_Live_Testing_Production_Guide.md"
TARGET = ROOT / "docs" / "OT_SOC_Live_Testing_Production_Guide.pdf"


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def inline_markup(text: str) -> str:
    text = esc(text)
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def on_page(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(18 * mm, 12 * mm, "OT-Based SOC Incident Response Platform")
    canvas.drawRightString(192 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "GuideTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            spaceAfter=18,
            textColor=colors.HexColor("#111111"),
        ),
        "h1": ParagraphStyle(
            "GuideH1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            spaceBefore=14,
            spaceAfter=8,
            textColor=colors.HexColor("#111111"),
        ),
        "h2": ParagraphStyle(
            "GuideH2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
            textColor=colors.HexColor("#222222"),
        ),
        "h3": ParagraphStyle(
            "GuideH3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=4,
            textColor=colors.HexColor("#333333"),
        ),
        "body": ParagraphStyle(
            "GuideBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "GuideBullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            leftIndent=8 * mm,
            firstLineIndent=-4 * mm,
            spaceAfter=3,
        ),
        "code": ParagraphStyle(
            "GuideCode",
            fontName="Courier",
            fontSize=7.5,
            leading=9.5,
            leftIndent=4 * mm,
            rightIndent=4 * mm,
            backColor=colors.HexColor("#f3f3f3"),
            borderColor=colors.HexColor("#dddddd"),
            borderWidth=0.5,
            borderPadding=4,
            spaceBefore=4,
            spaceAfter=7,
        ),
    }


def flush_paragraph(lines: list[str], story: list, style_map: dict) -> None:
    if not lines:
        return
    text = " ".join(line.strip() for line in lines if line.strip())
    if text:
        story.append(Paragraph(inline_markup(text), style_map["body"]))
    lines.clear()


def build_story(markdown: str) -> list:
    style_map = styles()
    story: list = []
    paragraph_lines: list[str] = []
    code_lines: list[str] = []
    in_code = False
    first_heading = True

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), style_map["code"]))
                code_lines = []
                in_code = False
            else:
                flush_paragraph(paragraph_lines, story, style_map)
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            flush_paragraph(paragraph_lines, story, style_map)
            continue

        if line == "---":
            flush_paragraph(paragraph_lines, story, style_map)
            story.append(Spacer(1, 6))
            continue

        if line.startswith("# "):
            flush_paragraph(paragraph_lines, story, style_map)
            text = line[2:].strip()
            if first_heading:
                story.append(Paragraph(inline_markup(text), style_map["title"]))
                first_heading = False
            else:
                story.append(PageBreak())
                story.append(Paragraph(inline_markup(text), style_map["h1"]))
            continue

        if line.startswith("## "):
            flush_paragraph(paragraph_lines, story, style_map)
            story.append(Paragraph(inline_markup(line[3:].strip()), style_map["h2"]))
            continue

        if line.startswith("### "):
            flush_paragraph(paragraph_lines, story, style_map)
            story.append(Paragraph(inline_markup(line[4:].strip()), style_map["h3"]))
            continue

        if line.startswith("- "):
            flush_paragraph(paragraph_lines, story, style_map)
            story.append(Paragraph("- " + inline_markup(line[2:].strip()), style_map["bullet"]))
            continue

        paragraph_lines.append(line)

    flush_paragraph(paragraph_lines, story, style_map)
    if code_lines:
        story.append(Preformatted("\n".join(code_lines), style_map["code"]))

    return story


def main() -> None:
    markdown = SOURCE.read_text(encoding="utf-8")
    doc = SimpleDocTemplate(
        str(TARGET),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=18 * mm,
        title="OT SOC Live Testing and Production Guide",
        author="OT-Based SOC Incident Response Platform",
    )
    doc.build(build_story(markdown), onFirstPage=on_page, onLaterPages=on_page)
    print(TARGET)


if __name__ == "__main__":
    main()
