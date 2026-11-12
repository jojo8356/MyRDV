#!/usr/bin/env python3
"""
build_pdf.py — Compile le cahier des charges MyRDV (Markdown) en PDF.

Thème « GitHub Light + startup » :
  - feuille de style inspirée de github-markdown-css (Primer) ;
  - couleur d'accent indigo/violet, badges, encadrés d'appel ;
  - typographie Inter, code JetBrains Mono ;
  - sommaire cliquable, signets PDF, en-têtes/pieds paginés, numéros de page.

Dépendances (dev uniquement) : reportlab, markdown
Usage :
    python build_pdf.py                      # document principal + annexes
    python build_pdf.py --only 06            # un seul document
    python build_pdf.py --out ../../pdf
"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
from pathlib import Path

import markdown
from reportlab.graphics.shapes import Drawing, Line, Rect
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, HRFlowable,
                                KeepTogether, NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle,
                                Preformatted, Flowable)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parent
CHARGE = ROOT.parent                      # docs/cahier-des-charges
def _fonts_dir() -> Path:
    candidates = []
    if os.environ.get("MYRDV_FONTS"):
        candidates.append(Path(os.environ["MYRDV_FONTS"]))
    candidates += [ROOT.parent / ".fonts", Path.home() / "fonts"]
    for path in candidates:
        if path.is_dir() and (path / "Inter-Regular.ttf").exists():
            return path
    return candidates[0] if candidates else Path(".fonts")


FONTS = _fonts_dir()

# --------------------------------------------------------------------------
# 1. Palette GitHub Light + accent startup
# --------------------------------------------------------------------------
FG = colors.HexColor("#1F2328")          # texte
FG_MUTED = colors.HexColor("#59636E")    # texte secondaire
CANVAS_DEFAULT = colors.HexColor("#FFFFFF")
CANVAS_SUBTLE = colors.HexColor("#F6F8FA")
BORDER = colors.HexColor("#D1D9E0")
BORDER_MUTED = colors.HexColor("#E6EAEF")
ACCENT = colors.HexColor("#6C4DF6")      # violet startup
ACCENT_SOFT = colors.HexColor("#EEEBFF")
ACCENT_DARK = colors.HexColor("#4B2FD0")
INFO = colors.HexColor("#0969DA")
INFO_SOFT = colors.HexColor("#DDF4FF")
DONE = colors.HexColor("#1A7F37")
DONE_SOFT = colors.HexColor("#DAFBE1")
WARN = colors.HexColor("#9A6700")
WARN_SOFT = colors.HexColor("#FFF8C5")
DANGER = colors.HexColor("#CF222E")
DANGER_SOFT = colors.HexColor("#FFEBE9")

PAGE_W, PAGE_H = A4
M_LEFT = M_RIGHT = 17 * mm
M_TOP = 20 * mm
M_BOTTOM = 17 * mm
CONTENT_W = PAGE_W - M_LEFT - M_RIGHT


# --------------------------------------------------------------------------
# 2. Enregistrement des polices
# --------------------------------------------------------------------------
def register_fonts() -> None:
    pairs = {
        "Inter": "Inter-Regular.ttf",
        "Inter-Light": "Inter-Light.ttf",
        "Inter-Medium": "Inter-Medium.ttf",
        "Inter-SemiBold": "Inter-SemiBold.ttf",
        "Inter-Bold": "Inter-Bold.ttf",
        "Inter-Italic": "Inter-Italic.ttf",
        "Inter-MediumItalic": "Inter-MediumItalic.ttf",
        "Inter-SemiBoldItalic": "Inter-SemiBoldItalic.ttf",
        "Inter-BoldItalic": "Inter-BoldItalic.ttf",
        "JBMono": "JetBrainsMono-Regular.ttf",
        "JBMono-Medium": "JetBrainsMono-Medium.ttf",
        "JBMono-Bold": "JetBrainsMono-Bold.ttf",
    }
    for alias, filename in pairs.items():
        path = FONTS / filename
        if not path.exists():
            raise SystemExit(
                f"Police manquante : {path}\n"
                "Placez les fichiers Inter/JetBrains Mono dans $MYRDV_FONTS."
            )
        pdfmetrics.registerFont(TTFont(alias, str(path)))
    pdfmetrics.registerFontFamily("Inter", normal="Inter", bold="Inter-SemiBold",
                                  italic="Inter-Italic", boldItalic="Inter-SemiBoldItalic")
    pdfmetrics.registerFontFamily("JBMono", normal="JBMono", bold="JBMono-Bold",
                                  italic="JBMono", boldItalic="JBMono-Bold")


# --------------------------------------------------------------------------
# 3. Styles (github-markdown-css, échelle adaptée A4)
# --------------------------------------------------------------------------
def build_styles() -> dict:
    s: dict[str, ParagraphStyle] = {}
    base = dict(fontName="Inter", textColor=FG, alignment=TA_LEFT)

    s["body"] = ParagraphStyle("body", fontSize=9.3, leading=14.4,
                               spaceBefore=0, spaceAfter=5.4, **base)
    s["body_list"] = ParagraphStyle("body_list", parent=s["body"], spaceAfter=2.6,
                                    leading=14.0)
    s["lead"] = ParagraphStyle("lead", parent=s["body"], fontSize=11.4, leading=17.6,
                               textColor=FG_MUTED, spaceAfter=8)
    s["tiny"] = ParagraphStyle("tiny", parent=s["body"], fontSize=7.8, leading=11.4,
                               textColor=FG_MUTED)
    for level, size, before, after in ((1, 21, 2, 8), (2, 14.6, 12, 6),
                                       (3, 11.6, 10, 4), (4, 10.2, 8, 3),
                                       (5, 9.6, 6, 2)):
        s[f"h{level}"] = ParagraphStyle(
            f"h{level}", fontName="Inter-SemiBold", fontSize=size,
            leading=size * 1.32, textColor=FG, spaceBefore=before, spaceAfter=after,
            keepWithNext=1)
    s["h1"].fontName = "Inter-Bold"
    s["h1"].textColor = FG
    s["blockquote"] = ParagraphStyle("blockquote", parent=s["body"], fontSize=9.0,
                                     leading=13.8, textColor=FG_MUTED,
                                     leftIndent=8, spaceAfter=3.4)
    s["callout_title"] = ParagraphStyle("callout_title", fontName="Inter-SemiBold",
                                        fontSize=8.4, leading=12, textColor=FG,
                                        spaceAfter=1.5)
    s["code"] = ParagraphStyle("code", fontName="JBMono", fontSize=7.5, leading=10.9,
                               textColor=FG, spaceBefore=0, spaceAfter=0)
    s["code_inline"] = ParagraphStyle("code_inline", parent=s["body"],
                                      fontName="JBMono", fontSize=7.9, leading=12.6)
    s["table"] = ParagraphStyle("table", fontName="Inter", fontSize=7.6, leading=10.4,
                                textColor=FG)
    s["table_header"] = ParagraphStyle("table_header", fontName="Inter-SemiBold",
                                       fontSize=7.4, leading=10.0,
                                       textColor=colors.HexColor("#3A4150"))
    s["table_muted"] = ParagraphStyle("table_muted", parent=s["table"],
                                      textColor=FG_MUTED)
    s["toc0"] = ParagraphStyle("toc0", fontName="Inter-SemiBold", fontSize=9.6,
                               leading=15, textColor=FG, leftIndent=0,
                               spaceBefore=5.5)
    s["toc1"] = ParagraphStyle("toc1", fontName="Inter", fontSize=8.8, leading=13.4,
                               textColor=FG_MUTED, leftIndent=10)
    s["toc2"] = ParagraphStyle("toc2", fontName="Inter", fontSize=8.2, leading=12.6,
                               textColor=FG_MUTED, leftIndent=22)
    s["cover_kicker"] = ParagraphStyle("cover_kicker", fontName="Inter-SemiBold",
                                       fontSize=8.6, leading=12, textColor=ACCENT,
                                       spaceAfter=10)
    s["cover_title"] = ParagraphStyle("cover_title", fontName="Inter-Bold",
                                      fontSize=38, leading=42, textColor=FG,
                                      spaceAfter=10)
    s["cover_sub"] = ParagraphStyle("cover_sub", fontName="Inter-Light",
                                    fontSize=15.5, leading=22, textColor=FG_MUTED,
                                    spaceAfter=16)
    s["cover_meta"] = ParagraphStyle("cover_meta", fontName="Inter", fontSize=9,
                                     leading=15, textColor=FG_MUTED)
    s["cover_stat_n"] = ParagraphStyle("cover_stat_n", fontName="Inter-Bold",
                                       fontSize=17, leading=19, textColor=FG,
                                       alignment=TA_CENTER)
    s["cover_stat_l"] = ParagraphStyle("cover_stat_l", fontName="Inter", fontSize=7.4,
                                       leading=9.6, textColor=FG_MUTED,
                                       alignment=TA_CENTER)
    return s


S = {}


# --------------------------------------------------------------------------
# 4. Inline : code, gras, liens, puces
# --------------------------------------------------------------------------
INLINE_CODE = re.compile(r"`([^`]+)`")
NOTE_RE = re.compile(r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$")

CALL_OUT = {
    "NOTE": ("Note", INFO, INFO_SOFT),
    "TIP": ("Astuce", DONE, DONE_SOFT),
    "IMPORTANT": ("Important", ACCENT, ACCENT_SOFT),
    "WARNING": ("Attention", WARN, WARN_SOFT),
    "CAUTION": ("Prudence", DANGER, DANGER_SOFT),
}


def code_chip(text: str) -> str:
    """`code` -> pastille grise (github-markdown-css).

    Au-delà de 24 caractères, la pastille n'est plus encadrée d'espaces
    insécables : dans une cellule étroite, ces espaces empêchent reportlab de
    replier le jeton, qui déborde alors de la colonne.
    """
    escaped = html.escape(text).replace("\u00a0", "&nbsp;")
    pad = "" if len(text) > 24 else "&nbsp;"
    return (f'<font name="JBMono" size="7.6" backColor="#EFF2F5" '
            f'color="#1F2328">{pad}{escaped}{pad}</font>')


def md_inline(text: str) -> str:
    """Conversion inline Markdown -> balisage ReportLab (à passer à md_to_rl)."""
    hold: list[str] = []

    def keep(fragment: str) -> str:
        hold.append(fragment)
        return f"\x00{len(hold) - 1}\x00"

    # liens [texte](url) : on garde le texte, l'URL devient une note discrète
    def link(m):
        label, url = m.group(1), m.group(2)
        if url.startswith("#"):
            return keep(md_inline(label))
        short = url.replace("https://", "").replace("http://", "")
        if len(short) > 58:
            short = short[:55] + "…"
        return keep(md_inline(label) + f'<font size="6.6" color="#6E7781"> ({short})</font>')

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)
    text = INLINE_CODE.sub(lambda m: keep(code_chip(m.group(1))), text)
    text = text.replace("\u2011", "-")
    return text


def md_to_rl(text: str) -> str:
    """Échappe le HTML puis applique les conversions ReportLab."""
    text = md_inline(text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # italique : on tolère le retour à la ligne (les paragraphes Markdown sont
    # repliés sur plusieurs lignes), sinon les astérisques restent visibles.
    text = re.sub(r"(?<![\w*])\*([^*]+?)\*(?![\w*])", r"<i>\1</i>", text, flags=re.S)
    text = re.sub(r"~~(.+?)~~", r"<strike>\1</strike>", text)

    def restore(m):
        return hold[int(m.group(1))]

    hold: list[str] = []
    return text


# On a besoin d'un état partagé pour les pastilles : on encapsule.
TAGS = r"(<\/?b>|<\/?i>|<\/?strike>)"
TOKEN = r"(\x00\d+\x00)"


def md_to_rl(text: str) -> str:  # noqa: F811  (seconde définition volontaire)
    """Markdown inline -> balisage ReportLab.

    Le gras/italique est appliqué AVANT l'échappement, puis seules les portions
    hors balises et hors pastilles sont échappées : ainsi `**texte `code`**`
    reste entièrement en gras.
    """
    hold: list[str] = []

    def keep(fragment: str) -> str:
        hold.append(fragment)
        return f"\x00{len(hold) - 1}\x00"

    def link(m):
        label, url = m.group(1), m.group(2)
        # Lien interne (ancre ou autre fichier du dossier) : on ne garde que le
        # libellé, mais il doit rester OPAQUE (jeton) — sinon les pastilles
        # `code` qu'il contient sont ré-échappées à l'étape 3 et le PDF affiche
        # le balisage ReportLab en clair.
        if url.startswith("#") or not url.startswith("http"):
            return keep(md_to_rl(label))
        short = url.replace("https://", "").replace("http://", "")
        if len(short) > 54:
            short = short[:51] + "…"
        return keep(md_to_rl(label) +
                    f'<font size="6.6" color="#6E7781"> ({html.escape(short)})</font>')

    # 1. liens puis code -> jetons opaques
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)
    text = INLINE_CODE.sub(lambda m: keep(code_chip(m.group(1))), text)

    # 2. gras / italique / barré sur l'ensemble (les jetons sont des \x00n\x00)
    #    un ** peut être coupé par un saut de paragraphe : on tolère les \n
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text, flags=re.S)
    # italique : on tolère le retour à la ligne (les paragraphes Markdown sont
    # repliés sur plusieurs lignes), sinon les astérisques restent visibles.
    text = re.sub(r"(?<![\w*])\*([^*]+?)\*(?![\w*])", r"<i>\1</i>", text, flags=re.S)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text, flags=re.S)
    text = re.sub(r"~~(.+?)~~", r"<strike>\1</strike>", text, flags=re.S)

    # 3. échappement uniquement hors balises/jetons
    parts = re.split(f"{TAGS}|{TOKEN}", text)
    for i, part in enumerate(parts):
        if part is None or re.fullmatch(TAGS, part) or re.fullmatch(TOKEN, part):
            continue
        parts[i] = html.escape(part, quote=False)
    text = "".join(p for p in parts if p is not None)
    return re.sub(r"\x00(\d+)\x00", lambda m: hold[int(m.group(1))], text)


# --------------------------------------------------------------------------
# 5. Blocs de rendu
# --------------------------------------------------------------------------
def muted_rule(width: float = CONTENT_W, color=BORDER_MUTED, thickness=0.6,
               space_before=2, space_after=6) -> HRFlowable:
    return HRFlowable(width="100%", thickness=thickness, color=color,
                      spaceBefore=space_before, spaceAfter=space_after,
                      lineCap="round")


class SectionRule(Flowable):
    """Trait sous les titres H1/H2 (style github : 1 px, gris clair)."""

    def __init__(self, width=CONTENT_W, color=BORDER_MUTED, thickness=1.0):
        super().__init__()
        self.width_, self.color, self.thickness = width, color, thickness
        self.height = thickness + 5

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.height - 4, self.width_, self.height - 4)


class Badge(Flowable):
    """Petite étiquette arrondie (MUST, SHOULD, V1, R-01…)."""

    def __init__(self, text, fg=FG, bg=CANVAS_SUBTLE, border=BORDER, size=6.7,
                 pad_x=3.2, pad_y=1.3):
        super().__init__()
        self.text, self.fg, self.bg, self.border = text, fg, bg, border
        self.size, self.pad_x, self.pad_y = size, pad_x, pad_y
        self.width = pdfmetrics.stringWidth(text, "Inter-SemiBold", size) + 2 * pad_x
        self.height = size + 2 * pad_y + 0.8

    def draw(self):
        c = self.canv
        c.setFillColor(self.bg)
        c.setStrokeColor(self.border)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, self.width, self.height, 2.2, stroke=1, fill=1)
        c.setFillColor(self.fg)
        c.setFont("Inter-SemiBold", self.size)
        c.drawString(self.pad_x, self.pad_y + 0.6, self.text)


class Callout(Flowable):
    """Encadré d'appel (NOTE / IMPORTANT / WARNING…), style Alerts GitHub."""

    def __init__(self, blocks, accent=INFO, bg=INFO_SOFT):
        super().__init__()
        self.blocks, self.accent, self.bg = blocks, accent, bg
        self.inner_w = CONTENT_W - 18
        self._measure()

    def _measure(self):
        h = 0
        for b in self.blocks:
            w, bh = b.wrap(self.inner_w, PAGE_H)
            h += bh
            b._callout_h = bh
        self.height = h + 12

    def wrap(self, aw, ah):
        self.width = CONTENT_W
        return CONTENT_W, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(self.bg)
        c.roundRect(0, 0, CONTENT_W, self.height, 3.0, stroke=0, fill=1)
        c.setFillColor(self.accent)
        c.roundRect(0, 0, 3.0, self.height, 1.4, stroke=0, fill=1)
        y = self.height - 6
        for b in self.blocks:
            bh = getattr(b, "_callout_h", self.height)
            b.drawOn(c, 12, y - bh)
            y -= bh


