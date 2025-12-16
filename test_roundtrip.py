#!/usr/bin/env python3
"""
Round-trip test script

Tests that CSV -> CFF -> CSV conversion produces identical results.
"""

import csv
import sys
import os
from cff_writer import CFFWriter
from cff_reader import CFFReader


def read_csv(path):
    """Read CSV file and return data"""
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric values
            converted_row = {}
            for key, value in row.items():
                if value == '':
                    converted_row[key] = ''
                else:
                    try:
                        if '.' not in value:
                            converted_row[key] = int(value)
                        else:
                            converted_row[key] = float(value)
                    except ValueError:
                        converted_row[key] = value
            data.append(converted_row)
    return data


def compare_data(data1, data2):
    """Compare two datasets for equality"""
    if len(data1) != len(data2):
        return False, f"Row count mismatch: {len(data1)} vs {len(data2)}"
    
    for i, (row1, row2) in enumerate(zip(data1, data2)):
        if set(row1.keys()) != set(row2.keys()):
            return False, f"Column mismatch at row {i}"
        
        for key in row1.keys():
            val1 = row1[key]
            val2 = row2[key]
            
            # Handle floating point comparison
            if isinstance(val1, float) and isinstance(val2, float):
                if abs(val1 - val2) > 1e-9:
                    return False, f"Value mismatch at row {i}, column {key}: {val1} vs {val2}"
            else:
                if val1 != val2:
                    return False, f"Value mismatch at row {i}, column {key}: {val1} vs {val2}"
    
    return True, "Data matches"


def test_file(csv_path):
    """Test round-trip conversion for a CSV file"""
    print(f"\nTesting: {csv_path}")
    print("-" * 60)
    
    # Read original CSV
    original_data = read_csv(csv_path)
    print(f"✓ Read CSV: {len(original_data)} rows, {len(original_data[0])} columns")
    
    # Write to CFF
    cff_path = csv_path.replace('.csv', '.cff')
    writer = CFFWriter(cff_path)
    writer.write(original_data)
    print(f"✓ Wrote CFF: {cff_path}")
    
    # Read back from CFF
    reader = CFFReader(cff_path)
    cff_data = reader.read()
    print(f"✓ Read CFF: {len(cff_data)} rows, {len(cff_data[0])} columns")
    
    # Compare
    match, message = compare_data(original_data, cff_data)
    if match:
        print(f"✓ Round-trip test PASSED: {message}")
    else:
        print(f"✗ Round-trip test FAILED: {message}")
        return False
    
    # Test selective column read
    column_names = reader.get_column_names()
    if len(column_names) > 1:
        test_column = column_names[0]
        print(f"\nTesting selective read of column: {test_column}")
        columns_data = reader.read_columns([test_column])
        print(f"✓ Selective read succeeded: {len(columns_data[test_column])} values")
        
        # Verify values match
        for i, val in enumerate(columns_data[test_column]):
            if val != cff_data[i][test_column]:
                print(f"✗ Selective read mismatch at row {i}")
                return False
        print(f"✓ Selective read values match")
    
    # Show file info
    print(f"\nFile Info:")
    print(reader.info())
    
    # Show file sizes
    csv_size = os.path.getsize(csv_path)
    cff_size = os.path.getsize(cff_path)
    compression_ratio = (1 - cff_size / csv_size) * 100
    print(f"\nFile Sizes:")
    print(f"  CSV: {csv_size} bytes")
    print(f"  CFF: {cff_size} bytes")
    print(f"  Compression: {compression_ratio:.1f}%")
    
    return True


def main():
    """Run all round-trip tests"""
    test_files = [
        'test_data/simple.csv',
        'test_data/sample.csv'
    ]
    
    print("=" * 60)
    print("CFF Round-Trip Test Suite")
    print("=" * 60)
    
    all_passed = True
    for test_file_path in test_files:
        if os.path.exists(test_file_path):
            if not test_file(test_file_path):
                all_passed = False
        else:
            print(f"\nWarning: Test file not found: {test_file_path}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests FAILED")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
