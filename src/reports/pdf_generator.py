"""
PDF Report Generator for Pharma AI System
EY Techathon 6.0 - Round 2
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak
)
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from config import recommendation_for

# Color scheme
COLORS = {
    'primary': HexColor('#1E3A5F'),
    'secondary': HexColor('#F7931E'),
    'success': HexColor('#28A745'),
    'warning': HexColor('#FFC107'),
    'danger': HexColor('#DC3545'),
    'light': HexColor('#F8F9FA'),
    'text': HexColor('#2D3748'),
    'muted': HexColor('#6C757D'),
}


def create_styles():
    """Create custom paragraph styles"""
    styles = getSampleStyleSheet()
    
    # Add custom styles with unique names to avoid conflicts
    custom_styles = {
        'PharmaTitle': ParagraphStyle(
            name='PharmaTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=COLORS['primary'],
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ),
        'PharmaSubtitle': ParagraphStyle(
            name='PharmaSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=COLORS['muted'],
            spaceAfter=30,
            alignment=TA_CENTER
        ),
        'PharmaSection': ParagraphStyle(
            name='PharmaSection',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=COLORS['primary'],
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ),
        'PharmaSubsection': ParagraphStyle(
            name='PharmaSubsection',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=COLORS['secondary'],
            spaceBefore=15,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ),
        'PharmaBody': ParagraphStyle(
            name='PharmaBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor=COLORS['text'],
            spaceAfter=10,
            alignment=TA_JUSTIFY,
            leading=14
        ),
        'PharmaFinding': ParagraphStyle(
            name='PharmaFinding',
            parent=styles['Normal'],
            fontSize=10,
            textColor=COLORS['text'],
            leftIndent=15,
            spaceAfter=8
        )
    }
    
    for name, style in custom_styles.items():
        if name not in styles:
            styles.add(style)
    
    return styles


def create_header(canvas, doc):
    """Create page header"""
    canvas.saveState()
    canvas.setFillColor(COLORS['primary'])
    canvas.rect(0, doc.height + doc.topMargin + 20, doc.width + doc.leftMargin + doc.rightMargin, 30, fill=1)
    canvas.setFillColor(white)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawString(doc.leftMargin, doc.height + doc.topMargin + 32, "PHARMA AI | Opportunity Assessment Report")
    canvas.drawRightString(doc.width + doc.leftMargin, doc.height + doc.topMargin + 32, 
                           datetime.now().strftime("%B %d, %Y"))
    canvas.restoreState()


def create_footer(canvas, doc):
    """Create page footer"""
    canvas.saveState()
    canvas.setStrokeColor(COLORS['muted'])
    canvas.line(doc.leftMargin, 40, doc.width + doc.leftMargin, 40)
    canvas.setFillColor(COLORS['muted'])
    canvas.setFont('Helvetica', 9)
    canvas.drawString(doc.leftMargin, 25, "Confidential | EY Techathon 6.0")
    canvas.drawRightString(doc.width + doc.leftMargin, 25, f"Page {doc.page}")
    canvas.restoreState()


def on_page(canvas, doc):
    """Combined header and footer"""
    create_header(canvas, doc)
    create_footer(canvas, doc)


def create_score_table(scores: Dict[str, float]) -> Table:
    """Create score visualization table"""
    
    def get_score_color(score):
        if score >= 7.5:
            return COLORS['success']
        elif score >= 5.5:
            return COLORS['warning']
        return COLORS['danger']
    
    data = [
        ['Metric', 'Score', 'Rating'],
        ['Overall', f"{scores.get('overall', 0):.1f}", '★' * int(scores.get('overall', 0) // 2)],
        ['Market Attractiveness', f"{scores.get('market_attractiveness', 0):.1f}", ''],
        ['Competitive Intensity', f"{scores.get('competitive_intensity', 0):.1f}", ''],
        ['Regulatory Feasibility', f"{scores.get('regulatory_feasibility', 0):.1f}", ''],
        ['Scientific Rationale', f"{scores.get('scientific_rationale', 0):.1f}", ''],
        ['Supply Chain', f"{scores.get('supply_chain_feasibility', 0):.1f}", '']
    ]
    
    table = Table(data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, 1), COLORS['light']),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 1), (1, 1), 14),
        ('TEXTCOLOR', (1, 1), (1, 1), get_score_color(scores.get('overall', 0))),
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS['muted']),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    return table


def generate_pdf_report(report_data: Dict[str, Any], output_path: str) -> str:
    """Generate a professional PDF report from the assessment data"""
    styles = create_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch
    )
    
    story = []
    
    # Title Page
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("Pharmaceutical Opportunity Assessment", styles['PharmaTitle']))
    
    query = report_data.get('query', {})
    story.append(Paragraph(
        f"{query.get('molecule', 'N/A')} | {query.get('indication', 'N/A')}",
        styles['PharmaSubtitle']
    ))
    
    story.append(Spacer(1, 0.5*inch))
    
    # Recommendation box
    overall_score = report_data.get('scores', {}).get('overall', 0)
    rec_text = recommendation_for(overall_score)
    rec_color = {
        "PROCEED": COLORS['success'],
        "PROCEED WITH CAUTION": COLORS['warning'],
        "RECONSIDER": COLORS['danger'],
    }[rec_text]
    
    rec_table = Table([[rec_text]], colWidths=[4*inch])
    rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), rec_color),
        ('TEXTCOLOR', (0, 0), (-1, -1), white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 16),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(rec_table)
    
    story.append(Spacer(1, 0.5*inch))
    story.append(create_score_table(report_data.get('scores', {})))
    story.append(Spacer(1, 0.3*inch))
    
    # Metadata
    metadata = report_data.get('metadata', {})
    meta_text = f"""
    <b>Report ID:</b> {report_data.get('report_id', 'N/A')}<br/>
    <b>Generated:</b> {report_data.get('created_at', 'N/A')}<br/>
    <b>Sources Analyzed:</b> {metadata.get('total_sources', 0)}<br/>
    <b>Data Freshness:</b> {metadata.get('data_freshness', 'N/A')}
    """
    story.append(Paragraph(meta_text, styles['PharmaBody']))
    
    story.append(PageBreak())
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", styles['PharmaSection']))
    summary = report_data.get('executive_summary', 'No summary available.')
    summary = summary.replace('**', '').replace('*', '')
    for line in summary.split('\n'):
        if line.strip():
            story.append(Paragraph(line.strip(), styles['PharmaBody']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Key Findings
    story.append(Paragraph("Key Findings", styles['PharmaSection']))
    
    findings = report_data.get('key_findings', [])
    for finding in findings:
        category = finding.get('category', 'Finding')
        text = finding.get('finding', '')
        confidence = finding.get('confidence', 0)
        
        story.append(Paragraph(f"<b>{category}</b>", styles['PharmaSubsection']))
        story.append(Paragraph(f"{text} <i>(Confidence: {confidence*100:.0f}%)</i>", styles['PharmaFinding']))
    
    story.append(PageBreak())
    
    # Recommendations
    story.append(Paragraph("Recommendations", styles['PharmaSection']))
    recs = report_data.get('recommendations', [])
    for rec in recs:
        story.append(Paragraph(f"• {rec}", styles['PharmaFinding']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Opportunities & Risks
    col_data = [['Opportunities', 'Risks']]
    opportunities = report_data.get('opportunities', [])
    risks = report_data.get('risks', [])
    
    max_rows = max(len(opportunities), len(risks))
    for i in range(max_rows):
        opp = opportunities[i] if i < len(opportunities) else ''
        risk = risks[i] if i < len(risks) else ''
        col_data.append([f"✓ {opp}" if opp else '', f"⚠ {risk}" if risk else ''])
    
    if max_rows > 0:
        story.append(Paragraph("Opportunities & Risks", styles['PharmaSection']))
        opp_table = Table(col_data, colWidths=[3.5*inch, 3.5*inch])
        opp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS['muted']),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(opp_table)
    
    story.append(Spacer(1, 0.3*inch))
    
    # Next Steps
    story.append(Paragraph("Recommended Next Steps", styles['PharmaSection']))
    next_steps = report_data.get('next_steps', [])
    for i, step in enumerate(next_steps, 1):
        story.append(Paragraph(f"{i}. {step}", styles['PharmaFinding']))
    
    # Build PDF
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    
    return output_path
