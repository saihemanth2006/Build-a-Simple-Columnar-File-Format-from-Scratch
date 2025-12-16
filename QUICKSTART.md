# Quick Start (short and honest)

I wanted a short page so future-me remembers how to run this. It is pretty bare-bones.

## What you need
- Python 3.7+ (I tested on Python 3.11)
- No extra packages; only stdlib (`struct`, `zlib`, `csv`)

## Fast sanity check
```bash
python test_roundtrip.py          # CSV -> CFF -> CSV
python benchmark.py               # quick perf idea
```
You should see tests pass. Benchmarks will show CFF is faster for single-column reads; full reads might be slower because of decompression.

## CLI I actually use
```bash
# CSV -> CFF
python csv_to_custom.py test_data/sample.csv out.cff

# CFF -> CSV (all columns)
python custom_to_csv.py out.cff back.csv

# CFF -> CSV (only a few columns)
python custom_to_csv.py out.cff back_small.csv --columns name salary

# Peek at header/hex
python inspect_cff.py out.cff --header-only

# Interactive demo (walks through features)
python demo.py
```

## Tiny Python snippets
Write:
```python
from cff_writer import CFFWriter

rows = [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]
writer = CFFWriter("data.cff")
writer.write(rows)
```

Read only what you need:
```python
from cff_reader import CFFReader

reader = CFFReader("data.cff")
names = reader.read_columns(["name"])  # column pruning
```

## If something breaks
- "Invalid magic number" usually means the file is not a CFF file
- Missing column? Check `reader.get_column_names()`
- Slow? Remember CSV might win for tiny full-table reads; CFF shines when you prune columns

## Where to look next
- [SPEC.md](SPEC.md) — actual format layout
- [README.md](README.md) — longer story and caveats

## Repo map (short)
```
SPEC.md        # format notes
README.md      # overview
QUICKSTART.md  # this file
cff_writer.py  # writer
cff_reader.py  # reader
csv_to_custom.py / custom_to_csv.py
inspect_cff.py / test_roundtrip.py / benchmark.py / demo.py
test_data/
```

That is about it. If you try it and it feels rough, it probably is — this was a learning build.
