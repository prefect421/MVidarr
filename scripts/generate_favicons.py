#!/usr/bin/env python3
"""
Favicon Generator for MVidarr
Creates multiple favicon sizes and formats for optimal browser support
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

# Add project root to path  
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class FaviconGenerator:
    def __init__(self):
        self.project_root = project_root
        self.static_dir = self.project_root / "frontend" / "static"
        self.logo_path = self.static_dir / "MVidarr.png"
        
        # Favicon sizes for different use cases
        self.favicon_sizes = [
            16, 32, 48, 64, 96, 128, 192, 256, 512
        ]
        
        # Standard favicon file formats
        self.favicon_formats = {
            'favicon.ico': [16, 32, 48],  # Multi-resolution ICO
            'favicon-16x16.png': [16],
            'favicon-32x32.png': [32], 
            'favicon-96x96.png': [96],
            'apple-touch-icon.png': [180],  # Apple devices
            'android-chrome-192x192.png': [192],  # Android
            'android-chrome-512x512.png': [512],  # Android large
            'mstile-150x150.png': [150],  # Microsoft tiles
        }
        
    def create_icon_from_logo(self, size):
        """Create a favicon from the MVidarr logo at specified size"""
        try:
            # Load the original logo
            if not self.logo_path.exists():
                print(f"❌ Logo not found: {self.logo_path}")
                return self.create_text_favicon(size)
                
            with Image.open(self.logo_path) as img:
                # Convert to RGBA if needed
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Resize with high quality
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                
                # Enhance for small sizes
                if size <= 32:
                    # For very small sizes, add subtle enhancement
                    enhancer = resized
                else:
                    enhancer = resized
                
                return enhancer
                
        except Exception as e:
            print(f"⚠️  Error processing logo: {e}")
            return self.create_text_favicon(size)
    
    def create_text_favicon(self, size):
        """Create a text-based favicon as fallback"""
        # Create a new image with transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate colors and text
        bg_color = (30, 58, 138, 255)  # Blue background
        text_color = (255, 255, 255, 255)  # White text
        
        # Draw background circle
        margin = max(1, size // 16)
        draw.ellipse([margin, margin, size-margin, size-margin], 
                    fill=bg_color, outline=(59, 130, 246, 255), width=max(1, size//32))
        
        # Add text "MV" for MVidarr
        try:
            # Try to use a system font
            font_size = max(6, size // 3)
            font = ImageFont.load_default()
            
            text = "MV"
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Center the text
            x = (size - text_width) // 2
            y = (size - text_height) // 2 - 1
            
            draw.text((x, y), text, font=font, fill=text_color)
            
        except Exception as e:
            print(f"⚠️  Font error: {e}")
            # Simple pixel art fallback for very small sizes
            if size >= 16:
                # Draw a simple "M" shape
                draw.rectangle([size//4, size//3, size//4+2, size*2//3], fill=text_color)
                draw.rectangle([size*3//4-2, size//3, size*3//4, size*2//3], fill=text_color)
                draw.rectangle([size//4, size//3, size*3//4, size//3+2], fill=text_color)
        
        return img
    
    def generate_ico_file(self, output_path, sizes):
        """Generate a multi-resolution ICO file"""
        images = []
        for size in sizes:
            icon_img = self.create_icon_from_logo(size)
            images.append(icon_img)
        
        # Save as ICO with multiple sizes
        if images:
            images[0].save(
                output_path,
                format='ICO',
                sizes=[(img.width, img.height) for img in images],
                append_images=images[1:] if len(images) > 1 else None
            )
            return True
        return False
    
    def generate_png_file(self, output_path, size):
        """Generate a PNG favicon file"""
        icon_img = self.create_icon_from_logo(size)
        icon_img.save(output_path, format='PNG', optimize=True)
        return True
    
    def generate_all_favicons(self):
        """Generate all favicon files"""
        print("🎨 MVidarr Favicon Generator")
        print("=" * 50)
        
        generated_files = []
        
        for filename, sizes in self.favicon_formats.items():
            output_path = self.static_dir / filename
            
            try:
                print(f"📱 Generating {filename}...")
                
                if filename.endswith('.ico'):
                    success = self.generate_ico_file(output_path, sizes)
                else:
                    success = self.generate_png_file(output_path, sizes[0])
                
                if success:
                    file_size = output_path.stat().st_size
                    print(f"✅ Generated {filename} ({file_size} bytes)")
                    generated_files.append(filename)
                else:
                    print(f"❌ Failed to generate {filename}")
                    
            except Exception as e:
                print(f"❌ Error generating {filename}: {e}")
        
        return generated_files
    
    def generate_manifest_json(self):
        """Generate web app manifest for PWA support"""
        manifest = {
            "name": "MVidarr",
            "short_name": "MVidarr",
            "description": "Professional Music Video Management System",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#1e3a8a",
            "theme_color": "#3b82f6",
            "orientation": "portrait",
            "icons": [
                {
                    "src": "/static/android-chrome-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "/static/android-chrome-512x512.png", 
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        }
        
        manifest_path = self.static_dir / "manifest.json"
        import json
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"✅ Generated manifest.json for PWA support")
        return "manifest.json"
    
    def generate_browserconfig_xml(self):
        """Generate browserconfig.xml for Microsoft tiles"""
        browserconfig = '''<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square150x150logo src="/static/mstile-150x150.png"/>
            <TileColor>#1e3a8a</TileColor>
        </tile>
    </msapplication>
</browserconfig>'''
        
        config_path = self.static_dir / "browserconfig.xml"
        with open(config_path, 'w') as f:
            f.write(browserconfig)
        
        print(f"✅ Generated browserconfig.xml for Microsoft tiles")
        return "browserconfig.xml"

def main():
    generator = FaviconGenerator()
    
    print("🚀 Starting favicon generation...")
    
    # Generate all favicon files
    generated_files = generator.generate_all_favicons()
    
    # Generate additional config files
    manifest_file = generator.generate_manifest_json()
    browserconfig_file = generator.generate_browserconfig_xml()
    
    generated_files.extend([manifest_file, browserconfig_file])
    
    print(f"\n📊 Favicon Generation Summary")
    print(f"✅ Generated {len(generated_files)} files:")
    for filename in generated_files:
        print(f"  • {filename}")
    
    print(f"\n🎯 Files saved to: {generator.static_dir}")
    print(f"🔗 Ready for implementation in HTML templates")
    
    return generated_files

if __name__ == "__main__":
    main()