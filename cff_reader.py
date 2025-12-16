"""
CFF Reader Module - Reads data from Columnar File Format

This module provides functionality to parse and read CFF binary files with support
for selective column reads (column pruning).
"""

import struct
import zlib
from typing import List, Dict, Any, Optional, BinaryIO


# Data type codes
TYPE_INT32 = 0x01
TYPE_FLOAT64 = 0x02
TYPE_STRING = 0x03

# Magic number for CFF format
MAGIC_NUMBER = b'CFF1'


class ColumnMetadata:
    """Represents metadata for a single column"""
    def __init__(self, name: str, dtype: int, offset: int, 
                 compressed_size: int, uncompressed_size: int):
        self.name = name
        self.dtype = dtype
        self.offset = offset
        self.compressed_size = compressed_size
        self.uncompressed_size = uncompressed_size
    
    def __repr__(self):
        type_names = {TYPE_INT32: 'INT32', TYPE_FLOAT64: 'FLOAT64', TYPE_STRING: 'STRING'}
        return (f"Column(name={self.name}, type={type_names.get(self.dtype, 'UNKNOWN')}, "
                f"offset={self.offset}, compressed={self.compressed_size}, "
                f"uncompressed={self.uncompressed_size})")


class CFFReader:
    """Reader for Columnar File Format"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.num_rows = 0
        self.columns_metadata = []
        self._read_header()
    
    def _read_header(self):
        """Read and parse the CFF header"""
        with open(self.file_path, 'rb') as f:
            # Read magic number
            magic = f.read(4)
            if magic != MAGIC_NUMBER:
                raise ValueError(f"Invalid magic number. Expected {MAGIC_NUMBER}, got {magic}")
            
            # Read version
            version = struct.unpack('<I', f.read(4))[0]
            if version != 1:
                raise ValueError(f"Unsupported format version: {version}")
            
            # Read number of rows
            self.num_rows = struct.unpack('<Q', f.read(8))[0]
            
            # Read number of columns
            num_columns = struct.unpack('<I', f.read(4))[0]
            
            # Read column metadata
            for _ in range(num_columns):
                # Column name
                name_length = struct.unpack('<I', f.read(4))[0]
                name = f.read(name_length).decode('utf-8')
                
                # Data type
                dtype = struct.unpack('<B', f.read(1))[0]
                
                # Offset, compressed size, uncompressed size
                offset = struct.unpack('<Q', f.read(8))[0]
                compressed_size = struct.unpack('<Q', f.read(8))[0]
                uncompressed_size = struct.unpack('<Q', f.read(8))[0]
                
                col_meta = ColumnMetadata(
                    name=name,
                    dtype=dtype,
                    offset=offset,
                    compressed_size=compressed_size,
                    uncompressed_size=uncompressed_size
                )
                self.columns_metadata.append(col_meta)
    
    def get_column_names(self) -> List[str]:
        """Get list of all column names"""
        return [col.name for col in self.columns_metadata]
    
    def get_schema(self) -> Dict[str, str]:
        """Get schema as dictionary mapping column names to type names"""
        type_names = {TYPE_INT32: 'INT32', TYPE_FLOAT64: 'FLOAT64', TYPE_STRING: 'STRING'}
        return {col.name: type_names.get(col.dtype, 'UNKNOWN') 
                for col in self.columns_metadata}
    
    def _read_column_data(self, col_meta: ColumnMetadata) -> bytes:
        """Read and decompress data for a specific column"""
        with open(self.file_path, 'rb') as f:
            # Seek to column data
            f.seek(col_meta.offset)
            
            # Read compressed data
            compressed_data = f.read(col_meta.compressed_size)
            
            # Decompress
            uncompressed_data = zlib.decompress(compressed_data)
            
            # Verify size
            if len(uncompressed_data) != col_meta.uncompressed_size:
                raise ValueError(
                    f"Decompressed size mismatch for column {col_meta.name}. "
                    f"Expected {col_meta.uncompressed_size}, got {len(uncompressed_data)}"
                )
            
            return uncompressed_data
    
    def _deserialize_int32_column(self, data: bytes) -> List[int]:
        """Deserialize INT32 column data"""
        values = []
        for i in range(0, len(data), 4):
            val = struct.unpack('<i', data[i:i+4])[0]
            values.append(val)
        return values
    
    def _deserialize_float64_column(self, data: bytes) -> List[float]:
        """Deserialize FLOAT64 column data"""
        values = []
        for i in range(0, len(data), 8):
            val = struct.unpack('<d', data[i:i+8])[0]
            values.append(val)
        return values
    
    def _deserialize_string_column(self, data: bytes) -> List[str]:
        """Deserialize STRING column data using offset-based encoding"""
        # Read offset array
        # Number of offsets = num_rows + 1
        offset_array_size = (self.num_rows + 1) * 4
        offset_data = data[:offset_array_size]
        string_data = data[offset_array_size:]
        
        # Parse offsets
        offsets = []
        for i in range(0, offset_array_size, 4):
            offset = struct.unpack('<I', offset_data[i:i+4])[0]
            offsets.append(offset)
        
        # Extract strings using offsets
        values = []
        for i in range(len(offsets) - 1):
            start = offsets[i]
            end = offsets[i + 1]
            string_bytes = string_data[start:end]
            string_val = string_bytes.decode('utf-8')
            values.append(string_val)
        
        return values
    
    def _deserialize_column(self, col_meta: ColumnMetadata, data: bytes) -> List[Any]:
        """Deserialize column data based on its type"""
        if col_meta.dtype == TYPE_INT32:
            return self._deserialize_int32_column(data)
        elif col_meta.dtype == TYPE_FLOAT64:
            return self._deserialize_float64_column(data)
        elif col_meta.dtype == TYPE_STRING:
            return self._deserialize_string_column(data)
        else:
            raise ValueError(f"Unknown data type: {col_meta.dtype}")
    
    def read_columns(self, column_names: Optional[List[str]] = None) -> Dict[str, List[Any]]:
        """
        Read specified columns from the file
        
        Args:
            column_names: List of column names to read. If None, reads all columns.
        
        Returns:
            Dictionary mapping column names to lists of values
        """
        if column_names is None:
            column_names = self.get_column_names()
        
        # Validate column names
        available_columns = set(self.get_column_names())
        for col_name in column_names:
            if col_name not in available_columns:
                raise ValueError(f"Column '{col_name}' not found in file")
        
        # Read only the requested columns
        result = {}
        for col_meta in self.columns_metadata:
            if col_meta.name in column_names:
                # Read and decompress column data
                data = self._read_column_data(col_meta)
                
                # Deserialize
                values = self._deserialize_column(col_meta, data)
                result[col_meta.name] = values
        
        return result
    
    def read(self) -> List[Dict[str, Any]]:
        """
        Read all data from the file
        
        Returns:
            List of dictionaries representing rows
        """
        # Read all columns
        columns_data = self.read_columns()
        
        # Convert to row format
        rows = []
        for i in range(self.num_rows):
            row = {col_name: columns_data[col_name][i] 
                   for col_name in columns_data.keys()}
            rows.append(row)
        
        return rows
    
    def info(self) -> str:
        """Get information about the file"""
        lines = [
            f"CFF File: {self.file_path}",
            f"Rows: {self.num_rows}",
            f"Columns: {len(self.columns_metadata)}",
            "",
            "Schema:"
        ]
        for col in self.columns_metadata:
            lines.append(f"  {col}")
        
        return "\n".join(lines)
