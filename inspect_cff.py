#!/usr/bin/env python3
"""
Hex Viewer for CFF Files

Displays the binary structure of a CFF file in hexadecimal format,
useful for inspecting the file layout and verifying the specification.
"""

import sys
import argparse
from cff_reader import CFFReader


def hex_dump(data: bytes, offset: int = 0, length: int = None, show_ascii: bool = True):
    """
    Display binary data in hexadecimal format
    
    Args:
        data: Binary data to display
        offset: Starting offset for display
        length: Number of bytes to display (None = all)
        show_ascii: Whether to show ASCII representation
    """
    if length is None:
        length = len(data)
    
    end = min(offset + length, len(data))
    
    for i in range(offset, end, 16):
        # Address
        print(f"{i:08x}  ", end="")
        
        # Hex bytes
        hex_part = ""
        ascii_part = ""
        for j in range(16):
            if i + j < end:
                byte = data[i + j]
                hex_part += f"{byte:02x} "
                # ASCII representation
                if 32 <= byte <= 126:
                    ascii_part += chr(byte)
                else:
                    ascii_part += "."
            else:
                hex_part += "   "
        
        print(hex_part, end="")
        
        if show_ascii:
            print(f" |{ascii_part}|")
        else:
            print()


def inspect_cff_file(file_path: str, show_header_only: bool = False, 
                    show_column_data: bool = False, column_name: str = None):
    """
    Inspect a CFF file and display its structure
    
    Args:
        file_path: Path to CFF file
        show_header_only: Only show header
        show_column_data: Show column data blocks
        column_name: Specific column to inspect
    """
    print("=" * 70)
    print(f"CFF File Inspection: {file_path}")
    print("=" * 70)
    
    # Read the entire file
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    print(f"\nFile Size: {len(file_data)} bytes")
    
    # Parse header
    reader = CFFReader(file_path)
    
    print(f"\n{reader.info()}")
    
    # Calculate header size
    header_end = reader.columns_metadata[0].offset if reader.columns_metadata else len(file_data)
    
    print(f"\n" + "=" * 70)
    print(f"HEADER (0x00000000 - 0x{header_end:08x}, {header_end} bytes)")
    print("=" * 70)
    hex_dump(file_data, 0, header_end)
    
    if not show_header_only:
        # Show column blocks
        for col in reader.columns_metadata:
            print(f"\n" + "=" * 70)
            print(f"COLUMN: {col.name} (offset=0x{col.offset:08x})")
            print(f"Type: {reader.get_schema()[col.name]}")
            print(f"Compressed size: {col.compressed_size} bytes")
            print(f"Uncompressed size: {col.uncompressed_size} bytes")
            print("=" * 70)
            
            if show_column_data or (column_name and col.name == column_name):
                # Show first 128 bytes of compressed data
                display_length = min(128, col.compressed_size)
                hex_dump(file_data, col.offset, display_length)
                if col.compressed_size > 128:
                    print(f"  ... ({col.compressed_size - 128} more bytes)")
            else:
                print(f"(Use --show-data to view column data)")


def main():
    parser = argparse.ArgumentParser(
        description='Hex viewer and inspector for CFF files'
    )
    parser.add_argument('file', help='CFF file to inspect')
    parser.add_argument(
        '--header-only',
        action='store_true',
        help='Only show header (no column data)'
    )
    parser.add_argument(
        '--show-data',
        action='store_true',
        help='Show column data blocks'
    )
    parser.add_argument(
        '--column',
        help='Show data for specific column only'
    )
    
    args = parser.parse_args()
    
    try:
        inspect_cff_file(
            args.file,
            show_header_only=args.header_only,
            show_column_data=args.show_data,
            column_name=args.column
        )
    except FileNotFoundError:
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
