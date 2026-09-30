import ast
import json
import re
from html import escape as html_escape
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List

import typst
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image as ReportLabImage
from reportlab.platypus import ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate, Spacer
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["mathtext.fontset"] = "stix"
from matplotlib.mathtext import math_to_image


TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent / "templates" / "study_guide.typ"
)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return (
        str(value)
        .replace("\\(", "")
        .replace("\\)", "")
        .replace("\\[", "")
        .replace("\\]", "")
        .strip()
    )


def escape_typst_plain_text(value: Any) -> str:
    """Escape plain text so it is safe to insert into Typst markup."""
    text = clean_text(value)
    text = text.replace("\\", "\\\\")
    for character in ("#", "$", "*", "_", "[", "]", "{", "}"):
        text = text.replace(character, "\\" + character)
    return text


def markdown_to_typst_text(value: Any) -> str:
    """
    Convert the small Markdown subset commonly returned by the AI into real
    Typst inline formatting.

    Markdown:
      **bold** / __bold__ -> Typst *bold*
      *italic* / _italic_ -> Typst _italic_
      ***bold italic*** -> Typst *[bold italic]*

    Everything else is escaped as plain text.
    """
    text = clean_text(value)
    if not text:
        return ""

    placeholders: list[tuple[str, str]] = []

    def protect(pattern: str, replacement_builder) -> None:
        nonlocal text

        def repl(match: re.Match[str]) -> str:
            token = f"__NOTESUP_FMT_{len(placeholders)}__"
            inner = escape_typst_plain_text(match.group(1))
            placeholders.append((token, replacement_builder(inner)))
            return token

        text = re.sub(pattern, repl, text, flags=re.DOTALL)

    # Handle the most specific form first so ***bold italic*** is not
    # interpreted as separate bold/italic markers.
    protect(r"\*\*\*(.+?)\*\*\*", lambda inner: f"*_{inner}_*")
    protect(r"\*\*(.+?)\*\*", lambda inner: f"*{inner}*")
    protect(r"__(.+?)__", lambda inner: f"*{inner}*")
    protect(r"(?<!\*)\*([^*\n]+)\*(?!\*)", lambda inner: f"_{inner}_")
    protect(r"(?<!_)_([^_\n]+)_(?!_)", lambda inner: f"_{inner}_")

    escaped = escape_typst_plain_text(text)

    for token, replacement in placeholders:
        # Placeholder tokens contain underscores, which are escaped by
        # escape_typst_plain_text(). Search for the exact escaped token.
        escaped_token = escape_typst_plain_text(token)
        escaped = escaped.replace(escaped_token, replacement)

        # Safety net: never allow an internal formatting token to reach the PDF.
        escaped = escaped.replace(token, replacement)

    return escaped


# Keep the old function name as a compatibility wrapper for callers that only
# need escaped plain text.
def escape_typst_text(value: Any) -> str:
    return markdown_to_typst_text(value)



def extract_equation(value: Any) -> str:
    """Extract only the equation from an AI equation object/string."""
    if isinstance(value, dict):
        return clean_text(value.get("eq", ""))

    if not isinstance(value, str):
        return clean_text(value)

    raw = value.strip()
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(raw)
            if isinstance(parsed, dict) and "eq" in parsed:
                return clean_text(parsed["eq"])
        except (ValueError, SyntaxError, TypeError, json.JSONDecodeError):
            pass

    match = re.search(
        r"""['"]eq['"]\s*:\s*['"](.*?)['"]\s*,\s*['"]variables['"]""",
        raw,
        flags=re.DOTALL,
    )
    if match:
        return match.group(1).replace("\\\\", "\\").strip()

    return raw


def escape_typst_title(value: Any) -> str:
    return escape_typst_text(value)


def replace_braced_command(equation: str, command: str, function: str) -> str:
    pattern = rf"{re.escape(command)}\{{([^{{}}]*)\}}"
    if function == '"':
        return re.sub(
            pattern,
            lambda match: '"' + match.group(1).replace('"', '\\"') + '"',
            equation,
        )
    return re.sub(pattern, lambda match: f"{function}({match.group(1)})", equation)


def replace_fraction_commands(equation: str) -> str:
    fraction_pattern = r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}"
    while re.search(fraction_pattern, equation):
        equation = re.sub(
            fraction_pattern,
            lambda match: f"frac({match.group(1)}, {match.group(2)})",
            equation,
        )
    return equation


