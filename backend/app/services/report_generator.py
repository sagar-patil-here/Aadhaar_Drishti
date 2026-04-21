"""
report_generator.py
-------------------
Generates a PDF investigation report for a red-flagged record.

The report is now designed to be *self-explanatory*: someone who has
never seen the codebase can open the PDF and understand:
  • what the record is,
  • why it was flagged,
  • what each risk signal actually means in plain language,
  • how serious it is and what to do next.

Uses ReportLab. Output saved to settings.REPORTS_DIR/{id}.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

from app.core.config import settings
from app.core.geography import is_border_state, is_low_population_territory


RED    = colors.HexColor("#C0392B")
AMBER  = colors.HexColor("#E67E22")
TEAL   = colors.HexColor("#1D8A6E")
DARK   = colors.HexColor("#1a1a2e")
LIGHT  = colors.HexColor("#F5F5F5")
NAVY   = colors.HexColor("#0F3057")


def _severity_color(severity: str) -> colors.Color:
    return {"HIGH": RED, "MEDIUM": AMBER, "LOW": TEAL}.get(severity, AMBER)


def generate(flag: Dict[str, Any], report_id: str) -> Path:
    """
    Parameters
    ----------
    flag      : red flag dict (from decision_logic.route)
    report_id : unique identifier for the report filename

    Returns
    -------
    Path to generated PDF
    """
    settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = settings.REPORTS_DIR / f"report_{report_id}.pdf"

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=f"Aadhaar DRISHTI Report {report_id}",
        author="Aadhaar DRISHTI",
    )

    styles = getSampleStyleSheet()
    sev        = flag.get("severity", "MEDIUM")
    sev_color  = _severity_color(sev)

    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"],
        textColor=DARK, fontSize=20, spaceAfter=4,
        alignment=TA_CENTER, leading=22,
    )
    sub_style = ParagraphStyle(
        "Sub", parent=styles["Normal"],
        textColor=colors.grey, fontSize=10,
        alignment=TA_CENTER, spaceAfter=14,
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"],
        textColor=NAVY, fontSize=13, spaceBefore=14, spaceAfter=6,
        leading=16,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, leading=15, alignment=TA_JUSTIFY,
    )
    note_style = ParagraphStyle(
        "Note", parent=styles["Normal"],
        fontSize=9, leading=13, textColor=colors.HexColor("#555"),
        alignment=TA_JUSTIFY,
    )

    story = []

    # ── Header ──────────────────────────────────────────
    story.append(Paragraph("AADHAAR DRISHTI", title_style))
    story.append(Paragraph(
        "Proactive Fraud Detection &mdash; Investigation Report", sub_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=sev_color))
    story.append(Spacer(1, 0.3*cm))

    # ── Severity badge ───────────────────────────────────
    badge_style = ParagraphStyle(
        "Badge", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=10, textColor=colors.white, alignment=TA_CENTER, leading=13,
    )
    badge_text = (
        f"SEVERITY: {sev}   |   "
        f"Anomaly Score: {flag.get('anomaly_score', 0):.4f}   |   "
        f"Report ID: {report_id}   |   "
        f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}"
    )
    severity_table = Table(
        [[Paragraph(badge_text, badge_style)]],
        colWidths=[17*cm],
    )
    severity_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), sev_color),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(severity_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Executive Summary (plain English) ────────────────
    story.append(Paragraph("Executive Summary", section_style))
    story.append(Paragraph(_executive_summary(flag), body_style))

    # Geographic context line — makes the report useful without
    # forcing the reader to already know which states are sensitive.
    geo_note = _geography_context(flag.get("state", ""))
    if geo_note:
        story.append(Spacer(1, 0.1*cm))
        story.append(Paragraph(geo_note, note_style))

    # ── Why was this flagged? ────────────────────────────
    story.append(Paragraph("Why Was This Record Flagged?", section_style))
    reason = flag.get("detection_reason") or _fallback_reason(flag)
    story.append(Paragraph(reason, body_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(_severity_explanation(sev), note_style))

    # ── Location ─────────────────────────────────────────
    story.append(Paragraph("Location Details", section_style))
    loc_data = [
        ["Field", "Value"],
        ["Date",     flag.get("date", "")],
        ["State",    flag.get("state", "")],
        ["District", flag.get("district", "")],
        ["Pincode",  str(flag.get("pincode", ""))],
    ]
    _add_table(story, loc_data, col_widths=[4.0*cm, 13.0*cm])

    # ── Enrollment counts ────────────────────────────────
    story.append(Paragraph("Enrollment Breakdown", section_style))
    story.append(Paragraph(
        "Raw counts for this (date, pincode). <b>Enrollment</b> = new "
        "Aadhaar registrations. <b>Bio Updates</b> = biometric re-captures "
        "(fingerprint/iris/photo). <b>Demo Updates</b> = demographic changes "
        "(name / address / phone). In a healthy pincode the three columns "
        "move together; large gaps are suspicious.",
        note_style,
    ))
    story.append(Spacer(1, 0.15*cm))
    enrol_data = [
        ["Age Group", "Enrollments", "Bio Updates", "Demo Updates"],
        ["0 – 5 yrs",  str(flag.get("age_0_5", 0)),        "—",                               "—"],
        ["5 – 17 yrs", str(flag.get("age_5_17", 0)),       str(flag.get("bio_age_5_17", 0)),  str(flag.get("demo_age_5_17", 0))],
        ["18+ yrs",    str(flag.get("age_18_greater", 0)), str(flag.get("bio_age_17_", 0)),   str(flag.get("demo_age_17_", 0))],
        ["Total",      str(flag.get("total_enrollments", 0)), "—",                            "—"],
    ]
    _add_table(story, enrol_data, col_widths=[4.25*cm, 4.25*cm, 4.25*cm, 4.25*cm])

    # ── Pie charts (visual distribution) ─────────────────
    age_pie_palette = [
        colors.HexColor("#3B82F6"),   # 0–5  — blue
        colors.HexColor("#F59E0B"),   # 5–17 — amber
        colors.HexColor("#10B981"),   # 18+  — emerald
    ]
    age_pie = _pie_chart(
        "Age Distribution",
        [
            ("0–5 yrs",  flag.get("age_0_5", 0)),
            ("5–17 yrs", flag.get("age_5_17", 0)),
            ("18+ yrs",  flag.get("age_18_greater", 0)),
        ],
        age_pie_palette,
    )

    bio_pie_palette = [
        colors.HexColor("#C0392B"),   # bio   — red
        colors.HexColor("#1D8A6E"),   # demo  — teal
    ]
    bio_demo_pie = _pie_chart(
        "Biometric vs Demographic Updates",
        [
            ("Bio updates",  flag.get("bio_age_5_17", 0) + flag.get("bio_age_17_", 0)),
            ("Demo updates", flag.get("demo_age_5_17", 0) + flag.get("demo_age_17_", 0)),
        ],
        bio_pie_palette,
    )

    # Lay the two charts side-by-side in a 2-column borderless table so
    # they always align correctly on the page and can't overflow the
    # 17 cm usable width.
    pie_row = Table(
        [[age_pie, bio_demo_pie]],
        colWidths=[8.5 * cm, 8.5 * cm],
        hAlign="LEFT",
    )
    pie_row.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(pie_row)
    story.append(Paragraph(
        "Left chart shows how the daily enrollments split across the "
        "three age buckets — a disproportionate 0–5 slice is the "
        "signature of Ghost Scanner. Right chart shows the balance "
        "between biometric and demographic updates — a heavy bias "
        "toward biometrics is the signature of the Laundering Detector.",
        note_style,
    ))
    story.append(Spacer(1, 0.2*cm))

    # ── Risk signals (with explanation column) ───────────
    story.append(Paragraph("Risk Signals &mdash; What Each Number Means", section_style))

    cell_style = ParagraphStyle(
        "Cell", parent=styles["Normal"], fontSize=9, leading=12,
        alignment=TA_LEFT, wordWrap="CJK",   # CJK wrap handles long words/ratios
    )
    header_cell_style = ParagraphStyle(
        "CellHead", parent=cell_style, fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    def P(text: str, header: bool = False) -> Paragraph:
        return Paragraph(str(text), header_cell_style if header else cell_style)

    risk_rows = [
        [
            P("Signal", header=True),
            P("Value", header=True),
            P("Assessment", header=True),
            P("Plain-English Meaning", header=True),
        ],
        [
            P("Ghost Child Ratio"),
            P(f"{flag.get('ghost_child_ratio', 0):.3f}"),
            P(_assess("ghost_child_ratio", flag)),
            P("Share of enrollments that are 0&ndash;5&nbsp;yr-olds. "
              "Healthy: 5&ndash;10%. &gt;55% suggests fabricated child "
              "entries for welfare subsidies."),
        ],
        [
            P("Bio/Demo Ratio (adult)"),
            P(f"{flag.get('bio_demo_ratio_17_', 0):.3f}"),
            P(_assess("bio_demo_ratio_17_", flag)),
            P("Adult biometric updates per demographic update. "
              "Healthy: ~1&times;. &gt;8&times; suggests identity "
              "laundering (same shell, new biometrics)."),
        ],
        [
            P("Bio/Demo Ratio (minor)"),
            P(f"{flag.get('bio_demo_ratio_5_17', 0):.3f}"),
            P(_assess("bio_demo_ratio_5_17", flag)),
            P("Same ratio for minors. Elevated values are especially "
              "serious &mdash; possible child-trafficking linkage."),
        ],
        [
            P("Enrollment Velocity"),
            P(f"{flag.get('enrollment_velocity', 0):.1f}"),
            P(_assess("enrollment_velocity", flag)),
            P("30-day rolling sum of enrollments in this district. "
              "Sudden spikes in border districts indicate coordinated "
              "migration."),
        ],
        [
            P("Migration Z-Score"),
            P(f"{flag.get('migration_zscore', 0):.3f}"),
            P(_assess("migration_zscore", flag)),
            P("How many standard deviations today's enrollments are "
              "above this district's own history. &gt;4 is statistically "
              "extreme."),
        ],
    ]
    # Column widths sum to 17cm — the usable A4 width with 2cm margins
    # on each side — so content never spills past the page edge.
    _add_table(
        story, risk_rows,
        col_widths=[3.8*cm, 1.8*cm, 2.4*cm, 9.0*cm],
        header_is_paragraph=True,
    )

    # ── Modules triggered ────────────────────────────────
    story.append(Paragraph("Detection Modules Triggered", section_style))
    modules_str = flag.get("modules_triggered", "isolation_forest_only") or "isolation_forest_only"
    module_items = [m.strip() for m in modules_str.split(",") if m.strip()]
    for m in module_items:
        label = m.replace("_", " ").title()
        desc  = _MODULE_DESCRIPTIONS.get(m, "")
        story.append(Paragraph(
            f"• <b>{label}</b> &mdash; {desc}",
            body_style,
        ))

    # ── Recommended action ───────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Recommended Action", section_style))
    story.append(Paragraph(_recommended_action(flag), body_style))

    # ── How to read this report ──────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("How to Read This Report", section_style))
    story.append(Paragraph(
        "Aadhaar DRISHTI combines a machine-learning anomaly detector "
        "(<b>Isolation Forest</b>, trained on 500,000 real enrollment rows) "
        "with three rule-based modules collectively called the <b>Tri-Shield</b>: "
        "<i>Ghost Scanner</i> (fake child enrollments), <i>Laundering Detector</i> "
        "(biometric cycling) and <i>Migration Radar</i> (coordinated surges). "
        "A record is flagged when the ML score falls below the threshold "
        f"({settings.ANOMALY_THRESHOLD}) <b>or</b> any Tri-Shield rule fires. "
        "Severity is HIGH when two or more signals align, MEDIUM when a single "
        "signal fires, LOW when the row is only a borderline statistical "
        "outlier.",
        note_style,
    ))

    # ── Footer ───────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Paragraph(
        "This report was generated automatically by Aadhaar DRISHTI. "
        "For official use only. Do not distribute.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER),
    ))

    doc.build(story)
    return out_path


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

_MODULE_DESCRIPTIONS = {
    "ghost_scanner":
        "detects fake child enrollments (0–5 yrs) used to claim "
        "welfare subsidies. Fires when the 0–5 share is abnormally "
        "high for the district.",
    "laundering_detector":
        "detects identity laundering. Fires when biometric updates "
        "surge while demographic data stays flat, i.e. someone is "
        "cycling biometrics on a static identity shell.",
    "migration_radar":
        "detects coordinated enrollment surges. Fires when a district's "
        "daily enrollments are 3+ standard deviations above its own "
        "30-day rolling average.",
    "isolation_forest_only":
        "the Isolation Forest ML model classified the full 15-feature "
        "signature of this record as an outlier, but no single rule "
        "crossed its hard threshold. The feature most responsible is "
        "named in the 'Why' section above.",
}


def _executive_summary(flag: Dict[str, Any]) -> str:
    sev       = flag.get("severity", "MEDIUM")
    state     = flag.get("state", "—")
    district  = flag.get("district", "—")
    pincode   = flag.get("pincode", "—")
    date      = flag.get("date", "—")
    total     = int(flag.get("total_enrollments", 0))
    modules   = [m for m in (flag.get("modules_triggered") or "").split(",") if m]

    if modules and modules != ["isolation_forest_only"]:
        trigger = ", ".join(m.replace("_", " ").title() for m in modules if m != "isolation_forest_only")
        trigger_line = f"The following detector(s) fired on this record: <b>{trigger}</b>."
    else:
        trigger_line = (
            "No single Tri-Shield rule crossed its hard threshold, but the "
            "Isolation Forest model flagged the combined feature pattern as "
            "statistically anomalous compared to the training corpus of "
            "500,000 real enrollment rows."
        )

    return (
        f"On <b>{date}</b>, pincode <b>{pincode}</b> in "
        f"<b>{district}, {state}</b> recorded <b>{total}</b> total "
        f"Aadhaar enrollments. Aadhaar DRISHTI has classified this "
        f"record as <b>{sev} severity</b>. {trigger_line} "
        f"The detailed reasoning and recommended next steps are provided "
        f"below."
    )


def _geography_context(state: str) -> str:
    """
    Produces a one-line geographic-risk annotation used in the
    executive-summary block. Returns empty string for neutral states.
    """
    if is_border_state(state):
        return (
            f"<b>Geographic context:</b> {state} is a land-border state. "
            f"Fraud patterns here warrant elevated scrutiny because these "
            f"corridors are historically associated with cross-border "
            f"document laundering and proxy enrollment."
        )
    if is_low_population_territory(state):
        return (
            f"<b>Geographic context:</b> {state} is a low-population "
            f"Union Territory. Statistical outliers from such regions are "
            f"far more likely to reflect sampling noise than coordinated "
            f"fraud and should be corroborated with field evidence before "
            f"escalation."
        )
    return ""


def _severity_explanation(sev: str) -> str:
    return {
        "HIGH":
            "HIGH severity means either the ML anomaly score is deeply "
            "negative OR two or more Tri-Shield rules fired simultaneously. "
            "Field verification should begin immediately.",
        "MEDIUM":
            "MEDIUM severity means one Tri-Shield rule fired OR the ML "
            "score is meaningfully below threshold. Schedule review "
            "within the current cycle.",
        "LOW":
            "LOW severity means the record is only a marginal statistical "
            "outlier. Include in routine audit sampling.",
    }.get(sev, "")


def _fallback_reason(flag: Dict[str, Any]) -> str:
    """Only used if `detection_reason` was not provided by the pipeline."""
    modules = (flag.get("modules_triggered") or "").split(",")
    reasons = []
    if "ghost_scanner" in modules:
        reasons.append(
            f"Ghost-child ratio of {flag.get('ghost_child_ratio', 0)*100:.1f}% "
            f"vs healthy 5–10% norm."
        )
    if "laundering_detector" in modules:
        reasons.append(
            f"Biometric-to-demographic ratio of "
            f"{max(flag.get('bio_demo_ratio_17_', 0), flag.get('bio_demo_ratio_5_17', 0)):.1f}× "
            f"vs healthy ~1× norm."
        )
    if "migration_radar" in modules:
        reasons.append(
            f"Migration z-score of {flag.get('migration_zscore', 0):.1f} "
            f"vs threshold 3.0."
        )
    if not reasons:
        return (
            f"The Isolation Forest ML model assigned an anomaly score of "
            f"{flag.get('anomaly_score', 0):.4f}, below the configured "
            f"threshold of {settings.ANOMALY_THRESHOLD}. No single rule "
            f"fired, but the combined feature signature is unusual."
        )
    return " ".join(reasons)


def _pie_chart(
    title: str,
    slices: List[Tuple[str, float]],
    palette: List[colors.Color],
    width: float = 7.5 * cm,
    height: float = 5.5 * cm,
) -> Drawing:
    """
    Build a compact donut-style pie chart with a side legend that fits
    neatly into a report column. Zero-value slices are automatically
    dropped so the chart never renders with invisible wedges.

    Parameters
    ----------
    title    : small caption rendered above the wedge
    slices   : list of (label, value) tuples
    palette  : list of ReportLab colours, one per non-zero slice
    """
    drawing = Drawing(width, height)

    # Filter out zero-value slices — ReportLab's Pie renders them as a
    # hairline on the edge which looks like a bug.
    filtered = [(lbl, float(val)) for lbl, val in slices if float(val) > 0]
    total = sum(v for _, v in filtered) or 1.0

    # Caption
    drawing.add(String(
        width / 2, height - 0.3 * cm, title,
        fontName="Helvetica-Bold", fontSize=9,
        fillColor=colors.HexColor("#1a1a2e"),
        textAnchor="middle",
    ))

    if not filtered:
        drawing.add(String(
            width / 2, height / 2, "(no data)",
            fontName="Helvetica", fontSize=8,
            fillColor=colors.grey, textAnchor="middle",
        ))
        return drawing

    pie = Pie()
    pie.x = 0.3 * cm
    pie.y = 0.5 * cm
    pie.width  = 3.6 * cm
    pie.height = 3.6 * cm
    pie.data = [v for _, v in filtered]
    # ReportLab's Pie rejects None-typed labels; empty strings keep the
    # wedges label-free so that the side Legend is the sole label source.
    pie.labels = [""] * len(filtered)
    pie.slices.strokeColor = colors.white
    pie.slices.strokeWidth = 0.8
    pie.sideLabels = 0
    pie.simpleLabels = 1
    for i, col in enumerate(palette[:len(filtered)]):
        pie.slices[i].fillColor = col
    drawing.add(pie)

    # Legend (right of pie) with "Label — value (percent%)" rows.
    legend = Legend()
    legend.x = 4.3 * cm
    legend.y = height - 1.5 * cm
    legend.alignment = "right"
    legend.boxAnchor  = "nw"
    legend.columnMaximum = 6
    legend.deltay = 11
    legend.fontName = "Helvetica"
    legend.fontSize = 8
    legend.strokeWidth = 0
    legend.dxTextSpace = 4
    legend.dy = 7
    legend.dx = 7
    legend.colorNamePairs = [
        (palette[i % len(palette)],
         f"{lbl}: {int(val) if val == int(val) else round(val, 2)} "
         f"({100 * val / total:.0f}%)")
        for i, (lbl, val) in enumerate(filtered)
    ]
    drawing.add(legend)

    return drawing


def _add_table(story, data, col_widths=None, header_is_paragraph: bool = False):
    """
    Render a styled table. When `header_is_paragraph=True` the caller
    has already supplied `Paragraph` objects for the header row (they
    carry their own colour/font), so we skip the plain-text header
    styling that would otherwise try to re-apply font colour to a
    Paragraph and cause rendering issues.
    """
    t = Table(data, hAlign="LEFT", colWidths=col_widths, repeatRows=1)
    style = [
        ("FONTSIZE",      (0, 0), (-1,-1),  9),
        ("ROWBACKGROUNDS",(0, 1), (-1,-1),  [colors.white, LIGHT]),
        ("GRID",          (0, 0), (-1,-1),  0.25, colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0, 0), (-1,-1),  5),
        ("BOTTOMPADDING", (0, 0), (-1,-1),  5),
        ("LEFTPADDING",   (0, 0), (-1,-1),  6),
        ("RIGHTPADDING",  (0, 0), (-1,-1),  6),
        ("VALIGN",        (0, 0), (-1,-1),  "TOP"),
        # Dark header background always — Paragraphs inherit their own
        # text colour so this remains safe for both plain-text and
        # Paragraph headers.
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#1a1a2e")),
    ]
    if not header_is_paragraph:
        style.extend([
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ])
    t.setStyle(TableStyle(style))
    story.append(t)
    story.append(Spacer(1, 0.2*cm))


def _assess(field: str, flag: dict) -> str:
    v = flag.get(field, 0) or 0
    thresholds = {
        "ghost_child_ratio":    (0.15, 0.40),
        "bio_demo_ratio_17_":   (3.0,  5.0),
        "bio_demo_ratio_5_17":  (3.0,  5.0),
        "migration_zscore":     (2.0,  3.0),
        "enrollment_velocity":  (500,  1000),
    }
    lo, hi = thresholds.get(field, (1, 2))
    v_abs = abs(v) if field == "migration_zscore" else v
    if v_abs >= hi:  return "HIGH RISK"
    if v_abs >= lo:  return "ELEVATED"
    return "Normal"


def _recommended_action(flag: dict) -> str:
    severity = flag.get("severity", "MEDIUM")
    modules  = flag.get("modules_triggered", "") or ""
    primary  = flag.get("primary_module") or ""
    state    = flag.get("state", "") or ""

    actions = []

    if is_border_state(state):
        actions.append(
            f"<b>Border-state escalation:</b> because {state} shares an "
            f"international land border, additionally loop in the SSB / "
            f"BSF area command and request the MHA border-district "
            f"enrollment audit team to cross-verify this record."
        )

    if severity == "HIGH":
        actions.append(
            "<b>Immediate field verification required.</b> Escalate to "
            "the District Registrar. Suspend new enrollments from this "
            "pincode pending investigation. Cross-reference with the "
            "civil registration database."
        )

    if "ghost_scanner" in modules or primary == "ghost_scanner":
        actions.append(
            "Conduct physical verification of the 0–5 yr-old enrollments "
            "at this pincode. Cross-reference with Anganwadi / ICDS "
            "birth records and hospital birth registers."
        )
    if "laundering_detector" in modules or primary == "laundering_detector":
        actions.append(
            "Audit biometric update logs for this district. Identify "
            "operator IDs with disproportionate update activity and pull "
            "CCTV footage for the update sessions."
        )
    if "migration_radar" in modules or primary == "migration_radar":
        actions.append(
            "Review enrollment-center activity in this district for the "
            "surge window. Check for coordinated multi-pincode patterns "
            "and cross-border movement records."
        )

    if not actions:
        actions.append(
            "Flag for routine review by the district enrollment officer "
            "within 7 days. No immediate operational action required."
        )

    return " ".join(actions)
