from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
import io
from datetime import datetime

def generate_results_pdf(test_code, subject, results):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
        fontSize=18, alignment=TA_CENTER, spaceAfter=6,
        textColor=colors.HexColor('#1a237e'))
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
        fontSize=11, alignment=TA_CENTER, spaceAfter=20,
        textColor=colors.HexColor('#555555'))
    elements = []
    elements.append(Paragraph("TEST NATIJALARI", title_style))
    elements.append(Paragraph(
        f"Fan: {subject} | Kod: {test_code} | Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        subtitle_style))
    table_data = [["#", "Ism Familiya", "Username", "To'g'ri", "Jami", "Foiz", "Baho"]]
    for i, row in enumerate(results, 1):
        pct = row['percentage']
        grade = "A'lo" if pct >= 85 else "Yaxshi" if pct >= 70 else "Qoniqarli" if pct >= 55 else "Qoniqarsiz"
        table_data.append([
            str(i), (row['full_name'] or "Noma'lum")[:25],
            f"@{row['username']}" if row['username'] else "-",
            str(row['score']), str(row['total']),
            f"{pct:.1f}%", grade
        ])
    col_widths = [1*cm, 5.5*cm, 4*cm, 2*cm, 2*cm, 2.2*cm, 2.8*cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (0,1), (0,-1), 'CENTER'),
        ('ALIGN', (3,1), (5,-1), 'CENTER'),
    ]))
    elements.append(table)
    if results:
        avg = sum(r['percentage'] for r in results) / len(results)
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(
            f"Jami: {len(results)} ta | O'rtacha: {avg:.1f}% | Eng yuqori: {max(r['percentage'] for r in results):.1f}%",
            ParagraphStyle('s', parent=styles['Normal'], fontSize=10)))
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_certificate(user_name, subject, score, total, percentage, test_code, rank=None):
    buffer = io.BytesIO()
    width, height = A4[1], A4[0]
    doc = SimpleDocTemplate(buffer, pagesize=(width, height),
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    if percentage >= 85:
        grade_text, border_color, symbol = "A'LO", colors.HexColor('#FFD700'), "★"
    elif percentage >= 70:
        grade_text, border_color, symbol = "YAXSHI", colors.HexColor('#C0C0C0'), "✓"
    elif percentage >= 55:
        grade_text, border_color, symbol = "QONIQARLI", colors.HexColor('#CD7F32'), "◆"
    else:
        grade_text, border_color, symbol = "QATNASHDI", colors.HexColor('#4CAF50'), "●"
    rank_line = f"Natija reytingi: {rank}-o'rin" if rank else ""
    cert_data = [[Paragraph(
        f"""<para align="center">
        <font size="13" color="#888888">MILLIY SERTIFIKAT TAYYORLOV MARKAZI</font><br/><br/>
        <font size="30" color="#1a237e"><b>SERTIFIKAT</b></font><br/><br/>
        <font size="12" color="#555555">Ushbu sertifikat</font><br/><br/>
        <font size="24" color="#b71c1c"><b>{user_name}</b></font><br/><br/>
        <font size="12" color="#333333">ga beriladi, chunki u</font><br/>
        <font size="14" color="#1a237e"><b>{subject}</b> fanidan test sinovini topshirdi</font><br/><br/>
        <font size="18" color="#2e7d32"><b>{score}/{total} ta togri javob — {percentage:.1f}%</b></font><br/><br/>
        <font size="22"><b>{symbol} {grade_text} {symbol}</b></font><br/><br/>
        <font size="10" color="#777777">Test kodi: {test_code} | Sana: {datetime.now().strftime('%d.%m.%Y')}</font><br/>
        <font size="10" color="#555555">{rank_line}</font>
        </para>""", styles['Normal'])]]
    cert_table = Table(cert_data, colWidths=[width - 4*cm])
    cert_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 4, border_color),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FAFAFA')),
        ('TOPPADDING', (0,0), (-1,-1), 30),
        ('BOTTOMPADDING', (0,0), (-1,-1), 30),
        ('LEFTPADDING', (0,0), (-1,-1), 20),
        ('RIGHTPADDING', (0,0), (-1,-1), 20),
    ]))
    doc.build([cert_table])
    buffer.seek(0)
    return buffer
