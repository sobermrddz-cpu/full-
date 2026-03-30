#!/usr/bin/env python3
"""
Generate PRD PDF from markdown file using reportlab.
"""
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import re

def read_markdown(file_path):
    """Read markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def create_pdf_with_reportlab(markdown_text, output_file):
    """Create PDF from markdown using reportlab."""
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
        title="PropDZ - Product Requirements Document"
    )
    
    # Container for PDF elements
    elements = []
    
    # Create custom styles
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#0066cc'),
        spaceAfter=6,
        spaceBefore=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Heading 2 style
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#0066cc'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Heading 3 style
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#0099ff'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )
    
    # Body text style
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leading=12
    )
    
    # Parse markdown and add to elements
    lines = markdown_text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Title (single #)
        if line.startswith('# ') and not line.startswith('## '):
            title = line[2:].strip()
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 0.1*inch))
            i += 1
        
        # Heading 2 (##)
        elif line.startswith('## '):
            heading = line[3:].strip()
            if elements:  # Add page break before major sections (but not before first)
                elements.append(PageBreak())
            elements.append(Paragraph(heading, h2_style))
            elements.append(Spacer(1, 0.1*inch))
            i += 1
        
        # Heading 3 (###)
        elif line.startswith('### '):
            heading = line[4:].strip()
            elements.append(Paragraph(heading, h3_style))
            elements.append(Spacer(1, 0.05*inch))
            i += 1
        
        # Horizontal rules
        elif line.strip().startswith('---'):
            elements.append(Spacer(1, 0.1*inch))
            i += 1
        
        # Skip empty lines
        elif not line.strip():
            elements.append(Spacer(1, 0.05*inch))
            i += 1
        
        # Regular text
        elif line.strip():
            # Remove markdown formatting
            text = line.strip()
            text = text.replace('**', '')
            text = text.replace('*', '')
            text = text.replace('`', '')
            text = text.replace('~~', '')
            
            elements.append(Paragraph(text, body_style))
            i += 1
        
        else:
            i += 1
    
    # Add footer
    elements.append(Spacer(1, 0.3*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER
    )
    elements.append(Paragraph("PropDZ - Real Estate Platform", footer_style))
    elements.append(Paragraph("Product Requirements Document (PRD) v1.0", footer_style))
    elements.append(Paragraph("Generated on March 16, 2026", footer_style))
    
    # Build PDF
    try:
        doc.build(elements)
        return True
    except Exception as e:
        print(f"Error building PDF: {e}")
        return False

if __name__ == '__main__':
    script_dir = Path(__file__).parent
    prd_file = script_dir / 'PRD.md'
    pdf_file = script_dir / 'PRD.pdf'
    
    if not prd_file.exists():
        print(f"❌ Error: PRD.md not found in {script_dir}")
        exit(1)
    
    print("📄 Converting PRD.md to PDF using ReportLab...")
    print(f"📥 Input:  {prd_file}")
    print(f"📤 Output: {pdf_file}")
    print()
    
    # Read markdown
    markdown_text = read_markdown(str(prd_file))
    
    # Generate PDF
    if create_pdf_with_reportlab(markdown_text, str(pdf_file)):
        print("✅ PDF generated successfully!")
        print(f"📍 Location: {pdf_file}")
        
        # Check file size
        file_size = os.path.getsize(str(pdf_file)) / (1024*1024)  # Convert to MB
        print(f"📊 File Size: {file_size:.2f} MB")
    else:
        print("❌ Failed to generate PDF")
        exit(1)
