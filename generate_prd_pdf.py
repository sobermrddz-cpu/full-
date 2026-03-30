#!/usr/bin/env python3
"""
Generate PRD PDF from markdown file using weasyprint and markdown.
"""
import os
import sys
import re
from pathlib import Path

def install_requirements():
    """Install required packages if not available."""
    try:
        import markdown
    except ImportError:
        print("Installing markdown...")
        os.system("pip install markdown")
    
    try:
        import weasyprint
    except ImportError:
        print("Installing weasyprint...")
        os.system("pip install weasyprint")

def markdown_to_html(markdown_text):
    """Convert markdown to HTML with styling."""
    try:
        import markdown
    except ImportError:
        print("markdown not available, attempting to install...")
        os.system("pip install markdown")
        import markdown
    
    # Convert markdown to HTML
    html_content = markdown.markdown(
        markdown_text,
        extensions=['tables', 'toc', 'codehilite']
    )
    
    return html_content

def create_pdf(markdown_file, output_file):
    """Create PDF from markdown file."""
    # Read markdown file
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    # Convert to HTML
    html_content = markdown_to_html(markdown_text)
    
    # Create styled HTML document
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>PropDZ - Product Requirements Document</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: white;
                padding: 40px;
                max-width: 1200px;
                margin: 0 auto;
            }}
            
            h1 {{
                font-size: 2.5em;
                color: #0066cc;
                margin-bottom: 0.5em;
                padding-bottom: 0.3em;
                border-bottom: 3px solid #0066cc;
                page-break-after: avoid;
            }}
            
            h2 {{
                font-size: 2em;
                color: #0066cc;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
                padding-bottom: 0.2em;
                border-bottom: 2px solid #0066cc;
                page-break-after: avoid;
            }}
            
            h3 {{
                font-size: 1.5em;
                color: #0099ff;
                margin-top: 1.2em;
                margin-bottom: 0.4em;
                page-break-after: avoid;
            }}
            
            h4 {{
                font-size: 1.2em;
                color: #0099ff;
                margin-top: 1em;
                margin-bottom: 0.3em;
                page-break-after: avoid;
            }}
            
            h5 {{
                font-size: 1.1em;
                color: #333;
                margin-top: 0.8em;
                margin-bottom: 0.3em;
                page-break-after: avoid;
            }}
            
            h6 {{
                font-size: 1em;
                color: #333;
                margin-top: 0.6em;
                margin-bottom: 0.2em;
                page-break-after: avoid;
            }}
            
            p {{
                margin-bottom: 1em;
                text-align: justify;
            }}
            
            ul, ol {{
                margin-left: 2em;
                margin-bottom: 1em;
            }}
            
            li {{
                margin-bottom: 0.5em;
            }}
            
            code {{
                background-color: #f5f5f5;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
                color: #d63384;
            }}
            
            pre {{
                background-color: #f5f5f5;
                padding: 1em;
                border-radius: 5px;
                overflow-x: auto;
                margin-bottom: 1em;
                border-left: 4px solid #0066cc;
            }}
            
            pre code {{
                background-color: transparent;
                padding: 0;
                color: #333;
                border-radius: 0;
            }}
            
            blockquote {{
                border-left: 4px solid #0066cc;
                margin-left: 0;
                padding-left: 1.5em;
                color: #666;
                font-style: italic;
                margin-bottom: 1em;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 1.5em;
                page-break-inside: avoid;
            }}
            
            th {{
                background-color: #0066cc;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: bold;
            }}
            
            td {{
                padding: 10px 12px;
                border-bottom: 1px solid #ddd;
            }}
            
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            tr:hover {{
                background-color: #f0f8ff;
            }}
            
            hr {{
                border: none;
                border-top: 2px solid #0066cc;
                margin: 3em 0;
                page-break-after: avoid;
            }}
            
            strong {{
                font-weight: bold;
                color: #0066cc;
            }}
            
            em {{
                font-style: italic;
                color: #666;
            }}
            
            .toc {{
                background-color: #f0f8ff;
                padding: 1.5em;
                border-radius: 5px;
                margin-bottom: 2em;
                page-break-inside: avoid;
            }}
            
            .toc h2 {{
                margin-top: 0;
                border-bottom: none;
            }}
            
            .toc ul {{
                margin-left: 1.5em;
            }}
            
            @page {{
                size: A4;
                margin: 1.5cm;
            }}
            
            @media print {{
                body {{
                    padding: 0;
                }}
                
                h1 {{
                    page-break-before: always;
                    margin-top: 0;
                }}
                
                h2 {{
                    page-break-after: avoid;
                }}
                
                table {{
                    page-break-inside: avoid;
                }}
            }}
            
            .status-badge {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 0.85em;
                margin-left: 0.5em;
            }}
            
            .status-ready {{
                background-color: #28a745;
                color: white;
            }}
            
            .section-number {{
                color: #0066cc;
                font-weight: bold;
                margin-right: 0.5em;
            }}
        </style>
    </head>
    <body>
        {html_content}
        <hr style="margin-top: 3em; margin-bottom: 1em;">
        <footer style="text-align: center; color: #999; font-size: 0.9em; padding-top: 1em;">
            <p>PropDZ - Real Estate Platform</p>
            <p>Product Requirements Document (PRD) v1.0</p>
            <p>Generated on March 16, 2026</p>
        </footer>
    </body>
    </html>
    """
    
    # Generate PDF
    try:
        from weasyprint import HTML, CSS
        
        # Write HTML to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp:
            tmp.write(full_html)
            tmp_path = tmp.name
        
        try:
            # Convert HTML to PDF
            HTML(string=full_html).write_pdf(output_file)
            print(f"✅ PDF generated successfully: {output_file}")
            return True
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    except ImportError:
        print("weasyprint not available, installing...")
        os.system("pip install weasyprint")
        try:
            from weasyprint import HTML
            HTML(string=full_html).write_pdf(output_file)
            print(f"✅ PDF generated successfully: {output_file}")
            return True
        except Exception as e:
            print(f"❌ Error generating PDF: {e}")
            return False
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        print("\nTrying alternative method...")
        return False

if __name__ == '__main__':
    # Get script directory
    script_dir = Path(__file__).parent
    prd_file = script_dir / 'PRD.md'
    pdf_file = script_dir / 'PRD.pdf'
    
    if not prd_file.exists():
        print(f"❌ Error: PRD.md not found in {script_dir}")
        sys.exit(1)
    
    print("📄 Converting PRD.md to PDF...")
    print(f"📥 Input:  {prd_file}")
    print(f"📤 Output: {pdf_file}")
    print()
    
    # Install requirements
    install_requirements()
    
    # Generate PDF
    if create_pdf(str(prd_file), str(pdf_file)):
        print()
        print("✨ Done! PRD PDF created successfully.")
        print(f"📍 Location: {pdf_file}")
    else:
        print("❌ Failed to generate PDF")
        sys.exit(1)
