#!/usr/bin/env python3
"""
CSV to CFF Converter

Converts a CSV file to Columnar File Format (CFF).
"""

import csv
import sys
import argparse
from cff_writer import CFFWriter


def csv_to_cff(csv_path: str, cff_path: str):
    """
    Convert CSV file to CFF format
    
    Args:
        csv_path: Path to input CSV file
        cff_path: Path to output CFF file
    """
    # Read CSV file
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric values
            converted_row = {}
            for key, value in row.items():
                # Try to convert to number
                if value == '':
                    converted_row[key] = ''
                else:
                    try:
                        # Try integer first
                        if '.' not in value:
                            converted_row[key] = int(value)
                        else:
                            converted_row[key] = float(value)
                    except ValueError:
                        # Keep as string
                        converted_row[key] = value
            data.append(converted_row)
    
    if not data:
        print("Error: CSV file is empty", file=sys.stderr)
        sys.exit(1)
    
    # Write to CFF format
    writer = CFFWriter(cff_path)
    writer.write(data)
    
    print(f"Successfully converted {csv_path} to {cff_path}")
    print(f"  Rows: {len(data)}")
    print(f"  Columns: {len(data[0])}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert CSV file to Columnar File Format (CFF)'
    )
    parser.add_argument('input', help='Input CSV file path')
    parser.add_argument('output', help='Output CFF file path')
    
    args = parser.parse_args()
    
    try:
        csv_to_cff(args.input, args.output)
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
