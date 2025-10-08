#!/usr/bin/env python3
"""
Simple ASCII FBX to Binary FBX Converter
Based on the FBX 7.x binary specification

This converter takes an ASCII FBX file and converts it to binary format
that Blender can import.
"""

import struct
import zlib
import re
from pathlib import Path


# FBX Binary constants
FBX_HEADER = b'Kaydara FBX Binary  \x00\x1a\x00'
FBX_VERSION = 7400
FBX_FOOTER_CODE = [0xf8, 0x5a, 0x8c, 0x6a, 0xde, 0xf5, 0xd9, 0x7e, 
                   0xec, 0xe9, 0x0c, 0xe3, 0x75, 0x8f, 0x29, 0x0b]


class FBXNode:
    def __init__(self, name=''):
        self.name = name
        self.properties = []
        self.children = []


def parse_ascii_fbx(content):
    """Parse ASCII FBX into a node tree."""
    lines = content.split('\n')
    root = FBXNode('__ROOT__')
    stack = [root]
    
    for line in lines:
        stripped = line.strip()
        
        # Skip comments and empty lines
        if not stripped or stripped.startswith(';'):
            continue
        
        # Handle closing brace
        if stripped == '}':
            if len(stack) > 1:
                stack.pop()
            continue
        
        # Check for node definition (contains colon)
        if ':' in stripped and '{' not in stripped:
            # Parse node definition
            parts = stripped.split(':', 1)
            node_def = parts[0].strip()
            
            # Extract node name and properties
            if ',' in node_def:
                # Example: Model: 12345, "Model::Name", "Mesh"
                items = [x.strip() for x in node_def.split(',')]
                node_name = items[0]
                properties = items[1:] if len(items) > 1 else []
            else:
                node_name = node_def
                properties = []
            
            node = FBXNode(node_name)
            
            # Parse properties - handle quotes and numbers
            for prop in properties:
                prop = prop.strip()
                if prop.startswith('"') and prop.endswith('"'):
                    # String property
                    node.properties.append(prop[1:-1])
                elif '.' in prop or 'e' in prop.lower():
                    # Float
                    try:
                        node.properties.append(float(prop))
                    except:
                        node.properties.append(prop)
                else:
                    # Integer
                    try:
                        node.properties.append(int(prop))
                    except:
                        node.properties.append(prop)
            
            stack[-1].children.append(node)
            
            # Check if this node has children (has opening brace on same line or next)
            if '{' in stripped:
                stack.append(node)
        elif '{' in stripped:
            # Standalone opening brace - previous node gets children
            if stack[-1].children:
                stack.append(stack[-1].children[-1])
    
    return root


def encode_property(value):
    """Encode a property value to FBX binary format."""
    if isinstance(value, str):
        # String: type 'S' + length (4 bytes) + UTF-8 bytes
        encoded = value.encode('utf-8')
        return b'S' + struct.pack('<I', len(encoded)) + encoded
    elif isinstance(value, bool):
        # Boolean: type 'C' + 1 byte
        return b'C' + struct.pack('<b', 1 if value else 0)
    elif isinstance(value, int):
        # Integer: choose appropriate size
        if -128 <= value <= 127:
            return b'C' + struct.pack('<b', value)
        elif -32768 <= value <= 32767:
            return b'Y' + struct.pack('<h', value)
        elif -2147483648 <= value <= 2147483647:
            return b'I' + struct.pack('<i', value)
        else:
            return b'L' + struct.pack('<q', value)
    elif isinstance(value, float):
        # Float/Double: use double for precision
        return b'D' + struct.pack('<d', value)
    elif isinstance(value, (list, tuple)):
        # Array
        if not value:
            return b'i' + struct.pack('<III', 0, 0, 0)
        
        # Determine array type
        first_type = type(value[0])
        if first_type == int:
            arr_type = b'i'
            arr_data = b''.join(struct.pack('<i', int(v)) for v in value)
        elif first_type == float:
            arr_type = b'd'
            arr_data = b''.join(struct.pack('<d', float(v)) for v in value)
        elif first_type == bool:
            arr_type = b'b'
            arr_data = b''.join(struct.pack('<?', v) for v in value)
        else:
            # Fallback
            arr_type = b'i'
            arr_data = b''.join(struct.pack('<i', 0) for _ in value)
        
        # Try compression
        encoding = 0
        data = arr_data
        if len(arr_data) > 128:
            compressed = zlib.compress(arr_data)
            if len(compressed) < len(arr_data):
                data = compressed
                encoding = 1
        
        header = struct.pack('<III', len(value), encoding, len(data))
        return arr_type + header + data
    else:
        # Unknown type - encode as string
        encoded = str(value).encode('utf-8')
        return b'S' + struct.pack('<I', len(encoded)) + encoded


def write_fbx_node(fp, node):
    """Write a single FBX node in binary format."""
    # Encode node name
    name_bytes = node.name.encode('utf-8')
    
    # Encode properties
    prop_data = b''
    for prop in node.properties:
        prop_data += encode_property(prop)
    
    # Prepare node record
    num_properties = len(node.properties)
    property_list_len = len(prop_data)
    name_len = len(name_bytes)
    
    # Placeholder for end offset
    end_offset_pos = fp.tell()
    fp.write(struct.pack('<I', 0))
    
    # Write node header
    fp.write(struct.pack('<I', num_properties))
    fp.write(struct.pack('<I', property_list_len))
    fp.write(struct.pack('<B', name_len))
    fp.write(name_bytes)
    fp.write(prop_data)
    
    # Write children
    if node.children:
        for child in node.children:
            write_fbx_node(fp, child)
        # Null record to mark end of children
        fp.write(b'\x00' * 13)
    
    # Update end offset
    end_pos = fp.tell()
    fp.seek(end_offset_pos)
    fp.write(struct.pack('<I', end_pos))
    fp.seek(end_pos)


def convert_ascii_to_binary(ascii_path, binary_path):
    """Convert ASCII FBX to Binary FBX."""
    # Read ASCII file
    with open(ascii_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse ASCII FBX
    root = parse_ascii_fbx(content)
    
    # Write binary FBX
    with open(binary_path, 'wb') as fp:
        # Write header
        fp.write(FBX_HEADER)
        fp.write(struct.pack('<I', FBX_VERSION))
        
        # Write nodes
        for child in root.children:
            write_fbx_node(fp, child)
        
        # Write final null record
        fp.write(b'\x00' * 13)
        
        # Write footer
        fp.write(bytes(FBX_FOOTER_CODE))
        fp.write(b'\x00' * 4)
        fp.write(struct.pack('<I', FBX_VERSION))
        fp.write(b'\x00' * 120)


def convert_all_fbx_in_directory(directory):
    """Convert all ASCII FBX files in a directory to binary."""
    directory = Path(directory)
    converted = []
    
    for fbx_file in directory.rglob('*.fbx'):
        # Check if it's ASCII FBX
        with open(fbx_file, 'rb') as f:
            header = f.read(25)
            if not header.startswith(FBX_HEADER):
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