def replace_sqrt_commands(equation: str) -> str:
    sqrt_pattern = r"\\sqrt\s*\{([^{}]*)\}"
    return re.sub(
        sqrt_pattern,
        lambda match: f"sqrt({match.group(1)})",
        equation,
    )




def normalize_unicode_math(equation: str) -> str:
    """Convert Unicode math decorations/subscripts into Typst-safe syntax."""
    equation = re.sub(r"([A-Za-z0-9])\u0302", r"hat(\1)", equation)
    equation = re.sub(r"([A-Za-z0-9])\u0304", r"overline(\1)", equation)

    subscript_map = str.maketrans({
        "₀": "_0", "₁": "_1", "₂": "_2", "₃": "_3", "₄": "_4",
        "₅": "_5", "₆": "_6", "₇": "_7", "₈": "_8", "₉": "_9",
        "ₐ": "_a", "ₑ": "_e", "ₕ": "_h", "ᵢ": "_i", "ⱼ": "_j",
        "ₖ": "_k", "ₗ": "_l", "ₘ": "_m", "ₙ": "_n", "ₒ": "_o",
        "ₚ": "_p", "ᵣ": "_r", "ₛ": "_s", "ₜ": "_t", "ᵤ": "_u",
        "ᵥ": "_v", "ₓ": "_x",
    })
    return equation.translate(subscript_map)



def equation_to_typst(value: Any) -> str:
    equation = extract_equation(value)
    if not equation:
        return ""

    equation = equation.strip().strip("$").strip()
    equation = normalize_unicode_math(equation)

    replacements = {
        "\\left": "",
        "\\right": "",
        "\\,": " ",
        "\\;": " ",
        "\\:": " ",
        "\\!": "",
        "\\quad": " ",
        "\\qquad": " ",
        "\\cdot": " dot ",
        "\\times": " times ",
        "\\pm": " plus.minus ",
        "\\leq": " <= ",
        "\\le": " <= ",
        "\\geq": " >= ",
        "\\ge": " >= ",
        "\\neq": " != ",
        "\\infty": " infinity ",
        "\\rightarrow": " arrow ",
        "\\to": " arrow ",
        "\\mid": " | ",
    }
    for old, new in replacements.items():
        equation = equation.replace(old, new)

    greek = {
        "\\alpha": "alpha", "\\beta": "beta", "\\gamma": "gamma",
        "\\delta": "delta", "\\epsilon": "epsilon", "\\varepsilon": "epsilon",
        "\\theta": "theta", "\\lambda": "lambda", "\\mu": "mu",
        "\\pi": "pi", "\\rho": "rho", "\\sigma": "sigma", "\\tau": "tau",
        "\\phi": "phi", "\\varphi": "phi", "\\omega": "omega",
        "\\Delta": "Delta", "\\Lambda": "Lambda", "\\Sigma": "Sigma",
        "\\Phi": "Phi", "\\Omega": "Omega",
    }
    for latex, typst_name in greek.items():
        equation = equation.replace(latex, typst_name)

    equation = re.sub(
        r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}",
        lambda m: f"frac({m.group(1)}, {m.group(2)})",
        equation,
    )
    equation = re.sub(
        r"\\sqrt\s*\{([^{}]*)\}",
        lambda m: f"sqrt({m.group(1)})",
        equation,
    )
    equation = re.sub(
        r"\\hat\s*\{([^{}]*)\}",
        lambda m: f"hat({m.group(1)})",
        equation,
    )
    equation = re.sub(
        r"\\bar\s*\{([^{}]*)\}",
        lambda m: f"overline({m.group(1)})",
        equation,
    )
    equation = re.sub(
        r"\\mathbf\s*\{([^{}]*)\}",
        lambda m: f"bold({m.group(1)})",
        equation,
    )
    equation = re.sub(
        r"\\mathrm\s*\{([^{}]*)\}",
        lambda m: f"upright({m.group(1)})",
        equation,
    )
    equation = re.sub(
        r"\\text\s*\{([^{}]*)\}",
        lambda m: f'"{m.group(1)}"',
        equation,
    )

    matrix = re.search(
        r"\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}",
        equation,
        flags=re.DOTALL,
    )
    if matrix:
        rows = [row.strip() for row in matrix.group(1).split("\\\\") if row.strip()]
        rendered_rows = [
            ", ".join(cell.strip() for cell in row.split("&"))
            for row in rows
        ]
        equation = (
            equation[:matrix.start()]
            + "mat(" + "; ".join(rendered_rows) + ")"
            + equation[matrix.end():]
        )

    equation = equation.replace("\\\\", " ")
    return equation.strip()