def join_soft_wraps(paragraphs: list[str]) -> list[str]:
    """Recolle les lignes issues d'un retour à la ligne Markdown (paragraphe)."""
    joined: list[str] = []
    for chunk in paragraphs:
        if joined and not chunk.startswith(("-", "*", "|", "#")) and not chunk.startswith("**Document"):
            joined[-1] = joined[-1].rstrip() + " " + chunk
        else:
            joined.append(chunk)
    return [c for c in joined if c.strip()]


def make_callout(kind: str, paragraphs: list[str]) -> Callout:
    title, accent, bg = CALL_OUT.get(kind, CALL_OUT["NOTE"])
    blocks: list = [Paragraph(md_to_rl(title), S["callout_title"])]
    for p in join_soft_wraps(paragraphs):
        if p.strip():
            blocks.append(Paragraph(md_to_rl(p), S["blockquote"]))
    return Callout(blocks, accent=accent, bg=bg)


DIAGRAM_CHARS = set("│─┌┐└┘├┤┬┴┼═║╔╗╚╝▶▼▲◀→←↑↓")


MERMAID_EDGE = re.compile(
    r"^\s*([A-Za-z0-9_\[\]*]+)\s*-->\s*([A-Za-z0-9_\[\]*]+)\s*(?::\s*(.+))?$")


