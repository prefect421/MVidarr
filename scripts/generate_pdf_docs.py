#!/usr/bin/env python3
"""
PDF Documentation Generator for MVidarr Enhanced
Converts Markdown documentation to professional PDFs with embedded screenshots
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
import markdown2
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class PDFDocumentGenerator:
    def __init__(self):
        self.project_root = project_root
        self.docs_dir = self.project_root / "docs"
        self.screenshots_dir = self.docs_dir / "screenshots"
        self.output_dir = self.docs_dir / "pdf"
        self.output_dir.mkdir(exist_ok=True)
        
        # Font configuration for better rendering
        self.font_config = FontConfiguration()
        
    def process_markdown_images(self, content, base_path):
        """Process markdown image references to use absolute paths"""
        def replace_image(match):
            alt_text = match.group(1)
            image_path = match.group(2)
            
            # Convert relative paths to absolute
            if not image_path.startswith(('http://', 'https://', '/')):
                # Handle screenshot references
                if 'screenshots/' in image_path:
                    abs_path = self.screenshots_dir / Path(image_path).name
                else:
                    abs_path = base_path / image_path
                
                if abs_path.exists():
                    image_path = abs_path.as_uri()
                else:
                    print(f"⚠️  Image not found: {abs_path}")
                    return f"![{alt_text}](missing-image.png)"
                    
            return f'<div class="image-container"><img src="{image_path}" alt="{alt_text}" class="doc-image"/><p class="image-caption">{alt_text}</p></div>'
        
        # Replace markdown image syntax with HTML
        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_image, content)
        return content
    
    def generate_css_styles(self):
        """Generate CSS styles for professional PDF formatting"""
        return """
        @page {
            size: A4;
            margin: 2cm 1.5cm 2cm 1.5cm;
            @top-center {
                content: "MVidarr Enhanced Documentation";
                font-size: 10pt;
                color: #666;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5pt;
            }
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10pt;
                color: #666;
            }
        }
        
        @page :first {
            @top-center { content: ""; }
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            font-size: 11pt;
        }
        
        h1 {
            color: #2c3e50;
            font-size: 24pt;
            margin-top: 0;
            margin-bottom: 20pt;
            padding-bottom: 10pt;
            border-bottom: 2px solid #3498db;
        }
        
        h2 {
            color: #34495e;
            font-size: 18pt;
            margin-top: 25pt;
            margin-bottom: 15pt;
            page-break-after: avoid;
        }
        
        h3 {
            color: #7f8c8d;
            font-size: 14pt;
            margin-top: 20pt;
            margin-bottom: 10pt;
        }
        
        h4, h5, h6 {
            color: #95a5a6;
            font-size: 12pt;
            margin-top: 15pt;
            margin-bottom: 8pt;
        }
        
        p {
            text-align: justify;
            margin-bottom: 10pt;
        }
        
        .image-container {
            text-align: center;
            margin: 20pt 0;
            page-break-inside: avoid;
        }
        
        .doc-image {
            max-width: 100%;
            max-height: 400pt;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .image-caption {
            font-style: italic;
            color: #666;
            font-size: 10pt;
            margin-top: 5pt;
            margin-bottom: 0;
        }
        
        code {
            background-color: #f8f9fa;
            padding: 2pt 4pt;
            border-radius: 3px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 10pt;
        }
        
        pre {
            background-color: #f8f9fa;
            padding: 10pt;
            border-radius: 4px;
            border-left: 4px solid #3498db;
            overflow-x: auto;
            margin: 15pt 0;
            page-break-inside: avoid;
        }
        
        pre code {
            background: none;
            padding: 0;
        }
        
        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 15pt;
            margin: 15pt 0;
            color: #555;
            font-style: italic;
        }
        
        ul, ol {
            margin: 10pt 0;
            padding-left: 20pt;
        }
        
        li {
            margin-bottom: 5pt;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15pt 0;
            font-size: 10pt;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8pt;
            text-align: left;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        
        .toc {
            page-break-after: always;
        }
        
        .toc h2 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10pt;
        }
        
        .toc ul {
            list-style: none;
            padding-left: 0;
        }
        
        .toc li {
            margin-bottom: 8pt;
            padding-left: 0;
        }
        
        .toc a {
            text-decoration: none;
            color: #3498db;
        }
        
        .cover-page {
            text-align: center;
            page-break-after: always;
            padding-top: 100pt;
        }
        
        .cover-title {
            font-size: 32pt;
            color: #2c3e50;
            margin-bottom: 20pt;
        }
        
        .cover-subtitle {
            font-size: 18pt;
            color: #7f8c8d;
            margin-bottom: 40pt;
        }
        
        .cover-info {
            font-size: 12pt;
            color: #95a5a6;
            margin-top: 60pt;
        }
        
        .badges {
            text-align: center;
            margin: 20pt 0;
        }
        
        .badge {
            display: inline-block;
            padding: 4pt 8pt;
            background-color: #3498db;
            color: white;
            border-radius: 3px;
            font-size: 9pt;
            margin: 2pt;
        }
        
        .warning {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 10pt;
            border-radius: 4px;
            margin: 15pt 0;
        }
        
        .info {
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            padding: 10pt;
            border-radius: 4px;
            margin: 15pt 0;
        }
        
        .success {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 10pt;
            border-radius: 4px;
            margin: 15pt 0;
        }
        """
    
    def generate_cover_page(self, title, subtitle=""):
        """Generate a professional cover page"""
        today = datetime.now().strftime("%B %d, %Y")
        return f"""
        <div class="cover-page">
            <h1 class="cover-title">{title}</h1>
            <p class="cover-subtitle">{subtitle}</p>
            <div class="badges">
                <span class="badge">Production Ready</span>
                <span class="badge">Version 2.0</span>
                <span class="badge">Professional Edition</span>
            </div>
            <div class="cover-info">
                <p><strong>MVidarr Enhanced</strong><br/>
                Professional Music Video Management System</p>
                <p>Generated: {today}</p>
            </div>
        </div>
        """
    
    def convert_markdown_to_pdf(self, md_file_path, output_name, title, subtitle=""):
        """Convert a markdown file to PDF with embedded screenshots"""
        print(f"📄 Converting {md_file_path.name} to PDF...")
        
        try:
            # Read markdown content
            with open(md_file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Process images to use absolute paths
            processed_content = self.process_markdown_images(markdown_content, md_file_path.parent)
            
            # Convert markdown to HTML
            html_content = markdown2.markdown(
                processed_content,
                extras=[
                    'fenced-code-blocks',
                    'tables',
                    'break-on-newline',
                    'code-friendly',
                    'cuddled-lists',
                    'footnotes',
                    'header-ids',
                    'markdown-in-html',
                    'numbering',
                    'strike',
                    'target-blank-links',
                    'task_list'
                ]
            )
            
            # Add cover page and complete HTML structure
            cover_page = self.generate_cover_page(title, subtitle)
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{title}</title>
            </head>
            <body>
                {cover_page}
                <div class="content">
                    {html_content}
                </div>
            </body>
            </html>
            """
            
            # Generate PDF
            css_styles = CSS(string=self.generate_css_styles(), font_config=self.font_config)
            html_doc = HTML(string=full_html, base_url=str(self.project_root))
            
            output_path = self.output_dir / output_name
            html_doc.write_pdf(output_path, stylesheets=[css_styles], font_config=self.font_config)
            
            print(f"✅ PDF generated: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error converting {md_file_path.name}: {e}")
            return None
    
    def generate_all_pdfs(self):
        """Generate all PDF documents"""
        print("🚀 MVidarr Enhanced PDF Documentation Generator")
        print("=" * 60)
        
        generated_pdfs = []
        
        # Document specifications
        documents = [
            {
                'file': self.project_root / 'README.md',
                'output': 'MVidarr-Enhanced-Overview.pdf',
                'title': 'MVidarr Enhanced',
                'subtitle': 'Professional Music Video Management System - Overview'
            },
            {
                'file': self.docs_dir / 'INSTALLATION-GUIDE.md',
                'output': 'MVidarr-Enhanced-Installation-Guide.pdf',
                'title': 'Installation Guide',
                'subtitle': 'Complete Setup Instructions for MVidarr Enhanced'
            },
            {
                'file': self.docs_dir / 'USER-GUIDE.md',
                'output': 'MVidarr-Enhanced-User-Guide.pdf',
                'title': 'User Guide',
                'subtitle': 'Complete User Manual for MVidarr Enhanced'
            },
            {
                'file': self.docs_dir / 'VIDEO_ORGANIZATION.md',
                'output': 'MVidarr-Enhanced-Video-Organization.pdf',
                'title': 'Video Organization System',
                'subtitle': 'Advanced Video Management and Organization'
            }
        ]
        
        # Generate each PDF
        for doc in documents:
            if doc['file'].exists():
                pdf_path = self.convert_markdown_to_pdf(
                    doc['file'],
                    doc['output'],
                    doc['title'],
                    doc['subtitle']
                )
                if pdf_path:
                    generated_pdfs.append(pdf_path)
            else:
                print(f"⚠️  File not found: {doc['file']}")
        
        # Generate summary
        print(f"\n📊 PDF Generation Summary")
        print(f"✅ Generated {len(generated_pdfs)} PDF documents:")
        for pdf in generated_pdfs:
            size_mb = pdf.stat().st_size / (1024 * 1024)
            print(f"  • {pdf.name} ({size_mb:.1f} MB)")
        
        print(f"\n📁 All PDFs saved to: {self.output_dir}")
        
        return generated_pdfs

def main():
    generator = PDFDocumentGenerator()
    generated_pdfs = generator.generate_all_pdfs()
    
    if generated_pdfs:
        print(f"\n🎉 PDF generation complete!")
        print(f"📚 {len(generated_pdfs)} professional PDF documents ready for distribution")
    else:
        print(f"\n❌ No PDFs were generated")

if __name__ == "__main__":
    main()