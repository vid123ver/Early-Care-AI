from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def _fmt_dt(value):
    if not value:
        return "N/A"
    if isinstance(value, str):
        try:
            # attempt ISO-like string
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d %b %Y, %I:%M %p")
        except Exception:
            return str(value)
    try:
        return value.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(value)


def build_health_report_pdf(user, report, overview, trends, diet=None, treatment=None):
    """Return PDF bytes for a structured, colorful health report.

    user: dict from g.current_user
    report: Mongo report document
    overview: dict from /dashboard/overview
    trends: dict from /dashboard/health_trends
    diet: optional dict (from /diet/recommend)
    treatment: optional dict (from /treatment/suggest)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="EarlyCare Health Report")

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SectionTitle", fontSize=14, leading=18, spaceAfter=6,
                              textColor=colors.HexColor("#1b6fbb"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="SubText", fontSize=9, leading=12, textColor=colors.HexColor("#6a8ca4")))

    story = []

    # Header
    story.append(Paragraph("EarlyCare Health Summary", styles["Title"]))
    story.append(Spacer(1, 6))
    patient_name = user.get("name") or user.get("email") or "Patient"
    story.append(Paragraph(f"Patient: <b>{patient_name}</b>", styles["Normal"]))
    created_at = report.get("created_at") if report else None
    story.append(Paragraph(f"Report generated: {_fmt_dt(datetime.utcnow())}", styles["SubText"]))
    story.append(Paragraph(f"Latest lab report: {_fmt_dt(created_at)}", styles["SubText"]))
    story.append(Spacer(1, 12))

    # 1. Lab findings & health score
    story.append(Paragraph("1. Lab findings & overall health", styles["SectionTitle"]))

    metrics = (report or {}).get("metrics") or {}
    metric_rows = [["Marker", "Value", "Comment"]]

    def _marker_comment(name, value):
        if value is None:
            return "—"
        if name == "glucose":
            if value >= 126:
                return "High – suggests diabetes range."
            if value >= 100:
                return "Borderline high – risk of diabetes is increasing."
            return "Within normal range."
        if name == "cholesterol":
            if value >= 240:
                return "High – heart risk is increased."
            if value >= 200:
                return "Borderline high – keep an eye on trends."
            return "Within target range."
        if name == "hemoglobin":
            if value < 11:
                return "Low – may suggest anemia."
            if value > 18:
                return "High – discuss with doctor."
            return "Within normal range."
        return "See doctor for clinical correlation."

    for key in sorted(metrics.keys()):
        value = metrics.get(key)
        if isinstance(value, (int, float)):
            metric_rows.append([key.capitalize(), f"{value}", _marker_comment(key, value)])

    t = Table(metric_rows, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3f0fc")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#234567")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e0eafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0eafc")),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    risk_level = (overview or {}).get("risk_level") or "N/A"
    health_score = (overview or {}).get("health_score") or 100
    story.append(Paragraph(
        f"Overall health score: <b>{health_score}/100</b> (risk level: <b>{risk_level}</b>)",
        styles["Normal"],
    ))

    comparison = (overview or {}).get("comparison") or {}
    deltas = comparison.get("deltas") or {}
    if deltas:
        bullet_lines = []
        for key, delta in deltas.items():
            if not isinstance(delta, (int, float)):
                continue
            arrow = "increasing" if delta > 0 else "decreasing" if delta < 0 else "unchanged"
            direction = "up" if delta > 0 else "down" if delta < 0 else "stable"
            bullet_lines.append(f"• {key.capitalize()} is {arrow} (trend: {direction}).")
        if bullet_lines:
            story.append(Spacer(1, 4))
            story.append(Paragraph(
                "<font color='#6a8ca4'>Trend note: "
                """"This report compares with your previous lab. Values marked as 
                "increasing" mean your risk is gradually going up, so early lifestyle changes matter.
                </font>""",
                styles["SubText"],
            ))
            for line in bullet_lines:
                story.append(Paragraph(line, styles["Normal"]))

    story.append(Spacer(1, 12))

    # 2. Diet recommendations (easy language)
    if diet:
        story.append(Paragraph("2. Daily diet guidance", styles["SectionTitle"]))
        story.append(Paragraph(
            "This is a simple, everyday food plan in easy language. "
            "Use it to remember what to eat more of and what to limit.",
            styles["SubText"],
        ))
        story.append(Spacer(1, 4))

        story.append(Paragraph("Eat more of (good for you):", styles["Normal"]))
        if diet.get("eat_more"):
            for item in diet["eat_more"]:
                story.append(Paragraph(f"• {item}", styles["Normal"]))

        story.append(Spacer(1, 6))
        story.append(Paragraph("Limit / avoid (may worsen your numbers):", styles["Normal"]))
        if diet.get("eat_less_or_avoid"):
            for item in diet["eat_less_or_avoid"]:
                story.append(Paragraph(f"• {item}", styles["Normal"]))

        sample = diet.get("sample_chart") or {}
        if sample:
            story.append(Spacer(1, 8))
            story.append(Paragraph("Example day plan (you can adjust portions):", styles["Normal"]))
            for meal, options in sample.items():
                story.append(Spacer(1, 3))
                story.append(Paragraph(meal.capitalize(), styles["SubText"]))
                for opt in options:
                    story.append(Paragraph(f"• {opt}", styles["Normal"]))

        if diet.get("notes"):
            story.append(Spacer(1, 6))
            story.append(Paragraph("Notes:", styles["SubText"]))
            for n in diet["notes"]:
                story.append(Paragraph(f"• {n}", styles["Normal"]))

        story.append(Spacer(1, 12))

    # 3. Medicines and home care (OTC guidance only)
    if treatment:
        story.append(Paragraph("3. Non-prescription medicines & home care", styles["SectionTitle"]))
        story.append(Paragraph(
            "These are over-the-counter (OTC) options and home remedies only. "
            "They do NOT replace your doctor&apos;s prescription.",
            styles["SubText"],
        ))
        story.append(Spacer(1, 4))

        for med in treatment.get("otc", []):
            story.append(Paragraph(f"• {med.get('name', 'Medicine')}", styles["Normal"]))
            uses = med.get("use_for") or []
            if uses:
                story.append(Paragraph(
                    f"  ")  # small indent via extra Paragraph
                )
                story.append(Paragraph(
                    f"  Use for: {', '.join(uses)}",
                    styles["SubText"],
                ))
            dose = med.get("adult_dose") or med.get("adult_max_per_day_mg")
            if dose:
                story.append(Paragraph(
                    f"  Dose/safety: {dose}",
                    styles["SubText"],
                ))
            for note in med.get("notes", []):
                story.append(Paragraph(f"  - {note}", styles["SubText"]))

        home = treatment.get("home_remedies") or []
        if home:
            story.append(Spacer(1, 6))
            story.append(Paragraph("Home remedies:", styles["Normal"]))
            for h in home:
                story.append(Paragraph(f"• {h}", styles["Normal"]))

        dosage_awareness = treatment.get("dosage_awareness") or []
        if dosage_awareness:
            story.append(Spacer(1, 6))
            story.append(Paragraph("Dosage awareness / safety:", styles["SubText"]))
            for d in dosage_awareness:
                story.append(Paragraph(f"• {d}", styles["Normal"]))

        alerts = treatment.get("consult_doctor_alerts") or []
        if alerts:
            story.append(Spacer(1, 6))
            story.append(Paragraph("When to urgently consult a doctor:", styles["SubText"]))
            for a in alerts:
                story.append(Paragraph(f"• {a}", styles["Normal"]))

        story.append(Spacer(1, 12))

    # 4. Final recommendations
    story.append(Paragraph("4. Simple next steps", styles["SectionTitle"]))
    bullets = []
    if risk_level == "High":
        bullets.append("Book an appointment with your doctor soon to discuss these results.")
    bullets.append("Repeat lab tests as advised by your clinician to track whether values are improving.")
    bullets.append(
        "Focus on consistent small changes (daily walking, home-cooked food, sleep) rather than quick fixes."
    )
    for b in bullets:
        story.append(Paragraph(f"• {b}", styles["Normal"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "This report is for education and discussion with your clinician. "
        "It is <b>not</b> a formal diagnosis or prescription.",
        styles["SubText"],
    ))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