def add_text_paragraphs(lines: List[str], value: Any) -> None:
    text = clean_text(value)
    if not text:
        return

    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    for paragraph in paragraphs:
        lines.append(markdown_to_typst_text(paragraph))
        lines.append("")


def add_bullets(lines: List[str], items: Any) -> None:
    if not isinstance(items, list):
        return

    for item in items:
        text = clean_text(item)
        if text:
            lines.append(f"- {markdown_to_typst_text(text)}")

    if items:
        lines.append("")



def add_equation(lines: List[str], equation: Any, safe_text: bool = False) -> None:
    equation_text = extract_equation(equation)
    if not equation_text:
        return

    if safe_text:
        # Last-resort representation: unsupported LaTeX/Unicode is rendered as text.
        lines.append("#align(center)[")
        lines.append("  #set text(size: 11pt)")
        lines.append("  " + escape_typst_text(equation_text))
        lines.append("]")
        lines.append("")
        return

    equation_text = equation_to_typst(equation)
    if not equation_text:
        return

    lines.append("#align(center)[")
    lines.append("  #set text(size: 12.5pt)")
    lines.append("  $" + equation_text + "$")
    lines.append("]")
    lines.append("")



def build_study_guide_typst(
    notes: Dict[str, Any] | List[Dict[str, Any]],
    title: str,
    safe_equations: bool = False,
) -> str:
    note_list = notes if isinstance(notes, list) else [notes]
    lines: List[str] = []

    lines.append(f"= {escape_typst_title(title or 'AI Study Guide')}")
    lines.append("")
    lines.append("Generated by *Note'sUp* — AI Study Guide")
    lines.append("")

    for index, note in enumerate(note_list, start=1):
        if not isinstance(note, dict):
            continue

        topic = clean_text(note.get("topic")) or "Study Topic"
        lines.append(f"== {index}. {escape_typst_title(topic)}")
        lines.append("")

        status = clean_text(note.get("status"))
        if status:
            lines.append(f"*Status:* {markdown_to_typst_text(status)}")
            lines.append("")

        if note.get("why_needed"):
            lines.append("== Why this is needed")
            lines.append("")
            add_text_paragraphs(lines, note.get("why_needed"))

        if note.get("student_knowledge"):
            lines.append("== What you already know")
            lines.append("")
            add_text_paragraphs(lines, note.get("student_knowledge"))

        missing_information = note.get("missing_information")
        if isinstance(missing_information, list) and missing_information:
            lines.append("== Focus on these gaps")
            lines.append("")
            add_bullets(lines, missing_information)

        sections = note.get("sections")
        if isinstance(sections, list):
            for section in sections:
                if not isinstance(section, dict):
                    continue

                heading = clean_text(section.get("heading"))
                if heading:
                    lines.append(f"== {escape_typst_title(heading)}")
                    lines.append("")

                add_text_paragraphs(lines, section.get("content"))

                equations = section.get("equations")
                if isinstance(equations, list):
                    for equation in equations:
                        add_equation(lines, equation, safe_text=safe_equations)

        exam_points = note.get("exam_points")
        if isinstance(exam_points, list) and exam_points:
            lines.append("== Exam Points")
            lines.append("")
            add_bullets(lines, exam_points)

        sources = note.get("sources")
        if isinstance(sources, list) and sources:
            source_text = " • ".join(
                clean_text(source)
                for source in sources
                if clean_text(source)
            )
            if source_text:
                lines.append(
                    f"*Sources:* {markdown_to_typst_text(source_text)}"
                )
                lines.append("")


    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.replace("{{CONTENT}}", "\n".join(lines))