def parse_mermaid(text: str) -> list[tuple[str, str, str]]:
    edges = []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line or line.startswith(("stateDiagram", "%%", "classDef", "class ")):
            continue
        m = MERMAID_EDGE.match(line)
        if not m:
            continue
        src, dst, label = m.group(1), m.group(2), (m.group(3) or "").strip()
        fmt = lambda x: ("Départ" if x == "[*]" else x.replace("_", " ").title())
        if dst == "[*]":
            continue                     # les fins terminales sont implicites
        edges.append((fmt(src), fmt(dst), label))
    return edges


STATE_SRC = ParagraphStyle("state_src", fontName="Inter-SemiBold", fontSize=7.3,
                           leading=10.2, textColor=colors.HexColor("#3A4150"))
STATE_DST = ParagraphStyle("state_dst", fontName="Inter-SemiBold", fontSize=7.3,
                           leading=10.2, textColor=ACCENT_DARK)
STATE_WHY = ParagraphStyle("state_why", fontName="Inter", fontSize=7.3,
                           leading=10.2, textColor=FG_MUTED)


def transitions_panel(edges: list[tuple[str, str, str]]) -> Table | None:
    """Panneau « transitions » : état source fusionné, flèche, état cible, condition."""
    if not edges:
        return None
    ordered, seen = [], set()
    for src, _, _ in edges:
        if src not in seen:
            seen.add(src)
            ordered.append(src)

    rows, separators = [], []
    for src in ordered:
        group = [e for e in edges if e[0] == src]
        if rows:
            separators.append(len(rows))
        first = len(rows)
        for k, (_, dst, label) in enumerate(group):
            rows.append([
                Paragraph('<font color="#9A8BF0">●</font>&nbsp; ' + src, STATE_SRC) if k == 0 else "",
                Paragraph('<font color="#6C4DF6">→</font>', STATE_SRC),
                Paragraph(dst, STATE_DST),
                Paragraph(md_to_rl(label), STATE_WHY) if label else "",
            ])

    widths = [0.23 * CONTENT_W, 0.05 * CONTENT_W, 0.26 * CONTENT_W, 0.46 * CONTENT_W]
    t = Table(rows, colWidths=widths, hAlign="LEFT")
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
    ]
    for row in separators:
        style.append(("LINEABOVE", (0, row), (-1, row), 0.4,
                      colors.HexColor("#E7E2FB")))
    t.setStyle(TableStyle(style))
    return t


