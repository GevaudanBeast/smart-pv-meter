#!/usr/bin/env python3
"""
Prepare optimized brand assets for Home Assistant brands repository.
Creates icon.png (256x256) and icon@2x.png (512x512) with proper optimization.
"""

from PIL import Image
import os

# Paths
SOURCE_ICON = "custom_components/spvm/icon.png"
OUTPUT_DIR = "brand_assets"
ICON_256 = os.path.join(OUTPUT_DIR, "icon.png")
ICON_512 = os.path.join(OUTPUT_DIR, "icon@2x.png")

def prepare_brand_assets():
    """Create optimized brand assets for Home Assistant brands repo."""

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("🎨 Preparing Home Assistant brand assets for SPVM...")
    print(f"📂 Source: {SOURCE_ICON}")
    print(f"📁 Output directory: {OUTPUT_DIR}/\n")

    # Load source image
    print(f"📖 Loading source image...")
    source_img = Image.open(SOURCE_ICON)
    print(f"   ✓ Loaded: {source_img.size[0]}×{source_img.size[1]}px, mode={source_img.mode}")

    # Ensure RGBA mode
    if source_img.mode != 'RGBA':
        print(f"   ⚠️  Converting from {source_img.mode} to RGBA...")
        source_img = source_img.convert('RGBA')

    # Create icon@2x.png (512×512)
    print(f"\n🔧 Creating icon@2x.png (512×512)...")
    if source_img.size == (512, 512):
        icon_512 = source_img.copy()
        print(f"   ✓ Using source image (already 512×512)")
    else:
        icon_512 = source_img.resize((512, 512), Image.Resampling.LANCZOS)
        print(f"   ✓ Resized from {source_img.size[0]}×{source_img.size[1]} to 512×512")

    # Save with optimization and interlacing
    icon_512.save(
        ICON_512,
        'PNG',
        optimize=True,
        compress_level=9,  # Maximum compression (lossless)
        interlace=True     # Progressive/interlaced format
    )
    file_size_512 = os.path.getsize(ICON_512) / 1024
    print(f"   ✓ Saved: {ICON_512}")
    print(f"   ✓ Size: {file_size_512:.1f} KB (optimized, interlaced)")

    # Create icon.png (256×256)
    print(f"\n🔧 Creating icon.png (256×256)...")
    icon_256 = source_img.resize((256, 256), Image.Resampling.LANCZOS)
    print(f"   ✓ Resized from {source_img.size[0]}×{source_img.size[1]} to 256×256")

    # Save with optimization and interlacing
    icon_256.save(
        ICON_256,
        'PNG',
        optimize=True,
        compress_level=9,  # Maximum compression (lossless)
        interlace=True     # Progressive/interlaced format
    )
    file_size_256 = os.path.getsize(ICON_256) / 1024
    print(f"   ✓ Saved: {ICON_256}")
    print(f"   ✓ Size: {file_size_256:.1f} KB (optimized, interlaced)")

    # Summary
    print(f"\n✅ Brand assets created successfully!")
    print(f"\n📋 Summary:")
    print(f"   • icon.png: 256×256px, {file_size_256:.1f} KB")
    print(f"   • icon@2x.png: 512×512px, {file_size_512:.1f} KB")
    print(f"   • Format: PNG with transparency (RGBA)")
    print(f"   • Optimization: Level 9 (lossless)")
    print(f"   • Interlacing: Enabled (progressive)")

    print(f"\n📦 Next steps:")
    print(f"   1. Clone home-assistant/brands repo")
    print(f"   2. Copy files to: custom_integrations/spvm/")
    print(f"   3. Create PR with these assets")

    return True

if __name__ == "__main__":
    try:
        prepare_brand_assets()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