def compile_study_guide_pdf_reportlab(
    notes: Dict[str, Any] | List[Dict[str, Any]],
    title: str,
) -> bytes:
    """Reliable PDF fallback that does not parse AI output as Typst markup."""
    note_list = notes if isinstance(notes, list) else [notes]
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=22 * mm,
        bottomMargin=20 * mm,
        title=clean_text(title) or "AI Study Guide",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("NoteSupTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=19, leading=23, spaceAfter=10)
    topic_style = ParagraphStyle("NoteSupTopic", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=16, leading=20, spaceBefore=8, spaceAfter=8)
    section_style = ParagraphStyle("NoteSupSection", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12.5, leading=16, spaceBefore=8, spaceAfter=5)
    body_style = ParagraphStyle("NoteSupBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, spaceAfter=7)
    small_style = ParagraphStyle("NoteSupSmall", parent=body_style, fontSize=8.5, leading=11)
    equation_style = ParagraphStyle("NoteSupEquation", parent=body_style, fontName="Courier", fontSize=8.5, leading=12, alignment=TA_CENTER, leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=8)

    story = [
        Paragraph(html_escape(clean_text(title) or "AI Study Guide"), title_style),
        Paragraph("Generated by Note'sUp — AI Study Guide", small_style),
        Spacer(1, 5 * mm),
    ]

    def add_math_image(equation_text: str) -> None:
        equation_text = clean_text(equation_text)
        if not equation_text:
            return

        # Convert common escaped math delimiters into matplotlib mathtext.
        equation_text = equation_text.strip()
        equation_text = equation_text.replace(r"\\(", "").replace(r"\\)", "")
        equation_text = equation_text.replace(r"\\[", "").replace(r"\\]", "")
        if equation_text.startswith("$") and equation_text.endswith("$"):
            math_expression = equation_text[1:-1].strip()
        else:
            math_expression = equation_text

        # Mathtext uses TeX-style syntax and renders subscripts, superscripts,
        # fractions, hats, Greek symbols, matrices, and operators cleanly.
        if not (math_expression.startswith("$") and math_expression.endswith("$")):
            math_expression = "$" + math_expression + "$"

        image_buffer = BytesIO()
        try:
            math_to_image(
                math_expression,
                image_buffer,
                format="png",
                dpi=160,
                color="black",
            )
            image_buffer.seek(0)
            image = ReportLabImage(image_buffer)
            max_width = 155 * mm
            max_height = 18 * mm
            scale = min(
                max_width / image.imageWidth,
                max_height / image.imageHeight,
                1.0,
            )
            image.drawWidth = image.imageWidth * scale
            image.drawHeight = image.imageHeight * scale
            image.hAlign = "CENTER"
            story.append(image)
            story.append(Spacer(1, 2 * mm))
        except Exception as equation_error:
            print(
                f"MATH IMAGE ERROR | equation={equation_text!r} | "
                f"type={type(equation_error).__name__} | error={repr(equation_error)}"
            )
            # If mathtext cannot parse a future equation, preserve it as text.
            story.append(Paragraph(html_escape(equation_text), equation_style))

    def extract_equation_fragments(line: str) -> list[str]:
        line = clean_text(line)
        if not line:
            return []

        fragments = []

        # Explicit math delimiters first.
        for pattern in (r"\\\((.+?)\\\)", r"\\\[(.+?)\\\]", r"\$(.+?)\$"):
            fragments.extend(re.findall(pattern, line, flags=re.DOTALL))

        if fragments:
            return [clean_text(fragment) for fragment in fragments if clean_text(fragment)]

        # Detect equation-like spans in generated prose. This handles common
        # AI output such as "The dynamics are: x_t = A x_{t-1} + w_t, where ...".
        if "=" not in line:
            return []

        candidates = re.findall(
            r"([A-Za-z\\][A-Za-z0-9_{}\\^|]*\s*=\s*[^.]+?)(?=,\s+where\\b|,\s+and\\b|\.\s+|$)",
            line,
        )

        for candidate in candidates:
            candidate = candidate.strip(" ,")
            if len(candidate) >= 5 and (
                "_" in candidate
                or "\\" in candidate
                or "^" in candidate
                or any(op in candidate for op in ("+", "-", "*", "/", "(", ")", "[", "]"))
            ):
                fragments.append(candidate)

        return fragments

    def add_paragraph(value: Any, style=body_style) -> None:
        text = clean_text(value)
        if not text:
            return

        for paragraph in [p.strip() for p in text.split("\n\n") if p.strip()]:
            lines_in_paragraph = [line.strip() for line in paragraph.split("\n") if line.strip()]

            for line in lines_in_paragraph:
                fragments = extract_equation_fragments(line)

                if fragments:
                    # Remove the equation fragments from prose so the same
                    # formula is not printed twice.
                    remaining = line
                    for fragment in fragments:
                        remaining = remaining.replace(fragment, "")
                    remaining = re.sub(r"\s{2,}", " ", remaining).strip(" :,-")

                    if remaining:
                        story.append(
                            Paragraph(
                                html_escape(remaining),
                                style,
                            )
                        )

                    for fragment in fragments:
                        add_math_image(fragment)
                else:
                    story.append(
                        Paragraph(
                            html_escape(line),
                            style,
                        )
                    )

    for index, note in enumerate(note_list, start=1):
        if not isinstance(note, dict):
            continue

        topic = clean_text(note.get("topic")) or "Study Topic"
        story.append(Paragraph(html_escape(f"{index}. {topic}"), topic_style))

        status = clean_text(note.get("status"))
        if status:
            story.append(Paragraph(html_escape(f"Status: {status}"), small_style))

        if note.get("why_needed"):
            story.append(Paragraph("Why this is needed", section_style))
            add_paragraph(note.get("why_needed"))

        if note.get("student_knowledge"):
            story.append(Paragraph("What you already know", section_style))
            add_paragraph(note.get("student_knowledge"))

        missing = note.get("missing_information")
        if isinstance(missing, list) and missing:
            story.append(Paragraph("Focus on these gaps", section_style))
            items = []
            for item in missing:
                text = clean_text(item)
                if text:
                    items.append(ListItem(Paragraph(html_escape(text), body_style), leftIndent=12))
            if items:
                story.append(ListFlowable(items, bulletType="bullet", leftIndent=14))
                story.append(Spacer(1, 3 * mm))

        sections = note.get("sections")
        if isinstance(sections, list):
            for section in sections:
                if not isinstance(section, dict):
                    continue

                heading = clean_text(section.get("heading"))
                if heading:
                    story.append(Paragraph(html_escape(heading), section_style))

                add_paragraph(section.get("content"))

                equations = section.get("equations")
                if isinstance(equations, list):
                    for equation in equations:
                        equation_text = extract_equation(equation)
                        if equation_text:
                            add_math_image(equation_text)

        exam_points = note.get("exam_points")
        if isinstance(exam_points, list) and exam_points:
            story.append(Paragraph("Exam Points", section_style))
            items = []
            for item in exam_points:
                text = clean_text(item)
                if text:
                    items.append(ListItem(Paragraph(html_escape(text), body_style), leftIndent=12))
            if items:
                story.append(ListFlowable(items, bulletType="bullet", leftIndent=14))
                story.append(Spacer(1, 3 * mm))

        sources = note.get("sources")
        if isinstance(sources, list) and sources:
            source_text = " • ".join(clean_text(source) for source in sources if clean_text(source))
            if source_text:
                story.append(Paragraph(html_escape(f"Sources: {source_text}"), small_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    if not pdf_bytes:
        raise RuntimeError("ReportLab returned an empty PDF.")

    print(f"REPORTLAB PDF SUCCESS | title={title!r} | bytes={len(pdf_bytes)}")
    return pdf_bytes


def compile_study_guide_pdf(
    notes: Dict[str, Any] | List[Dict[str, Any]],
    title: str,
) -> bytes:
    source = build_study_guide_typst(notes, title)

    try:
        pdf_bytes = typst.compile(source.encode("utf-8"), format="pdf")
    except Exception as error:
        print(
            f"TYPST PDF ERROR | type={type(error).__name__} | "
            f"error={repr(error)}"
        )

        # Retry once with all equations rendered as escaped text. This keeps
        # PDF generation reliable even for a future unsupported math format.
        try:
            safe_source = build_study_guide_typst(
                notes,
                title,
                safe_equations=True,
            )
            pdf_bytes = typst.compile(
                safe_source.encode("utf-8"),
                format="pdf",
            )
            print("TYPST PDF SAFE FALLBACK SUCCESS | equations_as_text=true")
        except Exception as fallback_error:
            print(
                f"TYPST PDF FALLBACK ERROR | type={type(fallback_error).__name__} | "
                f"error={repr(fallback_error)}"
            )

            # Final safety net: ReportLab receives the structured note data
            # directly, so AI-generated braces, brackets, dollar signs, and
            # other Typst delimiters can never break PDF generation.
            try:
                return compile_study_guide_pdf_reportlab(notes, title)
            except Exception as reportlab_error:
                print(
                    f"REPORTLAB PDF ERROR | type={type(reportlab_error).__name__} | "
                    f"error={repr(reportlab_error)}"
                )
                raise RuntimeError(
                    f"PDF generation failed in Typst and ReportLab: "
                    f"{error}; fallback={reportlab_error}"
                ) from error

    if not pdf_bytes:
        raise RuntimeError("Typst returned an empty PDF.")

    print(
        f"TYPST PDF SUCCESS | title={title!r} | "
        f"bytes={len(pdf_bytes)}"
    )

    return pdf_bytes