class Panel(Flowable):
    """Encadré d'un panneau (titre discret + contenu)."""

    def __init__(self, title: str, content: Flowable):
        super().__init__()
        self.title, self.content = title, content
        self._measure()

    def _measure(self):
        self.title_h = 12
        w, h = self.content.wrap(CONTENT_W - 20, PAGE_H)
        self.content_h = h
        self.width = CONTENT_W
        self.height = h + self.title_h + 14

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(colors.HexColor("#FBFAFF"))
        c.setStrokeColor(colors.HexColor("#E4DFFA"))
        c.setLineWidth(0.6)
        c.roundRect(0, 0, CONTENT_W, self.height, 3, stroke=1, fill=1)
        c.setFillColor(ACCENT_DARK)
        c.setFont("Inter-SemiBold", 6.8)
        c.drawString(10, self.height - 10.5, self.title.upper())
        self.content.drawOn(c, 10, self.height - self.title_h - self.content_h - 1)


def is_diagram(code: str) -> bool:
    lines = [ln for ln in code.split("\n") if ln.strip()]
    if not lines:
        return False
    hit = sum(1 for ln in lines if DIAGRAM_CHARS & set(ln))
    return hit / len(lines) > 0.5 and len(lines) < 40


def make_diagram(code: str) -> Table:
    """Schéma en caractères semi-graphiques (monospace conservé)."""
    style = fitted_code_style(code, base=6.9, floor=5.4, padding=20)
    style.textColor = colors.HexColor("#2B3440")
    cell = Preformatted(code.rstrip("\n"), style, maxLineLength=10_000)
    t = Table([[cell]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBFAFF")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#DED8FB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


MONO_RATIO = 0.602          # largeur d'un caractère JetBrains Mono / taille


def fitted_code_style(code: str, base: float = 7.2, floor: float = 6.2,
                      padding: float = 16) -> ParagraphStyle:
    """Réduit la police pour que la ligne la plus longue tienne dans la colonne."""
    longest = max((len(ln) for ln in code.split("\n")), default=40)
    size = min(base, (CONTENT_W - padding) / max(1, longest * MONO_RATIO))
    size = max(floor, round(size, 2))
    return ParagraphStyle("code_fit", fontName="JBMono", fontSize=size,
                          leading=size * 1.42, textColor=FG)


def make_code_block(code: str, max_lines: int = 82) -> Table:
    lines = code.rstrip("\n").split("\n")
    if len(lines) > max_lines:
        lines = lines[:max_lines] + ["…"]
    joined = "\n".join(lines)
    style = fitted_code_style(joined)
    cell = Preformatted(joined, style, maxLineLength=10_000)
    t = Table([[cell]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CANVAS_SUBTLE),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER_MUTED),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5.5),
    ]))
    return t


PILL_STYLES = {
    "MUST": (DONE, DONE_SOFT), "SHOULD": (INFO, INFO_SOFT),
    "COULD": (WARN, WARN_SOFT), "WON'T": (DANGER, DANGER_SOFT),
    "V1": (ACCENT_DARK, ACCENT_SOFT), "V1.1": (ACCENT_DARK, ACCENT_SOFT),
    "V2": (colors.HexColor("#5A4FCF"), ACCENT_SOFT), "Hors": (FG_MUTED, CANVAS_SUBTLE),
}


def pill_flowable(label: str):
    """Étiquette colorée pour une cellule de tableau (MUST, SHOULD, V1…)."""
    fg, bg = PILL_STYLES[label]
    size = 6.6
    width = pdfmetrics.stringWidth(label, "Inter-SemiBold", size) + 9
    par = Paragraph(label, ParagraphStyle(
        "pill", fontName="Inter-SemiBold", fontSize=size, leading=size + 2.2,
        textColor=fg, alignment=TA_CENTER))
    tag = Table([[par]], colWidths=[width])
    tag.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.4, bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1.1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.3),
    ]))
    tag.pill_width = width
    return tag


PILL_PREFIX = re.compile(r"^(V1\.1|V1|V2|Hors)\b\s*(.*)$", re.S)


