"""
CFF Writer Module - Writes data in Columnar File Format

This module provides functionality to serialize tabular data into the CFF binary format
with column-wise storage and zlib compression.
"""

import struct
import zlib
from typing import List, Dict, Any, BinaryIO


# Data type codes
TYPE_INT32 = 0x01
TYPE_FLOAT64 = 0x02
TYPE_STRING = 0x03

# Magic number for CFF format
MAGIC_NUMBER = b'CFF1'
FORMAT_VERSION = 1


class ColumnMetadata:
    """Represents metadata for a single column"""
    def __init__(self, name: str, dtype: int, offset: int = 0, 
                 compressed_size: int = 0, uncompressed_size: int = 0):
        self.name = name
        self.dtype = dtype
        self.offset = offset
        self.compressed_size = compressed_size
        self.uncompressed_size = uncompressed_size


class CFFWriter:
    """Writer for Columnar File Format"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.columns = []
        self.num_rows = 0
        
    def infer_type(self, value: Any) -> int:
        """Infer the CFF data type from a Python value"""
        if isinstance(value, bool):
            # Treat booleans as integers (True=1, False=0)
            return TYPE_INT32
        elif isinstance(value, int):
            return TYPE_INT32
        elif isinstance(value, float):
            return TYPE_FLOAT64
        elif isinstance(value, str):
            return TYPE_STRING
        else:
            # Default to string for unknown types
            return TYPE_STRING
    
    def serialize_int32_column(self, values: List[int]) -> bytes:
        """Serialize a column of INT32 values"""
        buffer = bytearray()
        for val in values:
            buffer.extend(struct.pack('<i', int(val)))
        return bytes(buffer)
    
    def serialize_float64_column(self, values: List[float]) -> bytes:
        """Serialize a column of FLOAT64 values"""
        buffer = bytearray()
        for val in values:
            buffer.extend(struct.pack('<d', float(val)))
        return bytes(buffer)
    
    def serialize_string_column(self, values: List[str]) -> bytes:
        """Serialize a column of STRING values using offset-based encoding"""
        buffer = bytearray()
        
        # Build offset array and concatenate strings
        offsets = [0]
        string_data = bytearray()
        
        for val in values:
            string_bytes = str(val).encode('utf-8')
            string_data.extend(string_bytes)
            offsets.append(len(string_data))
        
        # Write offset array (N+1 offsets for N strings)
        for offset in offsets:
            buffer.extend(struct.pack('<I', offset))
        
        # Write concatenated string data
        buffer.extend(string_data)
        
        return bytes(buffer)
    
    def serialize_column(self, values: List[Any], dtype: int) -> bytes:
        """Serialize a column based on its data type"""
        if dtype == TYPE_INT32:
            return self.serialize_int32_column(values)
        elif dtype == TYPE_FLOAT64:
            return self.serialize_float64_column(values)
        elif dtype == TYPE_STRING:
            return self.serialize_string_column(values)
        else:
            raise ValueError(f"Unknown data type: {dtype}")
    
    def compress_column(self, data: bytes) -> bytes:
        """Compress column data using zlib"""
        return zlib.compress(data, level=6)
    
    def write_header(self, f: BinaryIO, columns_metadata: List[ColumnMetadata]):
        """Write the CFF header"""
        # Magic number
        f.write(MAGIC_NUMBER)
        
        # Version
        f.write(struct.pack('<I', FORMAT_VERSION))
        
        # Number of rows
        f.write(struct.pack('<Q', self.num_rows))
        
        # Number of columns
        f.write(struct.pack('<I', len(columns_metadata)))
        
        # Write column metadata
        for col_meta in columns_metadata:
            # Column name length and name
            name_bytes = col_meta.name.encode('utf-8')
            f.write(struct.pack('<I', len(name_bytes)))
            f.write(name_bytes)
            
            # Data type
            f.write(struct.pack('<B', col_meta.dtype))
            
            # Offset, compressed size, uncompressed size
            f.write(struct.pack('<Q', col_meta.offset))
            f.write(struct.pack('<Q', col_meta.compressed_size))
            f.write(struct.pack('<Q', col_meta.uncompressed_size))
    
    def write(self, data: List[Dict[str, Any]]):
        """
        Write tabular data to CFF format
        
        Args:
            data: List of dictionaries representing rows
        """
        if not data:
            raise ValueError("Cannot write empty data")
        
        self.num_rows = len(data)
        
        # Get column names from first row
        column_names = list(data[0].keys())
        
        # Organize data by columns and infer types
        columns_data = {}
        column_types = {}
        
        for col_name in column_names:
            col_values = [row[col_name] for row in data]
            columns_data[col_name] = col_values
            
            # Infer type from first non-None value
            for val in col_values:
                if val is not None and val != '':
                    column_types[col_name] = self.infer_type(val)
                    break
            else:
                # All values are None/empty, default to STRING
                column_types[col_name] = TYPE_STRING
        
        # Serialize and compress each column
        compressed_columns = []
        columns_metadata = []
        
        for col_name in column_names:
            dtype = column_types[col_name]
            values = columns_data[col_name]
            
            # Serialize
            uncompressed_data = self.serialize_column(values, dtype)
            uncompressed_size = len(uncompressed_data)
            
            # Compress
            compressed_data = self.compress_column(uncompressed_data)
            compressed_size = len(compressed_data)
            
            compressed_columns.append(compressed_data)
            
            # Create metadata (offset will be calculated later)
            col_meta = ColumnMetadata(
                name=col_name,
                dtype=dtype,
                offset=0,  # Will be calculated
                compressed_size=compressed_size,
                uncompressed_size=uncompressed_size
            )
            columns_metadata.append(col_meta)
        
        # Calculate header size to determine column offsets
        header_size = 4 + 4 + 8 + 4  # magic + version + num_rows + num_cols
        for col_meta in columns_metadata:
            name_bytes = col_meta.name.encode('utf-8')
            header_size += 4 + len(name_bytes) + 1 + 8 + 8 + 8
        
        # Calculate offsets
        current_offset = header_size
        for i, col_meta in enumerate(columns_metadata):
            col_meta.offset = current_offset
            current_offset += col_meta.compressed_size
        
        # Write to file
        with open(self.file_path, 'wb') as f:
            # Write header
            self.write_header(f, columns_metadata)
            
            # Write compressed column blocks
            for compressed_data in compressed_columns:
                f.write(compressed_data)
    
    def write_from_columns(self, columns: Dict[str, List[Any]], 
                          column_types: Dict[str, int] = None):
        """
        Write data organized as columns
        
        Args:
            columns: Dictionary mapping column names to lists of values
            column_types: Optional dictionary mapping column names to type codes
        """
        if not columns:
            raise ValueError("Cannot write empty columns")
        
        # Verify all columns have same length
        col_lengths = [len(values) for values in columns.values()]
        if len(set(col_lengths)) != 1:
            raise ValueError("All columns must have the same length")
        
        self.num_rows = col_lengths[0]
        
        # Convert to list of dicts format
        column_names = list(columns.keys())
        data = []
        for i in range(self.num_rows):
            row = {col_name: columns[col_name][i] for col_name in column_names}
            data.append(row)
        
        self.write(data)
