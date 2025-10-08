#!/usr/bin/env python3
"""
ASCII FBX to Binary FBX Converter
Uses Autodesk FBX Converter CLI tool

This script wraps the Autodesk FBX Converter to convert ASCII FBX files
to binary format that Blender can import.

Requirements:
- FBX Converter must be installed and in PATH
- Download from: https://www.autodesk.com/developer-network/platform-technologies/fbx-converter-archives
"""

import subprocess
import shutil
import sys
from pathlib import Path


def find_fbx_converter():
    """Find FBX Converter executable."""
    # Try common executable names
    converter_names = [
        'FbxConverter',
        'FbxConverter.exe',
        'fbxconverter',
        'fbxconverter.exe'
    ]
    
    for name in converter_names:
        if shutil.which(name):
            return name
    
    return None


def convert_with_fbx_converter(input_file, output_file, converter_exe):
    """Convert ASCII FBX to Binary using Autodesk FBX Converter.
    
    Command line reference:
    https://download.autodesk.com/us/fbx/2013/FBXconverter/index.html
    """
    try:
        # FBX Converter command format:
        # FbxConverter <input_file> <output_file> /sffBIN /dffBIN /l
        # /sffBIN - source file format binary (actually we want ASCII to binary)
        # /dffBIN - destination file format binary
        # /l - verbose logging
        
        cmd = [
            converter_exe,
            str(input_file),
            str(output_file),
            '/dffBIN',  # Destination format: binary
            '/v'  # Verbose
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, "Conversion successful"
        else:
            return False, f"FBX Converter failed: {result.stderr or result.stdout}"
            
    except subprocess.TimeoutExpired:
        return False, "Conversion timed out"
    except Exception as e:
        return False, f"Error running FBX Converter: {e}"


def check_if_binary_fbx(file_path):
    """Check if a file is already binary FBX."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(23)
            return header == b'Kaydara FBX Binary  \x00\x1a\x00'
    except:
        return False


def convert_ascii_to_binary(ascii_path, binary_path):
    """Convert ASCII FBX to Binary FBX using Autodesk FBX Converter."""
    # Find FBX Converter
    converter = find_fbx_converter()
    
    if not converter:
        raise FileNotFoundError(
            "FBX Converter not found in PATH!\n\n"
            "Please install Autodesk FBX Converter and add it to your PATH.\n"
            "Download from: https://www.autodesk.com/developer-network/platform-technologies/fbx-converter-archives\n\n"
            "Or add it manually to your PATH environment variable."
        )
    
    # Convert using FBX Converter
    success, message = convert_with_fbx_converter(ascii_path, binary_path, converter)
    
    if not success:
        raise RuntimeError(f"FBX conversion failed: {message}")
    
    return True


def convert_all_fbx_in_directory(directory):
    """Convert all ASCII FBX files in a directory to binary."""
    directory = Path(directory)
    converted = []
    
    # Check if FBX Converter is available first
    converter = find_fbx_converter()
    if not converter:
        print("ERROR: FBX Converter not found in PATH!")
        print("\nPlease install Autodesk FBX Converter and add it to your PATH.")
        print("Download from: https://www.autodesk.com/developer-network/platform-technologies/fbx-converter-archives")
        return converted
    
    for fbx_file in directory.rglob('*.fbx'):
        # Check if it's ASCII FBX
        if not check_if_binary_fbx(fbx_file):
            # It's ASCII, convert it
            binary_file = fbx_file.with_name(fbx_file.stem + '_binary.fbx')
            print(f"Converting: {fbx_file.name}")
            try:
                convert_ascii_to_binary(str(fbx_file), str(binary_file))
                converted.append(binary_file)
                print(f"  -> Created: {binary_file.name}")
            except Exception as e:
                print(f"  -> Error: {e}")
    
    return converted


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python ascii_to_binary_fbx.py <input.fbx> [output.fbx]")
        print("  python ascii_to_binary_fbx.py <directory>  # Convert all FBX in directory")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    
    if input_path.is_dir():
        # Convert all FBX files in directory
        print(f"Scanning directory: {input_path}")
        converted = convert_all_fbx_in_directory(input_path)
        print(f"\nConverted {len(converted)} file(s)")
    elif input_path.is_file():
        # Convert single file
        output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_name(input_path.stem + '_binary.fbx')
        
        print(f"Converting: {input_path}")
        print(f"Output: {output_path}")
        
        try:
            convert_ascii_to_binary(str(input_path), str(output_path))
            print("[OK] Conversion successful!")
        except Exception as e:
            print(f"[ERROR] Conversion failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print(f"Error: {input_path} not found")
        sys.exit(1)