def inline_pill(label: str) -> str:
    """Étiquette inline (pastille colorée) utilisable dans un paragraphe."""
    fg, bg = PILL_STYLES[label]
    return (f'<font name="Inter-SemiBold" size="6.6" color="{fg.hexval()}" '
            f'backColor="{bg.hexval()}">&nbsp;{label}&nbsp;</font>')


def cell_flowable(raw: str, style):
    key = raw.strip().strip("*")
    if key in PILL_STYLES:
        return pill_flowable(key)
    m = PILL_PREFIX.match(key)
    if m and len(key) <= 48:
        rest = m.group(2).strip(" ()")
        html_text = inline_pill(m.group(1))
        if rest:
            html_text += "&nbsp; " + md_to_rl(rest)
        return Paragraph(html_text, style)
    return Paragraph(md_to_rl(breakable(raw)), style)


def column_widths(rows: list[list[str]], ncols: int) -> list[float]:
    """Largeurs de colonnes : plancher = mot le plus long, idéal = poids du contenu.

    Algorithme : on part d'une répartition proportionnelle au contenu, puis on
    relève toute colonne dont la largeur est inférieure à son mot le plus long
    (jetons monospace compris) en prélevant le déficit sur les colonnes qui ont
    du mou. Deux passes suffisent en pratique.
    """
    pad = 11.0  # 2 x 5 pt de padding + marge de sécurité (cf. make_table)
    mins, weights = [], []
    for c in range(ncols):
        cells = [re.sub(r"[`*]", "", r[c]) for r in rows]
        longest = 0.0
        for cell in cells:
            for token in cell.split():
                # Le pire des deux cas : corps (Inter 7.6) et en-tête (SemiBold 7.4),
                # sinon « Authentification » déborde de sa cellule.
                w = max(pdfmetrics.stringWidth(token, "Inter", 7.6),
                        pdfmetrics.stringWidth(token, "Inter-SemiBold", 7.4))
                if re.search(r"[_/.]|^[A-Z0-9_-]{4,}$", token):
                    w = max(w, pdfmetrics.stringWidth(token, "JBMono", 7.9))
                longest = max(longest, w)
        # Plancher = mot le plus long + padding, mais plafonné : reportlab coupe
        # les jetons trop larges (chemins, identifiants) sur 2-3 lignes, inutile
        # de réserver 165 pt à `schemas/recurrence-rule.schema.json`.
        mins.append(min(longest + pad, CONTENT_W * 0.28))
        weights.append((sum(len(x) for x in cells) / max(1, len(cells))) + 10)

    total_min = sum(mins)
    if total_min >= CONTENT_W:
        scale = CONTENT_W / total_min
        return [m * scale for m in mins]

    free = CONTENT_W - total_min
    wsum = sum(weights)
    cols = [m + free * w / wsum for m, w in zip(mins, weights)]

    # deux passes de rééquilibrage
    for _ in range(2):
        deficit = sum(max(0.0, mins[i] - cols[i]) for i in range(ncols))
        if deficit <= 0.5:
            break
        for i in range(ncols):
            cols[i] = max(cols[i], mins[i])
        slack = [max(0.0, cols[i] - mins[i]) for i in range(ncols)]
        total_slack = sum(slack)
        if total_slack <= 0.5:
            break
        for i in range(ncols):
            cols[i] -= deficit * slack[i] / total_slack
    return [max(m, c) for m, c in zip(mins, cols)] if sum(cols) <= CONTENT_W else cols


def breakable(text: str) -> str:
    """Neutralise les artefacts de césure.

    Historiquement, cette fonction insérait des espaces de largeur nulle (U+200B)
    dans les jetons longs. JetBrains Mono ne possède pas ce glyphe : reportlab le
    remplaçait par un caractère de largeur ≈ 0,6 em, ce qui ajoutait un blanc
    parasite au milieu des identifiants (`packages/ recurrence`). Depuis que la
    largeur plancher des colonnes est plafonnée et que `splitLongWords` (actif par
    défaut) coupe les jetons trop larges, la césure manuelle n'est plus utile :
    on conserve donc le texte tel quel.
    """
    return text


def make_table(rows: list[list[str]], aligns: list[str] | None = None) -> Table:
    ncols = max(len(r) for r in rows)
    norm = [r + [""] * (ncols - len(r)) for r in rows]
    header, body = norm[0], norm[1:]
    widths = column_widths(norm, ncols)

    data = [[cell_flowable(cell, S["table_header"]) for cell in header]]
    for r in body:
        data.append([cell_flowable(cell, S["table"]) for cell in r])

    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), CANVAS_SUBTLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), FG),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, BORDER),
        ("LINEBELOW", (0, 1), (-1, -1), 0.35, BORDER_MUTED),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FBFCFD")))
    t.setStyle(TableStyle(style))
    return t


