#!/usr/bin/env python3
"""
Multi-platform build script for Image Compressor
This script helps build the application with platform-specific optimizations
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def get_platform_info():
    """Get platform-specific information"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == 'windows':
        if 'arm' in machine or 'aarch64' in machine:
            return 'windows-arm64'
        else:
            return 'windows-x64'
    elif system == 'darwin':
        if 'arm' in machine or 'aarch64' in machine:
            return 'macos-arm64'
        else:
            return 'macos-x64'
    elif system == 'linux':
        if 'arm' in machine or 'aarch64' in machine:
            return 'linux-arm64'
        else:
            return 'linux-x64'
    else:
        return f'{system}-{machine}'

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import tkinter
        print("✓ tkinter is available")
    except ImportError:
        print("✗ tkinter is not available")
        if sys.platform == 'linux':
            print("  Install with: sudo apt-get install python3-tk")
        elif sys.platform == 'darwin':
            print("  Install with: brew install python-tk")
        return False
    
    try:
        import PIL
        print("✓ Pillow is available")
    except ImportError:
        print("✗ Pillow is not available")
        print("  Install with: pip install Pillow")
        return False
    
    try:
        import tkinterdnd2
        print("✓ tkinterdnd2 is available")
    except ImportError:
        print("✗ tkinterdnd2 is not available")
        print("  Install with: pip install tkinterdnd2")
        return False
    
    try:
        import PyInstaller
        print("✓ PyInstaller is available")
    except ImportError:
        print("✗ PyInstaller is not available")
        print("  Install with: pip install pyinstaller")
        return False
    
    return True

def build_executable():
    """Build the executable for the current platform"""
    platform_info = get_platform_info()
    print(f"\n🔨 Building for platform: {platform_info}")
    
    # Check if spec file exists
    spec_file = 'image_compressor.spec'
    if not os.path.exists(spec_file):
        print(f"✗ Spec file '{spec_file}' not found")
        return False
    
    # Clean previous builds
    if os.path.exists('dist'):
        shutil.rmtree('dist')
        print("🧹 Cleaned previous dist directory")
    
    if os.path.exists('build'):
        shutil.rmtree('build')
        print("🧹 Cleaned previous build directory")
    
    # Run PyInstaller
    try:
        cmd = [sys.executable, '-m', 'PyInstaller', spec_file]
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            print(f"✅ Build successful for {platform_info}")
            
            # List built files
            dist_path = Path('dist')
            if dist_path.exists():
                print("\n📦 Built files:")
                for file in dist_path.iterdir():
                    size = file.stat().st_size / (1024 * 1024)  # Size in MB
                    print(f"  - {file.name} ({size:.1f} MB)")
            
            return True
        else:
            print(f"✗ Build failed with return code: {result.returncode}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during build: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Image Compressor Multi-Platform Builder")
    print("=" * 50)
    
    platform_info = get_platform_info()
    print(f"Platform: {platform_info}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Architecture: {platform.machine()}")
    
    print("\n🔍 Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Please install missing dependencies before building")
        return 1
    
    print("\n🔨 Starting build process...")
    if build_executable():
        print(f"\n🎉 Build completed successfully for {platform_info}!")
        print("\n📋 Next steps:")
        print("  1. Test your executable in the 'dist' directory")
        print("  2. For other platforms, run this script on those systems")
        print("  3. Or use GitHub Actions for automated cross-platform builds")
        return 0
    else:
        print("\n❌ Build failed")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 