#!/usr/bin/env python3
"""
Performance Benchmark

Compares the performance of reading a single column from CFF vs CSV.
"""

import csv
import time
import sys
from cff_writer import CFFWriter
from cff_reader import CFFReader


def benchmark_csv_column_read(csv_path, column_name, num_runs=10):
    """Benchmark reading a single column from CSV"""
    times = []
    
    for _ in range(num_runs):
        start = time.perf_counter()
        
        values = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                values.append(row[column_name])
        
        end = time.perf_counter()
        times.append(end - start)
    
    avg_time = sum(times) / len(times)
    return avg_time, len(values)


def benchmark_cff_column_read(cff_path, column_name, num_runs=10):
    """Benchmark reading a single column from CFF"""
    times = []
    
    # Create reader once
    reader = CFFReader(cff_path)
    
    for _ in range(num_runs):
        start = time.perf_counter()
        
        columns_data = reader.read_columns([column_name])
        values = columns_data[column_name]
        
        end = time.perf_counter()
        times.append(end - start)
    
    avg_time = sum(times) / len(times)
    return avg_time, len(values)


def generate_large_csv(path, num_rows=10000):
    """Generate a larger CSV file for benchmarking"""
    print(f"Generating test CSV with {num_rows} rows...")
    
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'age', 'salary', 'department', 'city', 'country'])
        
        departments = ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance']
        cities = ['New York', 'San Francisco', 'London', 'Tokyo', 'Sydney']
        countries = ['USA', 'USA', 'UK', 'Japan', 'Australia']
        
        for i in range(num_rows):
            dept_idx = i % len(departments)
            writer.writerow([
                i + 1,
                f'Person_{i}',
                25 + (i % 40),
                50000.0 + (i * 100.5),
                departments[dept_idx],
                cities[dept_idx],
                countries[dept_idx]
            ])
    
    print(f"✓ Generated {path}")


def main():
    """Run performance benchmarks"""
    print("=" * 60)
    print("CFF Performance Benchmark")
    print("=" * 60)
    
    # Generate test data
    csv_path = 'test_data/benchmark.csv'
    cff_path = 'test_data/benchmark.cff'
    
    generate_large_csv(csv_path, num_rows=10000)
    
    # Convert to CFF
    print("\nConverting CSV to CFF...")
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
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
    
    writer = CFFWriter(cff_path)
    writer.write(data)
    print(f"✓ Created {cff_path}")
    
    # Benchmark single column read
    print("\n" + "=" * 60)
    print("Benchmark: Reading single column 'salary'")
    print("=" * 60)
    
    column_name = 'salary'
    num_runs = 100
    
    print(f"\nRunning {num_runs} iterations...")
    
    # CSV benchmark
    csv_time, csv_count = benchmark_csv_column_read(csv_path, column_name, num_runs)
    print(f"\nCSV column read:")
    print(f"  Average time: {csv_time * 1000:.3f} ms")
    print(f"  Values read: {csv_count}")
    
    # CFF benchmark
    cff_time, cff_count = benchmark_cff_column_read(cff_path, column_name, num_runs)
    print(f"\nCFF column read (selective):")
    print(f"  Average time: {cff_time * 1000:.3f} ms")
    print(f"  Values read: {cff_count}")
    
    # Comparison
    speedup = csv_time / cff_time
    print(f"\n" + "=" * 60)
    print(f"CFF is {speedup:.2f}x faster than CSV for single column read")
    print("=" * 60)
    
    # Benchmark full read
    print("\n" + "=" * 60)
    print("Benchmark: Reading all columns")
    print("=" * 60)
    
    print(f"\nRunning {num_runs} iterations...")
    
    # CSV full read
    csv_times = []
    for _ in range(num_runs):
        start = time.perf_counter()
        data = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(dict(row))
        end = time.perf_counter()
        csv_times.append(end - start)
    
    csv_full_time = sum(csv_times) / len(csv_times)
    print(f"\nCSV full read:")
    print(f"  Average time: {csv_full_time * 1000:.3f} ms")
    
    # CFF full read
    cff_times = []
    for _ in range(num_runs):
        reader = CFFReader(cff_path)
        start = time.perf_counter()
        data = reader.read()
        end = time.perf_counter()
        cff_times.append(end - start)
    
    cff_full_time = sum(cff_times) / len(cff_times)
    print(f"\nCFF full read:")
    print(f"  Average time: {cff_full_time * 1000:.3f} ms")
    
    full_speedup = csv_full_time / cff_full_time
    print(f"\n" + "=" * 60)
    if full_speedup > 1:
        print(f"CFF is {full_speedup:.2f}x faster than CSV for full read")
    else:
        print(f"CSV is {1/full_speedup:.2f}x faster than CFF for full read")
    print("=" * 60)
    
    print("\nNote: CFF's advantage is most apparent in selective column reads,")
    print("where it can skip decompressing and parsing unneeded columns.")


if __name__ == '__main__':
    main()
