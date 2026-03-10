from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import os
from datetime import datetime

def generate_results_pdf(test_code, subject, results):
    """Admin uchun barcha natijalar PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.HexColor('#1a237e')
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#555555')
    )

    elements = []

    # Header
    elements.append(Paragraph(f"📊 TEST NATIJALARI", title_style))
    elements.append(Paragraph(
        f"Fan: {subject} | Test kodi: <b>{test_code}</b> | Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        subtitle_style
    ))

    # Table header
    table_data = [["#", "Ism Familiya", "Username", "To'g'ri", "Jami", "Foiz", "Baho"]]

    for i, row in enumerate(results, 1):
        full_name = row['full_name'] or "Noma'lum"
        username = f"@{row['username']}" if row['username'] else "-"
        score = row['score']
        total = row['total']
        pct = row['percentage']

        if pct >= 85:
            grade = "A'lo ⭐"
            grade_color = colors.HexColor('#1b5e20')
        elif pct >= 70:
            grade = "Yaxshi ✅"
            grade_color = colors.HexColor('#1565c0')
        elif pct >= 55:
            grade = "Qoniqarli 🔶"
            grade_color = colors.HexColor('#e65100')
        else:
            grade = "Qoniqarsiz ❌"
            grade_color = colors.red

        table_data.append([
            str(i),
            full_name[:25],
            username[:20],
            str(score),
            str(total),
            f"{pct:.1f}%",
            grade
        ])

    col_widths = [1*cm, 5.5*cm, 4*cm, 2*cm, 2*cm, 2.2*cm, 2.8*cm]

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (3, 1), (5, -1), 'CENTER'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.5*cm))

    # Summary
    if results:
        avg = sum(r['percentage'] for r in results) / len(results)
        max_score = max(r['percentage'] for r in results)
        summary_style = ParagraphStyle('summary', parent=styles['Normal'], fontSize=10, spaceAfter=4)
        elements.append(Paragraph(
            f"<b>Jami ishtirokchilar:</b> {len(results)} ta | "
            f"<b>O'rtacha ball:</b> {avg:.1f}% | "
            f"<b>Eng yuqori:</b> {max_score:.1f}%",
            summary_style
        ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_certificate(user_name, subject, score, total, percentage, test_code, rank=None):
    """O'quvchi uchun sertifikat PDF"""
    buffer = io.BytesIO()
    width, height = A4[1], A4[0]  # Landscape

    doc = SimpleDocTemplate(
        buffer,
        pagesize=(width, height),
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    styles = getSampleStyleSheet()

    if percentage >= 85:
        grade_text = "A'LO"
        border_color = colors.HexColor('#FFD700')
        grade_emoji = "🥇"
    elif percentage >= 70:
        grade_text = "YAXSHI"
        border_color = colors.HexColor('#C0C0C0')
        grade_emoji = "🥈"
    elif percentage >= 55:
        grade_text = "QONIQARLI"
        border_color = colors.HexColor('#CD7F32')
        grade_emoji = "🥉"
    else:
        grade_text = "QATNASHDI"
        border_color = colors.HexColor('#4CAF50')
        grade_emoji = "📜"

    elements = []

    # Decorative border table
    cert_data = [[
        Paragraph(
            f"""
            <para align="center">
            <font size="14" color="#888888">✦ ✦ ✦ MILLIY SERTIFIKAT TAYYORLOV MARKAZI ✦ ✦ ✦</font><br/><br/>
            <font size="28" color="#1a237e"><b>SERTIFIKAT</b></font><br/>
            <font size="11" color="#555555">Ushbu sertifikat</font><br/><br/>
            <font size="22" color="#b71c1c"><b>{user_name}</b></font><br/><br/>
            <font size="11" color="#333333">ga beriladi, chunki u</font><br/>
            <font size="13" color="#1a237e"><b>{subject}</b> fanidan test sinovini muvaffaqiyatli topshirdi</font><br/><br/>
            <font size="16" color="#2e7d32"><b>{score}/{total} ta to'g'ri javob — {percentage:.1f}%</b></font><br/>
            <font size="20">{grade_emoji} <b>{grade_text}</b> {grade_emoji}</font><br/><br/>
            <font size="10" color="#777777">Test kodi: {test_code} | Sana: {datetime.now().strftime('%d.%m.%Y')}</font><br/>
            {'<font size="10" color="#555555">Natija reytingi: ' + str(rank) + '-o\'rin</font>' if rank else ''}
            </para>
            """,
            styles['Normal']
        )
    ]]

    cert_table = Table(cert_data, colWidths=[width - 4*cm])
    cert_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 4, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0, colors.white),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAFAFA')),
        ('TOPPADDING', (0, 0), (-1, -1), 30),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 30),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
    ]))

    elements.append(cert_table)
    doc.build(elements)
    buffer.seek(0)
    return buffer
