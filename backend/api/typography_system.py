"""
=============================================================================
StudyAI — Central Typography, Layout & Styling System (Phase 6)
=============================================================================
Single source of truth for document design, typography, spacing, and page layout.
Used across Word (DOCX), PDF (ReportLab), and Markdown generation to guarantee
zero styling discrepancies and academic textbook visual standards.
=============================================================================
"""

import os
from typing import Dict, Any, Tuple
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors


class DocumentTypography:
    """
    Centralized design tokens and typography rules conforming to Phase 6 Section 6.
    """
    # Primary Font Family
    FONT_FAMILY = "Arial"
    FONT_FALLBACK = "Helvetica"
    FONT_CODE = "Courier"

    # Font Sizes (in Points)
    SIZE_DOC_TITLE = 26.0
    SIZE_SUBTITLE = 9.5
    SIZE_MODULE_CHAPTER = 20.0
    SIZE_MAIN_HEADING = 16.0
    SIZE_SUBHEADING = 13.5
    SIZE_TOPIC_HEADING = 11.5
    SIZE_BODY_TEXT = 10.5
    SIZE_BULLET_TEXT = 10.5
    SIZE_TABLE_HEADER = 9.5
    SIZE_TABLE_BODY = 8.5
    SIZE_CAPTION = 9.0
    SIZE_HEADER_FOOTER = 8.5
    SIZE_EQUATION = 9.5

    # Leading / Line Heights (in Points)
    LEADING_DOC_TITLE = 30.0
    LEADING_SUBTITLE = 13.0
    LEADING_MODULE_CHAPTER = 24.0
    LEADING_MAIN_HEADING = 20.0
    LEADING_SUBHEADING = 17.0
    LEADING_TOPIC_HEADING = 15.0
    LEADING_BODY_TEXT = 14.0
    LEADING_BULLET_TEXT = 14.0
    LEADING_TABLE_HEADER = 11.5
    LEADING_TABLE_BODY = 11.0
    LEADING_EQUATION = 13.0

    # Paragraph & Heading Spacing (in Points)
    LINE_SPACING_FACTOR = 1.2
    SPACE_BEFORE_TITLE = 0.0
    SPACE_AFTER_TITLE = 4.0
    SPACE_AFTER_SUBTITLE = 16.0
    SPACE_BEFORE_CHAPTER = 18.0
    SPACE_AFTER_CHAPTER = 6.0
    SPACE_BEFORE_MAIN_HEADING = 14.0
    SPACE_AFTER_MAIN_HEADING = 4.0
    SPACE_BEFORE_SUBHEADING = 10.0
    SPACE_AFTER_SUBHEADING = 3.0
    SPACE_BEFORE_TOPIC = 8.0
    SPACE_AFTER_TOPIC = 2.0
    SPACE_BEFORE_BODY = 0.0
    SPACE_AFTER_BODY = 6.0
    SPACE_AFTER_LIST_ITEM = 3.0

    # List Indentation (in Points & Inches)
    LIST_LEFT_INDENT_PT = 20.0
    LIST_FIRST_LINE_INDENT_PT = -12.0
    LIST_LEFT_INDENT_IN = 0.30
    LIST_FIRST_LINE_INDENT_IN = -0.15

    # Standard A4 Dimensions
    # A4: 210 x 297 mm = 595.28 x 841.89 points
    A4_WIDTH_PT = 595.28
    A4_HEIGHT_PT = 841.89
    A4_WIDTH_IN = 8.27
    A4_HEIGHT_IN = 11.69

    # Margins
    PDF_MARGIN_PT = 54.0   # 0.75 in balanced academic margins
    PRINTABLE_WIDTH_PT = 487.28
    DOCX_MARGIN_IN = 1.0   # 1.0 inch standard Word margins
    DOCX_PRINTABLE_WIDTH_IN = 6.27

    # Running Canvas Coordinates (A4)
    CANVAS_HEADER_Y = 808.0
    CANVAS_HEADER_LINE_Y = 800.0
    CANVAS_FOOTER_Y = 28.0
    CANVAS_FOOTER_LINE_Y = 38.0
    CANVAS_X_START = 54.0
    CANVAS_X_END = 541.28

    # Color Palette (Hex)
    HEX_PRIMARY_DARK = "#0F172A"       # Deep slate for titles
    HEX_HEADING_CHAPTER = "#1E293B"    # Slate 800 for chapters
    HEX_HEADING_MAIN = "#4338CA"       # Indigo 700 for main sections
    HEX_HEADING_SUB = "#334155"        # Slate 700 for subsections
    HEX_HEADING_TOPIC = "#475569"      # Slate 600 for topic headings
    HEX_BODY_TEXT = "#334155"          # Slate 700 for readable paragraphs
    HEX_MUTED = "#64748B"              # Slate 500 for captions and subtitles
    HEX_BORDER_LIGHT = "#CBD5E1"       # Slate 300 for table grid & callout borders
    HEX_DIVIDER = "#E2E8F0"            # Slate 200 for horizontal rules & canvas lines
    HEX_TABLE_HEADER_BG = "#1E293B"    # Navy for table header rows
    HEX_TABLE_ROW_ALT = "#F8FAFC"      # Subtle slate tint for alternating rows
    HEX_MATH_BOX_BG = "#F8FAFC"        # Formula callout background

    # Semantic Academic Callout Types
    CALLOUT_CONFIG = {
        "DEFINITION": {
            "label": "Definition: ",
            "border_hex": "#4F46E5",
            "fill_hex": "#EEF2FF",
            "text_color_hex": "#1E293B",
            "badge_bg_hex": "#E0E7FF",
            "badge_text_hex": "#3730A3"
        },
        "EXAMPLE": {
            "label": "Example: ",
            "border_hex": "#64748B",
            "fill_hex": "#F8FAFC",
            "text_color_hex": "#1E293B",
            "badge_bg_hex": "#F1F5F9",
            "badge_text_hex": "#334155"
        },
        "IMPORTANT": {
            "label": "Important: ",
            "border_hex": "#F59E0B",
            "fill_hex": "#FFFBEB",
            "text_color_hex": "#1E293B",
            "badge_bg_hex": "#FEF3C7",
            "badge_text_hex": "#92400E"
        },
        "FORMULA": {
            "label": "Formula: ",
            "border_hex": "#7C3AED",
            "fill_hex": "#FAF5FF",
            "text_color_hex": "#1E293B",
            "badge_bg_hex": "#F3E8FF",
            "badge_text_hex": "#6B21A8"
        },
        "EXAM_TIP": {
            "label": "Exam Tip: ",
            "border_hex": "#10B981",
            "fill_hex": "#F0FDF4",
            "text_color_hex": "#1E293B",
            "badge_bg_hex": "#D1FAE5",
            "badge_text_hex": "#065F46"
        },
        "NOTE": {
            "label": "Note: ",
            "border_hex": "#6366F1",
            "fill_hex": "#EEF2FF",
            "text_color_hex": "#1E293B",
            "badge_bg_hex": "#E0E7FF",
            "badge_text_hex": "#3730A3"
        }
    }

    # =========================================================================
    # Phase 8: Central Style Token System (Semantic Typography Tokens)
    # =========================================================================
    SEMANTIC_STYLE_TOKENS = {
        "DOCUMENT_TITLE": {
            "font_size": 24.0,
            "leading": 28.0,
            "font_weight": "bold",
            "color_hex": HEX_PRIMARY_DARK,
            "space_before": 0.0,
            "space_after": 6.0,
            "keep_with_next": True,
            "alignment": "center"
        },
        "MODULE_TITLE": {
            "font_size": 18.0,
            "leading": 22.0,
            "font_weight": "bold",
            "color_hex": HEX_HEADING_CHAPTER,
            "space_before": 18.0,
            "space_after": 6.0,
            "keep_with_next": True,
            "alignment": "left"
        },
        "H1": {
            "font_size": 16.0,
            "leading": 20.0,
            "font_weight": "bold",
            "color_hex": HEX_HEADING_MAIN,
            "space_before": 16.0,
            "space_after": 5.0,
            "keep_with_next": True,
            "alignment": "left"
        },
        "H2": {
            "font_size": 13.5,
            "leading": 17.0,
            "font_weight": "bold",
            "color_hex": HEX_HEADING_SUB,
            "space_before": 12.0,
            "space_after": 4.0,
            "keep_with_next": True,
            "alignment": "left"
        },
        "H3": {
            "font_size": 11.5,
            "leading": 15.0,
            "font_weight": "bold",
            "color_hex": HEX_HEADING_TOPIC,
            "space_before": 8.0,
            "space_after": 3.0,
            "keep_with_next": True,
            "alignment": "left"
        },
        "BODY": {
            "font_size": 10.0,
            "leading": 14.0,
            "font_weight": "normal",
            "color_hex": HEX_BODY_TEXT,
            "space_before": 0.0,
            "space_after": 6.0,
            "line_spacing": 1.2,
            "alignment": "left"
        },
        "BODY_COMPACT": {
            "font_size": 9.0,
            "leading": 12.5,
            "font_weight": "normal",
            "color_hex": HEX_BODY_TEXT,
            "space_before": 0.0,
            "space_after": 3.0,
            "alignment": "left"
        },
        "DEFINITION": {
            "font_size": 10.0,
            "leading": 14.0,
            "font_weight": "normal",
            "color_hex": HEX_BODY_TEXT,
            "fill_color_hex": "#EEF2FF",
            "border_color_hex": "#4F46E5",
            "border_thickness": 1.0,
            "left_indent": 12.0,
            "space_before": 4.0,
            "space_after": 6.0
        },
        "EXAMPLE": {
            "font_size": 9.5,
            "leading": 13.5,
            "font_weight": "normal",
            "color_hex": HEX_BODY_TEXT,
            "fill_color_hex": "#F8FAFC",
            "border_color_hex": "#64748B",
            "border_thickness": 1.0,
            "left_indent": 12.0,
            "space_before": 4.0,
            "space_after": 6.0
        },
        "NOTE": {
            "font_size": 9.5,
            "leading": 13.5,
            "font_weight": "normal",
            "color_hex": HEX_BODY_TEXT,
            "fill_color_hex": "#EEF2FF",
            "border_color_hex": "#6366F1",
            "border_thickness": 1.0,
            "left_indent": 12.0,
            "space_before": 4.0,
            "space_after": 6.0
        },
        "FORMULA": {
            "font_size": 10.0,
            "leading": 13.5,
            "font_weight": "normal",
            "color_hex": HEX_PRIMARY_DARK,
            "fill_color_hex": "#F8FAFC",
            "border_color_hex": "#CBD5E1",
            "border_thickness": 0.75,
            "left_indent": 18.0,
            "space_before": 6.0,
            "space_after": 6.0,
            "alignment": "center"
        },
        "NUMERICAL_STEP": {
            "font_size": 9.5,
            "leading": 13.5,
            "font_weight": "normal",
            "color_hex": HEX_BODY_TEXT,
            "left_indent": 20.0,
            "first_line_indent": -12.0,
            "space_before": 2.0,
            "space_after": 3.0
        },
        "TABLE_HEADER": {
            "font_size": 9.0,
            "leading": 11.5,
            "font_weight": "bold",
            "color_hex": "#FFFFFF",
            "fill_color_hex": HEX_TABLE_HEADER_BG,
            "cell_padding": 4.0
        },
        "TABLE_BODY": {
            "font_size": 8.5,
            "leading": 11.0,
            "font_weight": "normal",
            "color_hex": HEX_BODY_TEXT,
            "cell_padding": 3.5
        },
        "CAPTION": {
            "font_size": 8.5,
            "leading": 11.0,
            "font_weight": "italic",
            "color_hex": HEX_MUTED,
            "space_before": 3.0,
            "space_after": 6.0,
            "alignment": "center"
        },
        "HEADER": {
            "font_size": 8.5,
            "leading": 10.5,
            "font_weight": "normal",
            "color_hex": HEX_MUTED
        },
        "FOOTER": {
            "font_size": 8.5,
            "leading": 10.5,
            "font_weight": "normal",
            "color_hex": HEX_MUTED
        }
    }

    @classmethod
    def get_semantic_style(cls, token_name: str) -> Dict[str, Any]:
        """Returns the centralized token dictionary for a semantic style."""
        norm_key = token_name.upper().strip()
        if norm_key in cls.SEMANTIC_STYLE_TOKENS:
            return dict(cls.SEMANTIC_STYLE_TOKENS[norm_key])
        return dict(cls.SEMANTIC_STYLE_TOKENS["BODY"])

    @classmethod
    def get_registered_fonts(cls) -> Tuple[str, str, str, str]:
        """
        Registers Arial TrueType fonts into ReportLab if available;
        falls back cleanly to standard Helvetica fonts.
        Returns: (regular_font, bold_font, italic_font, bold_italic_font)
        """
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            if os.path.exists('C:/Windows/Fonts/arial.ttf'):
                pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
                pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
                pdfmetrics.registerFont(TTFont('Arial-Italic', 'C:/Windows/Fonts/ariali.ttf'))
                pdfmetrics.registerFont(TTFont('Arial-BoldItalic', 'C:/Windows/Fonts/arialbi.ttf'))
                return ('Arial', 'Arial-Bold', 'Arial-Italic', 'Arial-BoldItalic')
        except Exception:
            pass

        return ('Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique', 'Helvetica-BoldOblique')
