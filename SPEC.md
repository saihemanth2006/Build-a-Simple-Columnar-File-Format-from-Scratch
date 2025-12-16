# Columnar File Format Specification (CFF)

Version: 1.0 (first pass)

## What this spec is (and is not)
I wrote this while learning how columnar layouts work. It aims to be accurate but it is intentionally simple: one header, one block per column, zlib compression, and a few types. If something seems off, it probably needs fixing — this is my current understanding.

## Design ideas I followed

- Store columns separately so you can skip the ones you do not need
- Compress each column with zlib on its own
- Put offsets in the header so seeking is just math, not scanning
- Keep it small enough to read in one sitting, even if that means fewer features

## File structure (big picture)

```
[HEADER]
[COLUMN_BLOCK_1]
[COLUMN_BLOCK_2]
...
[COLUMN_BLOCK_N]
```

## Header format

The header carries everything the reader needs: schema, row count, and where each column block starts plus its sizes.

### Header layout (variable size)

| Offset | Size (bytes) | Type | Description |
|--------|--------------|------|-------------|
| 0 | 4 | char[4] | Magic Number: "CFF1" (0x43 0x46 0x46 0x31) |
| 4 | 4 | uint32 | Format Version: 1 |
| 8 | 8 | uint64 | Total number of rows |
| 16 | 4 | uint32 | Number of columns (N) |
| 20 | Variable | Column Metadata[N] | Array of column metadata structures |

### Column metadata (variable size per column)

Each column has the following metadata:

| Offset | Size (bytes) | Type | Description |
|--------|--------------|------|-------------|
| 0 | 4 | uint32 | Column name length (L) |
| 4 | L | char[L] | Column name (UTF-8 encoded) |
| 4+L | 1 | uint8 | Data type code (see Data Types section) |
| 5+L | 8 | uint64 | Offset to column data block (from file start) |
| 13+L | 8 | uint64 | Compressed size of column block |
| 21+L | 8 | uint64 | Uncompressed size of column block |

**Total metadata size per column**: 29 + L bytes (where L is column name length)

## Data types

Right now I only handle three basic types:

| Type Code | Type Name | Description | Size |
|-----------|-----------|-------------|------|
| 0x01 | INT32 | 32-bit signed integer | 4 bytes per value |
| 0x02 | FLOAT64 | 64-bit IEEE 754 floating-point | 8 bytes per value |
| 0x03 | STRING | Variable-length UTF-8 string | Variable |

### How values are serialized

#### INT32 (0x01)
- Little-endian 32-bit signed ints
- Uncompressed size: `rows * 4`

#### FLOAT64 (0x02)
- Little-endian IEEE 754 doubles
- Uncompressed size: `rows * 8`

#### STRING (0x03)
- Offset-based layout: one offset array and one big blob of UTF-8 bytes
- Offset array has N+1 uint32s; first is 0, last is total bytes
- Empty strings show up as identical consecutive offsets
- Access: `s[i] = blob[offset[i]:offset[i+1]]`
- Uncompressed size: `(rows + 1) * 4 + total_string_bytes`

## Column block format

Each column block is just the serialized bytes for that column, compressed with zlib.

### Compression

- Algorithm: zlib (DEFLATE), default level
- Each column compressed separately (so you can skip others)

### Column block layout before compression

#### INT32 / FLOAT64
```
[v0][v1][v2]...[vN-1]
```

#### STRING
```
[OFFSET_ARRAY][STRING_DATA]
```
Offsets: N+1 uint32 values. String data: all bytes concatenated. Example for ["hello", "world", ""] => offsets [0,5,10,10], blob "helloworld".

## Reading algorithm (what the reader does)
1) Read header: magic, version, row/column counts, metadata
2) For each requested column: seek to its offset, read compressed bytes, decompress, deserialize
3) Rebuild rows by zipping columns together

## Writing algorithm (how I structured it)
1) Figure out schema and row count
2) Serialize each column according to its type
3) Compress each serialized column with zlib
4) Compute header size, then offsets for each column block
5) Write header, then write column blocks in order

## Tiny layout example

For 3 columns (id:int32, name:string, score:float64) and 2 rows:
```
0     magic "CFF1"
4     version
8     rows
16    column count
20    metadata for each column (names, types, offsets, sizes)
...   column data (compressed blocks), one after another
```

## Validation checklist
- Magic is "CFF1"
- Version == 1
- Column count > 0, row count >= 0
- Offsets stay within file
- Compressed/uncompressed sizes line up
- Type codes are 0x01/0x02/0x03

## Errors to expect
- Wrong magic or version
- Truncated files
- Decompression failure
- Bad UTF-8
- Offsets that point past EOF

## Future extensions I’d like (if time allows)
- More types (int64, bool, date/time)
- Null bitmap
- Dictionary encoding for strings
- Other codecs (lz4, zstd)
- Column stats and maybe row groups
- Checksums

## Notes
- Little-endian for all multi-byte integers
- Strings are UTF-8
- Extension: .cff
- This is for learning, not production