# --------------------------------------------------------------------------
# 6. Mini-parseur Markdown orienté document technique
# --------------------------------------------------------------------------
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET = re.compile(r"^(\s*)[-*+]\s+(.*)$")
ORDERED = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
HR = re.compile(r"^\s*(---|\*\*\*|___)\s*$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
FENCE = re.compile(r"^\s*```")


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells, buf, in_code = [], "", False
    for ch in line:
        if ch == "`":
            in_code = not in_code
            buf += ch
        elif ch == "|" and not in_code:
            cells.append(buf.strip())
            buf = ""
        else:
            buf += ch
    cells.append(buf.strip())
    return cells


def parse_markdown(text: str) -> list:
    """Retourne une liste de blocs intermédiaires."""
    lines = text.replace("\r\n", "\n").split("\n")
    blocks, i = [], 0
    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        if FENCE.match(line):
            lang = line.strip()[3:].strip().lower()
            i += 1
            code = []
            while i < len(lines) and not FENCE.match(lines[i]):
                code.append(lines[i])
                i += 1
            i += 1
            blocks.append(("code", "\n".join(code), lang))
            continue

        m = HEADING.match(line)
        if m:
            blocks.append(("h", len(m.group(1)), m.group(2).strip()))
            i += 1
            continue

        if line.lstrip().startswith(">"):
            quoted, meta = [], None
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                content = lines[i].lstrip()[1:].strip()
                if NOTE_RE.match(content):
                    meta = NOTE_RE.match(content).group(1)
                elif content:
                    quoted.append(content + (" " if content.endswith((",", ":", ";")) else ""))
                elif quoted and quoted[-1] != "":
                    quoted.append("")
                i += 1
            blocks.append(("callout", meta, quoted))
            continue

        if line.strip().startswith("|") and i + 1 < len(lines) and TABLE_SEP.match(lines[i + 1]):
            rows = [split_row(line)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            blocks.append(("table", rows))
            continue

        if HR.match(line):
            blocks.append(("hr",))
            i += 1
            continue

        if BULLET.match(line) or ORDERED.match(line):
            items = []
            while i < len(lines):
                cur = lines[i]
                mb, mo = BULLET.match(cur), ORDERED.match(cur)
                if mb:
                    indent = len(mb.group(1).replace("\t", "  "))
                    items.append((indent, "•", mb.group(2).strip()))
                elif mo:
                    indent = len(mo.group(1).replace("\t", "  "))
                    items.append((indent, mo.group(2) + ".", mo.group(3).strip()))
                elif cur.strip() and cur.startswith("  ") and items:
                    indent, marker, prev = items[-1]
                    items[-1] = (indent, marker, prev + " " + cur.strip())
                elif not cur.strip():
                    nxt = lines[i + 1] if i + 1 < len(lines) else ""
                    if BULLET.match(nxt) or ORDERED.match(nxt):
                        i += 1
                        continue
                    break
                else:
                    break
                i += 1
            blocks.append(("list", items))
            continue

        # paragraphe : accumulateur jusqu'à une ligne structurante
        para = [line.strip()]
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if (not nxt.strip() or HEADING.match(nxt) or FENCE.match(nxt)
                    or nxt.strip().startswith("|") or nxt.strip().startswith(">")
                    or BULLET.match(nxt) or ORDERED.match(nxt) or HR.match(nxt)):
                break
            para.append(nxt.strip())
            i += 1
        blocks.append(("p", " ".join(para)))
    return blocks


# --------------------------------------------------------------------------
# 7. Blocs -> flowables
# --------------------------------------------------------------------------
STRIP_META = re.compile(r"^\*\*Document\*\*\s*:.*$|^\*\*Date\*\*\s*:.*$")


def blocks_to_flowables(blocks: list, doc_key: str, doc_title: str,
                        first_h1_replaced: bool = True) -> list:
    flow: list = []
    lead_done = False
    for block in blocks:
        kind = block[0]

        if kind == "h":
            level, text = block[1], block[2]
            text = re.sub(r"[`*]", "", text)
            if level == 1:
                flow.append(Paragraph(md_to_rl(text), S["h1"]))
                flow.append(SectionRule())
                flow.append(Spacer(1, 3))
                flow[-2]._bookmark = (doc_key, text)
                flow[-2]._toc = (0, text)
            elif level == 2:
                flow.append(CondPageBreak(48))
                p = Paragraph(md_to_rl(text), S["h2"])
                p._bookmark = (doc_key, text)
                p._toc = (1, text)
                flow.append(p)
                flow.append(SectionRule(thickness=0.6))
            elif level in (3, 4):
                p = Paragraph(md_to_rl(text), S[f"h{level}"])
                if level == 3:
                    p._toc = (2, text)
                flow.append(p)
            else:
                flow.append(Paragraph(md_to_rl(text), S["h5"]))
            continue

        if kind == "p":
            raw = block[1]
            if STRIP_META.match(raw) and doc_key != "cover":
                flow.append(Paragraph(md_to_rl(raw), S["tiny"]))
                continue
            is_lead = (not lead_done and not flow and len(raw) > 90
                       and "|" not in raw)
            flow.append(Paragraph(md_to_rl(raw), S["lead"] if is_lead else S["body"]))
            lead_done = lead_done or is_lead
            continue

        if kind == "list":
            for indent, marker, text in block[1]:
                depth = min(3, indent // 2)
                color = "#6C4DF6" if marker == "•" else "#6E7781"
                size = "7.4" if marker == "•" else "8.6"
                st = ParagraphStyle(
                    f"li{depth}", parent=S["body_list"],
                    leftIndent=12 + depth * 12, firstLineIndent=-10,
                    spaceAfter=2.4 if depth else 3.0)
                flow.append(Paragraph(
                    f'<font color="{color}" size="{size}">{marker}</font>  ' + md_to_rl(text), st))
            flow.append(Spacer(1, 2.4))
            continue

        if kind == "code":
            flow.append(Spacer(1, 1.5))
            if len(block) > 2 and block[2] == "mermaid":
                edges = parse_mermaid(block[1])
                panel = transitions_panel(edges)
                if panel is not None:
                    flow.append(Panel("Transitions autorisées", panel))
                flow.append(Spacer(1, 6.5))
                continue
            if is_diagram(block[1]):
                flow.append(make_diagram(block[1]))
            else:
                flow.append(make_code_block(block[1]))
            flow.append(Spacer(1, 5.5))
            continue

        if kind == "table":
            rows = block[1]
            if len(rows) <= 1:
                continue
            flow.append(Spacer(1, 1.5))
            flow.append(make_table(rows))
            flow.append(Spacer(1, 6.5))
            continue

        if kind == "callout":
            meta, quoted = block[1], block[2]
            flow.append(Spacer(1, 3))
            flow.append(make_callout(meta or "NOTE", quoted))
            flow.append(Spacer(1, 7))
            continue

        if kind == "hr":
            flow.append(muted_rule(space_before=4, space_after=7))
            continue
    return flow


# --------------------------------------------------------------------------
# 8. Gabarits de page : couverture, sommaire, corps
# --------------------------------------------------------------------------
class Doc(BaseDocTemplate):
    def __init__(self, filename, doc_title: str, doc_key: str, **kw):
        self.doc_title = doc_title
        self.doc_key = doc_key
        super().__init__(filename, pagesize=A4, leftMargin=M_LEFT,
                         rightMargin=M_RIGHT, topMargin=M_TOP,
                         bottomMargin=M_BOTTOM, title=doc_title,
                         author="MyRDV — Direction produit",
                         subject="Cahier des charges MyRDV",
                         creator="build_pdf.py", **kw)
        frame = Frame(M_LEFT, M_BOTTOM, CONTENT_W,
                      PAGE_H - M_TOP - M_BOTTOM, id="body",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[Frame(M_LEFT, M_BOTTOM, CONTENT_W,
                                                  PAGE_H - M_TOP - M_BOTTOM,
                                                  leftPadding=0, rightPadding=0,
                                                  topPadding=0, bottomPadding=0)],
                         onPage=self.draw_cover),
            PageTemplate(id="body", frames=[frame], onPage=self.draw_decor),
        ])

    # --- couverture ---
    def draw_cover(self, c: canvas.Canvas, doc):
        c.saveState()
        # dégradé simulé par bandes
        top = colors.HexColor("#6C4DF6")
        for k in range(0, 26):
            ratio = k / 25
            col = colors.Color(
                top.red + (1 - top.red) * ratio,
                top.green + (1 - top.green) * ratio,
                top.blue + (1 - top.blue) * ratio)
            c.setFillColor(col)
            c.rect(0, PAGE_H - 6 * mm - k * 1.1 * mm, PAGE_W, 1.15 * mm, stroke=0, fill=1)
        # trame de points discrète
        c.setFillColor(colors.HexColor("#E9E4FF"))
        for x in range(int(M_LEFT), int(PAGE_W - M_LEFT), 9):
            for y in range(int(PAGE_H * 0.42), int(PAGE_H - 20 * mm), 9):
                c.circle(x, y, 0.22, stroke=0, fill=1)
        c.setFillColor(colors.HexColor("#F6F8FA"))
        c.rect(0, 0, PAGE_W, 12 * mm, stroke=0, fill=1)
        c.setFillColor(FG_MUTED)
        c.setFont("Inter", 7.4)
        c.drawString(M_LEFT, 7 * mm, "MyRDV · Cahier des charges · v1.0 · 12 novembre 2026")
        c.drawRightString(PAGE_W - M_RIGHT, 7 * mm, "Confidentiel — diffusion restreinte")
        c.restoreState()

    # --- pages de corps ---
    def draw_decor(self, c: canvas.Canvas, doc):
        c.saveState()
        c.setStrokeColor(BORDER_MUTED)
        c.setLineWidth(0.6)
        c.line(M_LEFT, PAGE_H - 13.4 * mm, PAGE_W - M_RIGHT, PAGE_H - 13.4 * mm)
        c.setFont("Inter-SemiBold", 7.3)
        c.setFillColor(ACCENT)
        c.drawString(M_LEFT, PAGE_H - 11.6 * mm, "MyRDV")
        c.setFont("Inter", 7.3)
        c.setFillColor(FG_MUTED)
        c.drawString(M_LEFT + 15 * mm, PAGE_H - 11.6 * mm, "· " + self.doc_title)
        c.drawRightString(PAGE_W - M_RIGHT, PAGE_H - 11.6 * mm, "Cahier des charges v1.0")
        c.line(M_LEFT, 12.6 * mm, PAGE_W - M_RIGHT, 12.6 * mm)
        c.setFont("Inter", 7.2)
        c.drawString(M_LEFT, 8.6 * mm, "12 novembre 2026 · Confidentiel")
        c.setFillColor(FG)
        c.setFont("Inter-SemiBold", 7.6)
        c.drawRightString(PAGE_W - M_RIGHT, 8.6 * mm, str(c.getPageNumber()))
        c.restoreState()

    # --- table des matières ---
    def afterFlowable(self, flowable):
        toc = getattr(flowable, "_toc", None)
        if toc:
            level, text = toc
            self.notify("TOCEntry", (level, text, self.page))
        bm = getattr(flowable, "_bookmark", None)
        if bm:
            key, text = bm
            safe = re.sub(r"[^A-Za-z0-9]+", "-", text)[:60].strip("-")
            self.canv.bookmarkPage(f"{key}-{self.page}-{safe}")
            self.canv.addOutlineEntry(text, f"{key}-{self.page}-{safe}",
                                      level=0, closed=False)


# --------------------------------------------------------------------------
# 9. Couverture + sommaire
# --------------------------------------------------------------------------
def cover_page(title: str, subtitle: str, kicker: str, meta_lines: list[str],
               stats: list[tuple[str, str]]) -> list:
    story: list = [Spacer(1, 30 * mm)]
    story.append(Paragraph(kicker, S["cover_kicker"]))
    story.append(Paragraph(title, S["cover_title"]))
    story.append(Paragraph(subtitle, S["cover_sub"]))
    story.append(Spacer(1, 2 * mm))
    story.append(HRFlowable(width="34%", thickness=2.4, color=ACCENT,
                            spaceBefore=0, spaceAfter=9, hAlign="LEFT"))
    story.append(Spacer(1, 2 * mm))

    if stats:
        cols = len(stats)
        col_w = [CONTENT_W / cols] * cols
        row_n = [Paragraph(number, S["cover_stat_n"]) for number, _ in stats]
        row_l = [Paragraph(label, S["cover_stat_l"]) for _, label in stats]
        t = Table([row_n, row_l], colWidths=col_w)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBFBFE")),
            ("BOX", (0, 0), (-1, -1), 0.7, BORDER_MUTED),
            ("LINEBEFORE", (1, 0), (-1, -1), 0.7, BORDER_MUTED),
            ("INNERGRID", (0, 0), (-1, -1), 0, colors.white),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
            ("TOPPADDING", (0, 1), (-1, 1), 1),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t)
        story.append(Spacer(1, 9 * mm))

    for line in meta_lines:
        story.append(Paragraph(md_to_rl(line), S["cover_meta"]))
    return story


