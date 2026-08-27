#!/usr/bin/env python3
"""Render Online Resource 2 Markdown as a stable submission PDF."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "manuscript" / "Online_Resource_2_reproduction_manifest.md"
OUTPUT = ROOT / "manuscript" / "Online_Resource_2_reproduction_manifest.pdf"

BLUE = colors.HexColor("#2E74B5")
INK = colors.HexColor("#20262E")
MUTED = colors.HexColor("#5D6A75")
GRID = colors.HexColor("#C9D2DC")
HEADER = colors.HexColor("#EEF3F8")


def inline_markup(text: str) -> str:
    escaped = html.escape(text.strip())
    escaped = re.sub(
        r"`([^`]+)`",
        lambda match: f'<font name="Courier">{match.group(1)}</font>',
        escaped,
    )
    escaped = re.sub(
        r"(https?://[^\s<]+)",
        lambda match: f'<link href="{match.group(1)}" color="#2E74B5">{match.group(1)}</link>',
        escaped,
    )
    return escaped


def page_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 12 * mm, "Online Resource 2 - Reproduction Manifest")
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build() -> Path:
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "OR2Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=BLUE,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    heading = ParagraphStyle(
        "OR2Heading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=15,
        textColor=BLUE,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True,
    )
    body = ParagraphStyle(
        "OR2Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.2,
        leading=12.5,
        textColor=INK,
        alignment=TA_LEFT,
        spaceAfter=5,
    )
    bullet = ParagraphStyle(
        "OR2Bullet",
        parent=body,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3,
    )
    code = ParagraphStyle(
        "OR2Code",
        parent=body,
        fontName="Courier",
        fontSize=7.6,
        leading=10,
        leftIndent=6,
        rightIndent=6,
        borderColor=GRID,
        borderWidth=0.5,
        borderPadding=6,
        backColor=colors.HexColor("#F6F8FA"),
        spaceBefore=4,
        spaceAfter=7,
    )
    table_header = ParagraphStyle(
        "OR2TableHeader", parent=body, fontName="Helvetica-Bold", fontSize=7.6, leading=9
    )
    table_body = ParagraphStyle(
        "OR2TableBody", parent=body, fontSize=7.4, leading=9
    )

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title="Online Resource 2: Reproduction Manifest",
        author="Manuscript supplementary information",
        subject="Reproduction manifest for task-set reduction study",
    )
    story = []
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    index = 0
    paragraph_buffer: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_buffer:
            story.append(Paragraph(inline_markup(" ".join(paragraph_buffer)), body))
            paragraph_buffer.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[2:]), title))
            index += 1
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[3:]), heading))
            index += 1
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            index += 1
            code_lines = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            story.append(Preformatted("\n".join(code_lines), code))
            index += 1
            continue
        if stripped.startswith("|"):
            flush_paragraph()
            table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            raw_rows = [[cell.strip() for cell in row.strip("|").split("|")] for row in table_lines]
            raw_rows = [row for row in raw_rows if not all(re.fullmatch(r":?-+:?", c) for c in row)]
            data = []
            for row_index, row in enumerate(raw_rows):
                style = table_header if row_index == 0 else table_body
                data.append([Paragraph(inline_markup(cell), style) for cell in row])
            available = A4[0] - 36 * mm
            if len(data[0]) == 4:
                widths = [available * f for f in (0.21, 0.25, 0.24, 0.30)]
            elif len(data[0]) == 2:
                widths = [available * 0.28, available * 0.72]
            else:
                widths = [available / len(data[0])] * len(data[0])
            table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), HEADER),
                        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
                        ("GRID", (0, 0), (-1, -1), 0.5, GRID),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.extend([table, Spacer(1, 6)])
            continue
        if stripped.startswith("- "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[2:]), bullet, bulletText="-"))
            index += 1
            continue
        paragraph_buffer.append(stripped)
        index += 1

    flush_paragraph()
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    print(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    build()
