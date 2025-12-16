#!/usr/bin/env python3
"""
CFF to CSV Converter

Converts a Columnar File Format (CFF) file back to CSV.
"""

import csv
import sys
import argparse
from cff_reader import CFFReader


def cff_to_csv(cff_path: str, csv_path: str, columns: list = None):
    """
    Convert CFF file to CSV format
    
    Args:
        cff_path: Path to input CFF file
        csv_path: Path to output CSV file
        columns: Optional list of column names to export (for selective read)
    """
    # Read CFF file
    reader = CFFReader(cff_path)
    
    # Read specified columns or all columns
    if columns:
        columns_data = reader.read_columns(columns)
        column_names = columns
    else:
        columns_data = reader.read_columns()
        column_names = reader.get_column_names()
    
    # Write to CSV
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=column_names)
        writer.writeheader()
        
        # Convert column data to rows
        for i in range(reader.num_rows):
            row = {col_name: columns_data[col_name][i] for col_name in column_names}
            writer.writerow(row)
    
    print(f"Successfully converted {cff_path} to {csv_path}")
    print(f"  Rows: {reader.num_rows}")
    print(f"  Columns: {len(column_names)}")
    if columns:
        print(f"  Selected columns: {', '.join(columns)}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert Columnar File Format (CFF) to CSV'
    )
    parser.add_argument('input', help='Input CFF file path')
    parser.add_argument('output', help='Output CSV file path')
    parser.add_argument(
        '-c', '--columns',
        nargs='+',
        help='Specific columns to export (enables selective column read)'
    )
    
    args = parser.parse_args()
    
    try:
        cff_to_csv(args.input, args.output, args.columns)
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