def toc_page(title: str = "Sommaire") -> list:
    story = [Spacer(1, 4 * mm), Paragraph(title, S["h1"]), SectionRule(),
             Spacer(1, 4 * mm)]
    toc = TableOfContents()
    toc.levelStyles = [S["toc0"], S["toc1"], S["toc2"]]
    toc.dotsMinLevel = 1
    story.append(toc)
    return story, toc


def truncate_toc(toc_flowable: TableOfContents, first_page: int) -> None:
    """Supprime les entrées des documents suivants dans un extrait."""
    entries = toc_flowable._entries
    kept = []
    for entry in entries:
        level, text, page = entry[0], entry[1], entry[2]
        if level == 0 and page >= first_page:
            break
        kept.append(entry)
    toc_flowable._entries = kept


# --------------------------------------------------------------------------
# 10. Assemblage des documents
# --------------------------------------------------------------------------
DOCS = [
    ("00", "00-synthese-executive.md", "Synthèse exécutive"),
    ("01", "01-contexte-analyse-marche.md", "Contexte et analyse de marché"),
    ("02", "02-personas-utilisateurs.md", "Personas et parcours"),
    ("03", "03-exigences-fonctionnelles.md", "Exigences fonctionnelles"),
    ("04", "04-securite-conformite.md", "Sécurité et conformité"),
    ("05", "05-architecture-technique.md", "Architecture technique"),
    ("06", "06-moteur-rdv-recurrents.md", "Moteur de rendez-vous récurrents"),
    ("07", "07-api-et-schemas-rdv-recurrents.md", "API et schémas"),
    ("08", "08-exigences-non-fonctionnelles.md", "Exigences non fonctionnelles"),
    ("09", "09-plan-tests-recette.md", "Plan de tests et recette"),
    ("10", "10-roadmap-budget-risques.md", "Roadmap, budget et risques"),
    ("11", "11-api-regles-et-conformite.md", "Règles d'API et conformité"),
]


