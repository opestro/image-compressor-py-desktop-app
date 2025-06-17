# Multi-Platform Build Instructions

This document explains how to build Image Compressor for different platforms and architectures.

## Platform Compatibility

### Current Build Status
- ✅ **macOS ARM64** (Apple Silicon) - Built successfully
- ❌ **Windows ARM64** - Requires building on Windows ARM system
- ❌ **Windows x64** - Requires building on Windows x64 system
- ❌ **Linux x64** - Requires building on Linux x64 system

### Why Cross-Platform Building is Challenging

PyInstaller creates **platform-specific executables**:
- Each executable only works on the platform it was built on
- ARM64 vs x64 architectures are incompatible
- Different operating systems have different APIs and libraries

## Building Options

### Option 1: Build on Each Platform (Recommended)

#### macOS (Current Platform)
```bash
# You're already set up! Just run:
source path/to/venv/bin/activate
python build_multiplatform.py
```

#### Windows (x64 or ARM64)
1. Install Python 3.11+ with tkinter support
2. Clone your repository
3. Create virtual environment:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Run build script:
   ```cmd
   python build_multiplatform.py
   ```

#### Linux
1. Install dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-tk python3-pip python3-venv
   ```
2. Set up project:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Build:
   ```bash
   python build_multiplatform.py
   ```

### Option 2: GitHub Actions (Automated)

Use the included `.github/workflows/build.yml` file:

1. Push your code to GitHub
2. Go to Actions tab in your repository
3. Run the "Build Multi-Platform Executables" workflow
4. Download artifacts for each platform

### Option 3: Virtual Machines / Cloud Services

For Windows ARM64 specifically:
- Use Azure VMs with Windows ARM64
- Use GitHub Codespaces with ARM64 runners
- Use local Windows ARM64 device (Surface Pro X, etc.)

## Platform-Specific Notes

### Windows ARM64
- **Why it doesn't work**: Your macOS ARM64 build uses different system calls and libraries
- **Solution**: Must build on actual Windows ARM64 system
- **Alternative**: Some Windows ARM64 systems can run x64 executables via emulation (with performance penalty)

### macOS Universal Binaries
To create a universal binary that works on both Intel and Apple Silicon Macs:
```bash
# This requires building on both architectures and combining them
# Currently not supported by PyInstaller automatically
```

### Linux Distribution Compatibility
- Build on the oldest Linux version you want to support
- Consider using Docker for consistent builds
- Static linking may be needed for some dependencies

## Testing Your Builds

### macOS
```bash
# Test the current build
./dist/ImageCompressor
```

### Windows
```cmd
# Test the executable
dist\ImageCompressor.exe
```

### Linux
```bash
# Make executable if needed
chmod +x dist/ImageCompressor
./dist/ImageCompressor
```

## Troubleshooting

### Common Issues

1. **Missing tkinter**
   - macOS: `brew install python-tk`
   - Linux: `sudo apt-get install python3-tk`
   - Windows: Usually included with Python installer

2. **Large executable size**
   - Normal for PyInstaller (15-20MB)
   - Includes Python interpreter and all dependencies

3. **Slow startup**
   - First run extracts files to temp directory
   - Subsequent runs are faster

4. **Antivirus false positives**
   - Common with PyInstaller executables
   - Add exception or sign the executable

### Platform-Specific Issues

#### Windows
- **Antivirus**: Windows Defender may flag the executable
- **Permissions**: May need to "Run as Administrator"
- **Dependencies**: Ensure Visual C++ Redistributable is installed

#### macOS
- **Gatekeeper**: Unsigned apps may be blocked
- **Solution**: Right-click → Open, or run `xattr -d com.apple.quarantine dist/ImageCompressor`

#### Linux
- **Missing libraries**: Install system dependencies
- **Desktop integration**: Create .desktop file for application menu

## Advanced Building

### Custom Icon
- Ensure `assets/logo.ico` exists for Windows/Linux
- macOS can use .ico files as well

### Code Signing
- **Windows**: Use SignTool with certificate
- **macOS**: Use codesign with Apple Developer certificate
- **Linux**: AppImage signing or package manager signatures

### Distribution
- **Windows**: Create installer with NSIS or Inno Setup
- **macOS**: Create .app bundle or .dmg
- **Linux**: Create .deb, .rpm, or AppImage

## Resources

- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Cross-Platform Python Applications](https://packaging.python.org/) 