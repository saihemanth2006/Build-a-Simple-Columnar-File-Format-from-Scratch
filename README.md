# Columnar File Format (CFF) – my attempt at a column store

Hi! I wanted to learn how columnar file formats actually work, so I tried building a tiny one. It is not meant to beat Parquet or ORC; I just wanted to see the pieces fit together. It writes data by column, compresses each column with zlib, and can read back only the columns you ask for.

## What it does (and what it does not)
- Converts CSV -> a small binary format I call CFF
- Supports three types: int32, float64, and UTF-8 strings (strings use an offset array + one blob)
- Compresses every column block with zlib
- Reads everything or only a subset of columns (column pruning)
- No null bitmap yet, so blanks are just blanks

## Quick tour of the repo
```
.
├── SPEC.md          # format notes, probably the most precise doc here
├── README.md        # this chatty overview
├── QUICKSTART.md    # fast instructions
├── cff_writer.py    # writes CFF files
├── cff_reader.py    # reads CFF files (can prune columns)
├── csv_to_custom.py # CLI: CSV -> CFF
├── custom_to_csv.py # CLI: CFF -> CSV
├── inspect_cff.py   # peek at header/hex
├── test_roundtrip.py# CSV -> CFF -> CSV sanity
├── benchmark.py     # quick perf check
└── test_data/       # sample CSVs
```

## How I run things (Python 3.7+, stdlib only)
I kept dependencies to the stdlib: `struct`, `zlib`, `csv`.

```bash
python csv_to_custom.py test_data/sample.csv test_data/sample.cff
python custom_to_csv.py test_data/sample.cff test_data/back.csv --columns name salary
python test_roundtrip.py
python benchmark.py
```

## Little code snippet
Write:
```python
from cff_writer import CFFWriter

rows = [
    {"id": 1, "name": "Alice", "score": 95.5},
    {"id": 2, "name": "Bob", "score": 87.0},
]

writer = CFFWriter("data.cff")
writer.write(rows)
```

Read (full or selective):
```python
from cff_reader import CFFReader

reader = CFFReader("data.cff")
print(reader.get_schema())

all_rows = reader.read()
names_only = reader.read_columns(["name"])
```

## Why bother with columns?
- If you only need a couple columns, you skip reading/decompressing the rest.
- Similar values sit together, so zlib compresses them better than mixed rows.
- The header stores offsets, so seeking is simple math.

## Things that are rough edges
- No nulls yet (I just treat empty strings as empty, numbers are assumed present)
- Only one codec (zlib) and three types
- No statistics or row groups; this is a small learning project

## Tests I actually ran
- `python test_roundtrip.py` — round-trip CSV -> CFF -> CSV
- `python benchmark.py` — on my box CFF was much faster for single-column reads; full reads can be slower because of decompression

## If you want details
The binary layout is written down in [SPEC.md](SPEC.md). The short version: header holds schema and offsets, each column block is zlib-compressed, strings use an offset array plus a big concatenated blob.

## Maybe future work
- Add int64/bool/date
- Null bitmap
- Try a faster codec (lz4/zstd)
- Column stats so readers can skip obvious misses

## Closing note
I made this mostly to understand how columnar storage hangs together. If you spot mistakes or have ideas, I am happy to learn more.