"""
report_generator.py
-------------------
Generates a PDF investigation report for a red-flagged record.
Uses ReportLab. Output saved to settings.REPORTS_DIR/{id}.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from app.core.config import settings


RED    = colors.HexColor("#C0392B")
AMBER  = colors.HexColor("#E67E22")
TEAL   = colors.HexColor("#1D8A6E")
DARK   = colors.HexColor("#1a1a2e")
LIGHT  = colors.HexColor("#F5F5F5")


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
    )

    styles = getSampleStyleSheet()
    sev_color = _severity_color(flag.get("severity", "MEDIUM"))

    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"],
        textColor=DARK, fontSize=18, spaceAfter=4,
        alignment=TA_CENTER,
    )
    sub_style = ParagraphStyle(
        "Sub", parent=styles["Normal"],
        textColor=colors.grey, fontSize=10,
        alignment=TA_CENTER, spaceAfter=16,
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"],
        textColor=DARK, fontSize=12, spaceBefore=14, spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, leading=15,
    )

    story = []

    # ── Header ──────────────────────────────────────────
    story.append(Paragraph("AADHAAR DRISHTI", title_style))
    story.append(Paragraph("Automated Investigation Report — Red Flag", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=sev_color))
    story.append(Spacer(1, 0.3*cm))

    # ── Severity badge ───────────────────────────────────
    severity_table = Table(
        [[f"SEVERITY: {flag.get('severity','N/A')}   |   Score: {flag.get('anomaly_score',0):.4f}   |   Generated: {datetime.now().strftime('%d %b %Y %H:%M')}"]],
        colWidths=["100%"],
    )
    severity_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), sev_color),
        ("TEXTCOLOR",  (0,0), (-1,-1), colors.white),
        ("FONTNAME",   (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 11),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(severity_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Location ─────────────────────────────────────────
    story.append(Paragraph("Location Details", section_style))
    loc_data = [
        ["Field", "Value"],
        ["Date",     flag.get("date", "")],
        ["State",    flag.get("state", "")],
        ["District", flag.get("district", "")],
        ["Pincode",  str(flag.get("pincode", ""))],
    ]
    _add_table(story, loc_data)

    # ── Enrollment counts ────────────────────────────────
    story.append(Paragraph("Enrollment Breakdown", section_style))
    enrol_data = [
        ["Age Group", "Enrollment", "Bio Updates", "Demo Updates"],
        ["0–5 yrs",  str(flag.get("age_0_5", 0)),    str(flag.get("bio_age_5_17", 0)), str(flag.get("demo_age_5_17", 0))],
        ["5–17 yrs", str(flag.get("age_5_17", 0)),   "—", "—"],
        ["18+ yrs",  str(flag.get("age_18_greater", 0)), str(flag.get("bio_age_17_", 0)), str(flag.get("demo_age_17_", 0))],
        ["Total",    str(flag.get("total_enrollments", 0)), "—", "—"],
    ]
    _add_table(story, enrol_data)

    # ── Risk signals ─────────────────────────────────────
    story.append(Paragraph("Risk Signals", section_style))
    risk_data = [
        ["Signal", "Value", "Assessment"],
        ["Ghost Child Ratio",      f"{flag.get('ghost_child_ratio',0):.3f}",    _assess("ghost_child_ratio", flag)],
        ["Bio/Demo Ratio (adult)", f"{flag.get('bio_demo_ratio_17_',0):.3f}",   _assess("bio_demo_ratio_17_", flag)],
        ["Bio/Demo Ratio (minor)", f"{flag.get('bio_demo_ratio_5_17',0):.3f}",  _assess("bio_demo_ratio_5_17", flag)],
        ["Enrollment Velocity",    f"{flag.get('enrollment_velocity',0):.1f}",  _assess("enrollment_velocity", flag)],
        ["Migration Z-Score",      f"{flag.get('migration_zscore',0):.3f}",     _assess("migration_zscore", flag)],
    ]
    _add_table(story, risk_data)

    # ── Modules triggered ────────────────────────────────
    story.append(Paragraph("Detection Modules Triggered", section_style))
    modules_str = flag.get("modules_triggered", "isolation_forest_only")
    for m in modules_str.split(","):
        story.append(Paragraph(f"• {m.replace('_', ' ').title()}", body_style))

    # ── Recommended action ───────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Recommended Action", section_style))
    action = _recommended_action(flag)
    story.append(Paragraph(action, body_style))

    # ── Footer ───────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Paragraph(
        "This report was generated automatically by Aadhaar DRISHTI. "
        "For official use only. Do not distribute.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    return out_path


def _add_table(story, data):
    t = Table(data, hAlign="LEFT", colWidths=None)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1,-1),  9),
        ("ROWBACKGROUNDS",(0, 1), (-1,-1),  [colors.white, LIGHT]),
        ("GRID",          (0, 0), (-1,-1),  0.25, colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0, 0), (-1,-1),  5),
        ("BOTTOMPADDING", (0, 0), (-1,-1),  5),
        ("LEFTPADDING",   (0, 0), (-1,-1),  8),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2*cm))


def _assess(field: str, flag: dict) -> str:
    v = flag.get(field, 0)
    thresholds = {
        "ghost_child_ratio":  (0.15, 0.40),
        "bio_demo_ratio_17_": (3.0,  5.0),
        "bio_demo_ratio_5_17":(3.0,  5.0),
        "migration_zscore":   (2.0,  3.0),
        "enrollment_velocity":(500, 1000),
    }
    lo, hi = thresholds.get(field, (1, 2))
    if v >= hi:  return "HIGH RISK"
    if v >= lo:  return "ELEVATED"
    return "Normal"


def _recommended_action(flag: dict) -> str:
    severity = flag.get("severity", "MEDIUM")
    modules  = flag.get("modules_triggered", "")
    if severity == "HIGH":
        return (
            "Immediate field verification required. Escalate to District Registrar. "
            "Suspend new enrollments from this pincode pending investigation. "
            "Cross-reference with civil registration database."
        )
    if "ghost_scanner" in modules:
        return (
            "Conduct physical verification of age_0_5 enrollments at this pincode. "
            "Cross-reference with Anganwadi / ICDS birth records."
        )
    if "laundering_detector" in modules:
        return (
            "Audit biometric update logs for this district. "
            "Identify operator IDs with disproportionate update activity."
        )
    if "migration_radar" in modules:
        return (
            "Review enrollment center activity in this district. "
            "Check for coordinated multi-pincode enrollment surge patterns."
        )
    return "Flag for routine review by district enrollment officer within 7 days."
