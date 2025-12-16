#!/usr/bin/env python3
"""
Interactive Demo of CFF Capabilities

Demonstrates the key features of the Columnar File Format.
"""

from cff_writer import CFFWriter
from cff_reader import CFFReader
import time


def demo_basic_usage():
    """Demonstrate basic write and read operations"""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Usage - Write and Read")
    print("=" * 70)
    
    # Create sample data
    data = [
        {'id': 1, 'name': 'Alice', 'age': 30, 'score': 95.5},
        {'id': 2, 'name': 'Bob', 'age': 25, 'score': 87.0},
        {'id': 3, 'name': 'Charlie', 'age': 35, 'score': 92.3},
    ]
    
    print("\n1. Writing data to CFF format...")
    print(f"   Data: {len(data)} rows, {len(data[0])} columns")
    
    writer = CFFWriter('demo_basic.cff')
    writer.write(data)
    print("   ✓ Written to demo_basic.cff")
    
    print("\n2. Reading data back...")
    reader = CFFReader('demo_basic.cff')
    read_data = reader.read()
    print(f"   ✓ Read {len(read_data)} rows")
    
    print("\n3. Verifying data integrity...")
    if data == read_data:
        print("   ✓ Data matches perfectly!")
    else:
        print("   ✗ Data mismatch!")
    
    print("\n4. Schema information:")
    for col_name, col_type in reader.get_schema().items():
        print(f"   {col_name}: {col_type}")


def demo_selective_read():
    """Demonstrate selective column reads"""
    print("\n" + "=" * 70)
    print("DEMO 2: Selective Column Read (Column Pruning)")
    print("=" * 70)
    
    # Create data with many columns
    data = [
        {'id': i, 'name': f'Person{i}', 'age': 20 + i, 
         'salary': 50000 + i * 1000, 'city': 'City' + str(i % 3)}
        for i in range(100)
    ]
    
    print(f"\n1. Created dataset: {len(data)} rows, {len(data[0])} columns")
    print(f"   Columns: {list(data[0].keys())}")
    
    writer = CFFWriter('demo_selective.cff')
    writer.write(data)
    print("   ✓ Written to demo_selective.cff")
    
    print("\n2. Reading ONLY 'name' and 'salary' columns...")
    reader = CFFReader('demo_selective.cff')
    
    start = time.perf_counter()
    selected_columns = reader.read_columns(['name', 'salary'])
    elapsed = time.perf_counter() - start
    
    print(f"   ✓ Read {len(selected_columns['name'])} values in {elapsed*1000:.2f}ms")
    print(f"   ✓ Skipped reading: id, age, city")
    
    print("\n3. First 3 results:")
    for i in range(3):
        name = selected_columns['name'][i]
        salary = selected_columns['salary'][i]
        print(f"   {name}: ${salary:,.2f}")


def demo_compression():
    """Demonstrate compression benefits"""
    print("\n" + "=" * 70)
    print("DEMO 3: Compression Analysis")
    print("=" * 70)
    
    import os
    
    # Create repetitive data (compresses well)
    data = [
        {'category': 'A', 'value': i % 10, 'description': 'Test' * 10}
        for i in range(1000)
    ]
    
    print(f"\n1. Created dataset: {len(data)} rows (with repetitive data)")
    
    writer = CFFWriter('demo_compression.cff')
    writer.write(data)
    
    reader = CFFReader('demo_compression.cff')
    file_size = os.path.getsize('demo_compression.cff')
    
    print(f"   ✓ Written to demo_compression.cff")
    print(f"   File size: {file_size:,} bytes")
    
    print("\n2. Compression details per column:")
    for col in reader.columns_metadata:
        ratio = (1 - col.compressed_size / col.uncompressed_size) * 100
        print(f"   {col.name}:")
        print(f"      Uncompressed: {col.uncompressed_size:,} bytes")
        print(f"      Compressed:   {col.compressed_size:,} bytes")
        print(f"      Ratio:        {ratio:.1f}% reduction")


