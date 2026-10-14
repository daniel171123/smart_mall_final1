from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.http import HttpResponse
from django.utils import timezone
import io


def generate_receipt_pdf(payment):
    """
    WHY: Generates a professional, legal-looking
    payment receipt PDF that includes:
    - Mall name and contact info
    - Receipt number and date
    - Tenant and lease details
    - Full payment breakdown
    - Verification stamp
    """
    buffer   = io.BytesIO()
    doc      = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    invoice  = payment.invoice
    lease    = invoice.lease
    tenant   = lease.tenant
    shop     = lease.shop
    mall     = shop.mall
    styles   = getSampleStyleSheet()
    elements = []

    # ── Color Palette ──────────────────────────────
    primary = colors.HexColor('#1a3c5e')
    accent  = colors.HexColor('#f0a500')
    light   = colors.HexColor('#f8f9fa')
    white   = colors.white
    green   = colors.HexColor('#28a745')

    # ── Custom Styles ──────────────────────────────
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontSize=22,
        textColor=white,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#a0c0e0'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#6c757d'),
        fontName='Helvetica'
    )
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#212529'),
        fontName='Helvetica-Bold'
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Normal'],
        fontSize=11,
        textColor=primary,
        fontName='Helvetica-Bold',
        spaceAfter=4
    )

    # ── HEADER BANNER ─────────────────────────────
    header_data = [[
        Paragraph(mall.name.upper(), title_style),
    ]]
    header_table = Table(header_data, colWidths=[170*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), primary),
        ('TOPPADDING',    (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('RIGHTPADDING',  (0,0), (-1,-1), 10),
        ('ROUNDEDCORNERS', [5]),
    ]))
    elements.append(header_table)

    sub_data = [[
        Paragraph(
            f'{mall.location}  |  {mall.contact_phone}'
            f'  |  {mall.contact_email}',
            subtitle_style
        )
    ]]
    sub_table = Table(sub_data, colWidths=[170*mm])
    sub_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), primary),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
    ]))
    elements.append(sub_table)
    elements.append(Spacer(1, 6*mm))

    # ── RECEIPT TITLE + NUMBER ─────────────────────
    receipt_no = f'RCP-{payment.pk:06d}'
    title_data = [[
        Paragraph('OFFICIAL PAYMENT RECEIPT', ParagraphStyle(
            'RT', parent=styles['Normal'],
            fontSize=16, fontName='Helvetica-Bold',
            textColor=primary
        )),
        Paragraph(
            f'<b>{receipt_no}</b>',
            ParagraphStyle(
                'RN', parent=styles['Normal'],
                fontSize=14, fontName='Helvetica-Bold',
                textColor=accent, alignment=TA_RIGHT
            )
        )
    ]]
    title_tbl = Table(title_data, colWidths=[100*mm, 70*mm])
    title_tbl.setStyle(TableStyle([
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(title_tbl)
    elements.append(HRFlowable(
        width='100%', thickness=2,
        color=accent, spaceAfter=6*mm
    ))

    # ── RECEIPT META INFO ──────────────────────────
    issued_date = (
        payment.verified_at.strftime('%B %d, %Y')
        if payment.verified_at
        else timezone.now().strftime('%B %d, %Y')
    )
    meta_data = [
        [
            Paragraph('Date Issued:', label_style),
            Paragraph(issued_date, value_style),
            Paragraph('Payment Method:', label_style),
            Paragraph(
                payment.get_payment_method_display(),
                value_style
            ),
        ],
        [
            Paragraph('Invoice Number:', label_style),
            Paragraph(invoice.invoice_number, value_style),
            Paragraph('Transaction Ref:', label_style),
            Paragraph(
                payment.transaction_reference or '—',
                value_style
            ),
        ],
        [
            Paragraph('Verified By:', label_style),
            Paragraph(
                payment.verified_by.get_full_name()
                if payment.verified_by else '—',
                value_style
            ),
            Paragraph('Verification Date:', label_style),
            Paragraph(
                payment.verified_at.strftime('%B %d, %Y %H:%M')
                if payment.verified_at else '—',
                value_style
            ),
        ],
    ]
    meta_tbl = Table(
        meta_data,
        colWidths=[40*mm, 45*mm, 40*mm, 45*mm]
    )
    meta_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), light),
        ('ROWBACKGROUNDS', (0,0), (-1,-1),
         [light, white, light]),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5,
         colors.HexColor('#dee2e6')),
        ('ROUNDEDCORNERS', [4]),
    ]))
    elements.append(meta_tbl)
    elements.append(Spacer(1, 6*mm))

    # ── TENANT & SHOP INFO ─────────────────────────
    elements.append(
        Paragraph('TENANT INFORMATION', section_style)
    )
    tenant_data = [
        [
            Paragraph('Business Name:', label_style),
            Paragraph(tenant.business_name, value_style),
            Paragraph('Shop Number:', label_style),
            Paragraph(
                f'Shop {shop.shop_number} — '
                f'{shop.floor} Floor',
                value_style
            ),
        ],
        [
            Paragraph('Tenant Name:', label_style),
            Paragraph(
                tenant.user.get_full_name(),
                value_style
            ),
            Paragraph('Lease Period:', label_style),
            Paragraph(
                f'{invoice.period_start.strftime("%b %d, %Y")}'
                f' — '
                f'{invoice.period_end.strftime("%b %d, %Y")}',
                value_style
            ),
        ],
        [
            Paragraph('Email:', label_style),
            Paragraph(tenant.user.email, value_style),
            Paragraph('TIN Number:', label_style),
            Paragraph(
                tenant.tin_number or '—',
                value_style
            ),
        ],
    ]
    tenant_tbl = Table(
        tenant_data,
        colWidths=[40*mm, 45*mm, 40*mm, 45*mm]
    )
    tenant_tbl.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0), (-1,-1),
         [light, white, light]),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5,
         colors.HexColor('#dee2e6')),
    ]))
    elements.append(tenant_tbl)
    elements.append(Spacer(1, 6*mm))

    # ── PAYMENT BREAKDOWN ──────────────────────────
    elements.append(
        Paragraph('PAYMENT BREAKDOWN', section_style)
    )
    breakdown_header = [
        [
            Paragraph('Description', ParagraphStyle(
                'BH', parent=styles['Normal'],
                fontSize=10, fontName='Helvetica-Bold',
                textColor=white
            )),
            Paragraph('Details', ParagraphStyle(
                'BH2', parent=styles['Normal'],
                fontSize=10, fontName='Helvetica-Bold',
                textColor=white, alignment=TA_CENTER
            )),
            Paragraph('Amount (ETB)', ParagraphStyle(
                'BH3', parent=styles['Normal'],
                fontSize=10, fontName='Helvetica-Bold',
                textColor=white, alignment=TA_RIGHT
            )),
        ]
    ]
    breakdown_rows = [
        [
            Paragraph('Base Rent', styles['Normal']),
            Paragraph(
                f'{lease.monthly_rent} ETB/month × 3 months',
                ParagraphStyle('S', parent=styles['Normal'],
                               fontSize=9,
                               textColor=colors.grey)
            ),
            Paragraph(
                f'{invoice.base_rent:,.2f}',
                ParagraphStyle('R', parent=styles['Normal'],
                               alignment=TA_RIGHT)
            ),
        ],
        [
            Paragraph('Maintenance Fee', styles['Normal']),
            Paragraph(
                'Quarterly common area maintenance',
                ParagraphStyle('S', parent=styles['Normal'],
                               fontSize=9,
                               textColor=colors.grey)
            ),
            Paragraph(
                f'{invoice.maintenance_fee:,.2f}',
                ParagraphStyle('R', parent=styles['Normal'],
                               alignment=TA_RIGHT)
            ),
        ],
    ]

    if invoice.other_charges > 0:
        breakdown_rows.append([
            Paragraph('Other Charges', styles['Normal']),
            Paragraph(
                invoice.other_charges_description or '—',
                ParagraphStyle('S', parent=styles['Normal'],
                               fontSize=9,
                               textColor=colors.grey)
            ),
            Paragraph(
                f'{invoice.other_charges:,.2f}',
                ParagraphStyle('R', parent=styles['Normal'],
                               alignment=TA_RIGHT)
            ),
        ])

    if invoice.penalty_amount > 0:
        breakdown_rows.append([
            Paragraph(
                'Late Payment Penalty',
                ParagraphStyle('P', parent=styles['Normal'],
                               textColor=colors.red)
            ),
            Paragraph(
                f'{invoice.get_days_overdue()} days × '
                f'1% of ETB {lease.monthly_rent}/month',
                ParagraphStyle('S', parent=styles['Normal'],
                               fontSize=9,
                               textColor=colors.red)
            ),
            Paragraph(
                f'{invoice.penalty_amount:,.2f}',
                ParagraphStyle('R', parent=styles['Normal'],
                               alignment=TA_RIGHT,
                               textColor=colors.red)
            ),
        ])

    # Total row
    breakdown_rows.append([
        Paragraph('TOTAL AMOUNT PAID', ParagraphStyle(
            'T', parent=styles['Normal'],
            fontSize=12, fontName='Helvetica-Bold',
            textColor=primary
        )),
        Paragraph('', styles['Normal']),
        Paragraph(
            f'ETB {payment.amount_paid:,.2f}',
            ParagraphStyle(
                'TA', parent=styles['Normal'],
                fontSize=13, fontName='Helvetica-Bold',
                textColor=primary, alignment=TA_RIGHT
            )
        ),
    ])

    all_rows  = breakdown_header + breakdown_rows
    n_rows    = len(all_rows)
    breakdown_tbl = Table(
        all_rows,
        colWidths=[70*mm, 65*mm, 35*mm]
    )
    style_cmds = [
        # Header row
        ('BACKGROUND',    (0,0), (-1,0), primary),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-2), 0.5,
         colors.HexColor('#dee2e6')),
        # Total row background
        ('BACKGROUND',
         (0, n_rows-1), (-1, n_rows-1),
         colors.HexColor('#e8f0fe')),
        ('LINEABOVE',
         (0, n_rows-1), (-1, n_rows-1),
         2, primary),
        # Alternating rows
        ('ROWBACKGROUNDS',
         (0,1), (-1, n_rows-2),
         [white, light]),
    ]
    breakdown_tbl.setStyle(TableStyle(style_cmds))
    elements.append(breakdown_tbl)
    elements.append(Spacer(1, 8*mm))

    # ── VERIFIED STAMP ─────────────────────────────
    stamp_data = [[
        Paragraph(
            '✓  PAYMENT VERIFIED & CONFIRMED',
            ParagraphStyle(
                'Stamp', parent=styles['Normal'],
                fontSize=13, fontName='Helvetica-Bold',
                textColor=green, alignment=TA_CENTER
            )
        )
    ]]
    stamp_tbl = Table(stamp_data, colWidths=[170*mm])
    stamp_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1),
         colors.HexColor('#d1edde')),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('ROUNDEDCORNERS', [6]),
        ('BOX', (0,0), (-1,-1), 1.5, green),
    ]))
    elements.append(stamp_tbl)
    elements.append(Spacer(1, 6*mm))

    # ── FOOTER ─────────────────────────────────────
    elements.append(HRFlowable(
        width='100%', thickness=1,
        color=colors.HexColor('#dee2e6'),
        spaceAfter=4*mm
    ))
    footer_data = [[
        Paragraph(
            f'This is an official receipt issued by '
            f'<b>{mall.name}</b>.<br/>'
            f'Keep this document for your records. '
            f'For inquiries contact: {mall.contact_email}',
            ParagraphStyle(
                'Footer', parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#6c757d'),
                alignment=TA_CENTER
            )
        )
    ]]
    footer_tbl = Table(footer_data, colWidths=[170*mm])
    elements.append(footer_tbl)

    # ── BUILD PDF ──────────────────────────────────
    doc.build(elements)
    buffer.seek(0)
    return buffer


def download_receipt(request, payment_pk):
    """
    View that serves the receipt PDF for download.
    Accessible by the tenant who owns it and by staff.
    """
    from .models import Payment
    from django.shortcuts import get_object_or_404
    from django.contrib.auth.decorators import login_required

    payment = get_object_or_404(
        Payment,
        pk=payment_pk,
        status='VERIFIED'
    )

    # Security: only owner tenant or staff can download
    user = request.user
    if user.role == 'TENANT':
        try:
            if payment.tenant != user.tenant_profile:
                from django.http import Http404
                raise Http404
        except Exception:
            from django.http import Http404
            raise Http404

    buffer   = generate_receipt_pdf(payment)
    filename = (
        f'Receipt_{payment.invoice.invoice_number}.pdf'
    )
    response = HttpResponse(
        buffer,
        content_type='application/pdf'
    )
    response['Content-Disposition'] = (
        f'attachment; filename="{filename}"'
    )
    return response