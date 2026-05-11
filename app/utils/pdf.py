"""PDF generation helpers — single source of truth for budget PDFs."""
import io
from datetime import datetime


def build_budget_pdf(budget) -> bytes:
    """
    Build a budget PDF and return raw bytes.
    Called by both the download route and the send-email route,
    eliminating the duplicated code that existed before.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer,
        Table, TableStyle, HRFlowable
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm
    )
    story = []

    # ── Styles ──────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'title', fontSize=28, textColor=colors.HexColor('#1e293b'),
        spaceAfter=2, fontName='Helvetica-Bold'
    )
    sub_style = ParagraphStyle(
        'sub', fontSize=11, textColor=colors.HexColor('#64748b'), spaceAfter=4
    )
    note_style = ParagraphStyle(
        'note', fontSize=9, textColor=colors.HexColor('#64748b')
    )

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph("PRESUPUESTO", title_style))
    story.append(Paragraph(f"N° {budget.budget_number}", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#6366f1')))
    story.append(Spacer(1, 0.4 * cm))

    # ── Info grid ───────────────────────────────────────────────────────────
    info_data = [
        ['CLIENTE', '', 'DATOS DEL PRESUPUESTO', ''],
        [budget.client_name, '', f'Fecha: {budget.created_at.strftime("%d/%m/%Y")}', ''],
        [budget.client_email or '-', '', f'Estado: {budget.status.upper()}', ''],
        [budget.client_phone or '-', '', 'Válido por: 30 días', ''],
    ]
    info_table = Table(info_data, colWidths=[8 * cm, 1 * cm, 6 * cm, 2.5 * cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1e293b')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.6 * cm))

    # ── Items table ─────────────────────────────────────────────────────────
    rows = [['#', 'Descripción', 'Cant.', 'Precio Unit.', 'Subtotal']]
    for i, item in enumerate(budget.items, 1):
        rows.append([
            str(i),
            item.description,
            f"{item.quantity:g}",
            f"${item.unit_price:,.2f}",
            f"${item.subtotal:,.2f}",
        ])
    items_table = Table(rows, colWidths=[0.8 * cm, 9 * cm, 1.5 * cm, 3 * cm, 3 * cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Totals ──────────────────────────────────────────────────────────────
    totals_data = [['', 'Subtotal:', f"${budget.subtotal:,.2f}"]]
    if budget.discount > 0:
        totals_data.append(['', f'Descuento ({budget.discount:.0f}%):', f"-${budget.discount_amount:,.2f}"])
    if budget.tax > 0:
        totals_data.append(['', f'IVA ({budget.tax:.0f}%):', f"${budget.tax_amount:,.2f}"])
    totals_data.append(['', 'TOTAL:', f"${budget.total:,.2f}"])

    totals_table = Table(totals_data, colWidths=[10.8 * cm, 3.5 * cm, 3 * cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -2), 10),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 13),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#6366f1')),
        ('LINEABOVE', (1, -1), (-1, -1), 1.5, colors.HexColor('#6366f1')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(totals_table)

    # ── Notes ───────────────────────────────────────────────────────────────
    if budget.notes:
        story.append(Spacer(1, 0.6 * cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0')))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph('<b>Notas:</b>', note_style))
        story.append(Paragraph(budget.notes, note_style))

    doc.build(story)
    return buffer.getvalue()