def demo_performance():
    """Demonstrate performance advantage for selective reads"""
    print("\n" + "=" * 70)
    print("DEMO 4: Performance Comparison")
    print("=" * 70)
    
    import csv
    
    # Create a wide table
    num_rows = 1000
    num_columns = 20
    
    data = []
    for i in range(num_rows):
        row = {f'col_{j}': i * j for j in range(num_columns)}
        data.append(row)
    
    print(f"\n1. Created dataset: {num_rows} rows × {num_columns} columns")
    
    # Write to CFF
    writer = CFFWriter('demo_performance.cff')
    writer.write(data)
    
    # Write to CSV
    csv_file = 'demo_performance.csv'
    with open(csv_file, 'w', newline='') as f:
        writer_csv = csv.DictWriter(f, fieldnames=[f'col_{j}' for j in range(num_columns)])
        writer_csv.writeheader()
        writer_csv.writerows(data)
    
    print("   ✓ Written to both CFF and CSV formats")
    
    # Benchmark reading single column from CSV
    print("\n2. Reading SINGLE column (col_5) from CSV...")
    num_runs = 50
    csv_times = []
    for _ in range(num_runs):
        start = time.perf_counter()
        values = []
        with open(csv_file, 'r') as f:
            reader_csv = csv.DictReader(f)
            for row in reader_csv:
                values.append(row['col_5'])
        elapsed = time.perf_counter() - start
        csv_times.append(elapsed)
    
    avg_csv_time = sum(csv_times) / len(csv_times)
    print(f"   Average time: {avg_csv_time * 1000:.3f}ms")
    
    # Benchmark reading single column from CFF
    print("\n3. Reading SINGLE column (col_5) from CFF...")
    reader = CFFReader('demo_performance.cff')
    cff_times = []
    for _ in range(num_runs):
        start = time.perf_counter()
        columns = reader.read_columns(['col_5'])
        elapsed = time.perf_counter() - start
        cff_times.append(elapsed)
    
    avg_cff_time = sum(cff_times) / len(cff_times)
    print(f"   Average time: {avg_cff_time * 1000:.3f}ms")
    
    speedup = avg_csv_time / avg_cff_time
    print(f"\n4. Result: CFF is {speedup:.2f}x faster for single column read!")
    print(f"   (Skipped reading {num_columns - 1} unnecessary columns)")


def cleanup_demo_files():
    """Clean up demo files"""
    import os
    demo_files = [
        'demo_basic.cff', 'demo_selective.cff', 'demo_compression.cff',
        'demo_performance.cff', 'demo_performance.csv'
    ]
    for file in demo_files:
        if os.path.exists(file):
            os.remove(file)


def main():
    print("\n" + "=" * 70)
    print("Columnar File Format (CFF) - Interactive Demo")
    print("=" * 70)
    print("\nThis demo showcases the key features of the CFF format:")
    print("  • Binary columnar storage")
    print("  • Compression per column")
    print("  • Selective column reads (column pruning)")
    print("  • Performance advantages for analytics")
    
    input("\nPress Enter to start the demo...")
    
    try:
        demo_basic_usage()
        input("\nPress Enter to continue to next demo...")
        
        demo_selective_read()
        input("\nPress Enter to continue to next demo...")
        
        demo_compression()
        input("\nPress Enter to continue to next demo...")
        
        demo_performance()
        
        print("\n" + "=" * 70)
        print("Demo Complete!")
        print("=" * 70)
        print("\nKey Takeaways:")
        print("  ✓ CFF preserves data integrity (round-trip conversion works)")
        print("  ✓ Selective column reads skip unnecessary data")
        print("  ✓ Compression reduces file size")
        print("  ✓ Significant performance advantage for analytical queries")
        print("\nFor more information, see:")
        print("  • SPEC.md - Binary format specification")
        print("  • README.md - Usage guide and examples")
        
    finally:
        print("\n" + "=" * 70)
        cleanup = input("Clean up demo files? (y/n): ")
        if cleanup.lower() == 'y':
            cleanup_demo_files()
            print("✓ Demo files cleaned up")
        else:
            print("Demo files preserved for inspection")


if __name__ == '__main__':
    main()