def load(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section_header(number: str, title: str, lead: str | None = None) -> list:
    kicker = Paragraph(f"Document {number}", S["cover_kicker"])
    kicker._toc = (0, f"{number} — {title}")
    kicker._bookmark = ("doc", f"{number} {title}")
    flow = [kicker,
            Paragraph(title, S["h1"]),
            SectionRule(thickness=2.0, color=ACCENT),
            Spacer(1, 1.5 * mm)]
    if lead:
        flow.append(Paragraph(lead, S["lead"]))
        flow.append(Spacer(1, 1.5 * mm))
    return flow


def strip_leading_h1(blocks: list) -> tuple[list, str | None]:
    """Retire le H1 d'ouverture (déjà rendu par l'en-tête de section)."""
    title = None
    out = []
    skipped = False
    for blk in blocks:
        if not skipped and blk[0] == "h" and blk[1] == 1:
            title = re.sub(r"[`*]", "", blk[2])
            skipped = True
            continue
        if not skipped and blk[0] == "p" and STRIP_META.match(blk[1]):
            continue
        out.append(blk)
    return out, title


def build_part(output: Path, title: str, subtitle: str, kicker: str,
               meta: list[str], stats: list[tuple[str, str]], sections: list[tuple[str, str, str]],
               toc_title: str = "Sommaire",
               toc_extract_from: int | None = None) -> Path:
    doc = Doc(str(output), title, doc_key=output.stem)
    story: list = []
    story += cover_page(title, subtitle, kicker, meta, stats)
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())
    toc_story, toc_flow = toc_page(toc_title)
    story += toc_story
    for number, relpath, label in sections:
        blocks, md_title = strip_leading_h1(parse_markdown(load(CHARGE / relpath)))
        story.append(PageBreak())
        story += section_header(number, label)
        story += blocks_to_flowables(blocks, doc_key=output.stem, doc_title=title)
        story.append(Spacer(1, 4 * mm))
    if toc_extract_from is not None:
        truncate_toc(toc_flow, toc_extract_from)
    doc.multiBuild(story)
    return output


def build_main(out_dir: Path) -> Path:
    sections = [(f"{n}", f"docs/{f}", label) for n, f, label in DOCS]
    sections += [
        ("A1", "annexes/tracabilite-gorendezvous.md",
         "Annexe — Traçabilité GOrendezvous"),
        ("A2", "annexes/glossaire.md", "Annexe — Glossaire"),
    ]
    return build_part(
        out_dir / "MyRDV-cahier-des-charges-complet-v1.0.pdf",
        "Cahier des charges",
        "Plateforme de prise de rendez-vous et de gestion d'agenda — spécification "
        "fonctionnelle, technique et normative",
        "CAHIER DES CHARGES · VERSION 1.0",
        ["**Produit** : MyRDV · **Référence** : GOrendezvous",
         "**Date** : 12 novembre 2026 · **Statut** : baseline soumise à revue",
         "**Diffusion** : comité exécutif, architecture, sécurité, juridique"],
        [("12", "documents"), ("195", "exigences fonctionnelles"),
         ("24", "règles de récurrence"), ("87", "exigences non fonctionnelles")],
        sections,
    )


def build_recurrence_only(out_dir: Path) -> Path:
    return build_part(
        out_dir / "MyRDV-moteur-rdv-recurrents-v1.0.pdf",
        "Moteur de rendez-vous récurrents",
        "Spécification normative : bornes de répétition, exceptions, conflits, "
        "fuseaux horaires et changement d'heure",
        "SPÉCIFICATION NORMATIVE · EXTRAIT DU CAHIER DES CHARGES",
        ["**Produit** : MyRDV · **Document** : 06",
         "**Date** : 12 novembre 2026 · **Statut** : normatif",
         "**Implémentation de référence** : tools/recurrence_simulator.py"],
        [("24", "règles R-01 à R-24"), ("4", "modes de fin"),
         ("26", "exemples chiffrés"), ("60", "cas de test")],
        [("06", "docs/06-moteur-rdv-recurrents.md", "Moteur de rendez-vous récurrents"),
         ("07", "docs/07-api-et-schemas-rdv-recurrents.md", "API et schémas")],
        toc_extract_from=99,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile le cahier des charges en PDF")
    parser.add_argument("--out", default=str(ROOT.parent.parent.parent / "pdf"),
                        help="répertoire de sortie (défaut : pdf/ à la racine du dépôt)")
    parser.add_argument("--only", default=None,
                        choices=["all", "06"],
                        help="construire tout ou seulement le module de récurrence")
    args = parser.parse_args()

    global S
    register_fonts()
    S = build_styles()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    produced = []
    if args.only in (None, "all"):
        produced.append(build_main(out_dir))
    if args.only in (None, "06"):
        produced.append(build_recurrence_only(out_dir))

    for p in produced:
        size = p.stat().st_size / 1024
        print(f"✔ {p}  ({size:.0f} Ko)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
