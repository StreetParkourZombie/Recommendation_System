"""ratings.csv (678 MB) -> parquet bang pyarrow streaming (khong dung Spark, tranh winutils)."""
import os, io, sys, time, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

SRC = r"D:\recsys_data\raw\ml-25m\ratings.csv"
DST = r"D:\recsys_data\parquet\ratings"
TMP = r"D:\recsys_data\spark_tmp"

os.makedirs(DST, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

# PyArrow ParquetWriter can ONLY write a single file, Spark can ONLY read a directory.
# -> write to <DST>/part-00000.parquet, Spark reads the directory.
OUT_FILE = os.path.join(DST, "part-00000.parquet")
for f in os.listdir(DST):
    try:
        os.remove(os.path.join(DST, f))
    except OSError:
        pass

schema = pa.schema([
    pa.field("userId", pa.int32()),
    pa.field("movieId", pa.int32()),
    pa.field("rating", pa.float32()),
    pa.field("timestamp", pa.int32()),
])

t0 = time.time()
convert_opts = pacsv.ConvertOptions(column_types={
    "userId": pa.int32(), "movieId": pa.int32(),
    "rating": pa.float32(), "timestamp": pa.int32()})
read_opts = pacsv.ReadOptions(block_size=64 << 20)   # 64 MB/chunk
w = pq.ParquetWriter(OUT_FILE, schema, compression="snappy")

reader = pacsv.open_csv(SRC, read_options=read_opts, convert_options=convert_opts)
total = 0
batch_n = 0
for batch in reader:
    w.write_table(pa.Table.from_batches([batch]))
    total += batch.num_rows
    batch_n += 1
    if batch_n % 20 == 0:
        print("  %d rows, %.0fs" % (total, time.time() - t0), flush=True)
w.close()
print("TOTAL rows:", total, "in %.0fs" % (time.time() - t0), flush=True)

# verify
t = pq.read_table(DST)
print("verify rows:", t.num_rows, "cols:", t.column_names)
print("schema:", t.schema)
meta = pq.ParquetFile(OUT_FILE)
print("row groups:", meta.num_row_groups, "size MB:", round(os.path.getsize(OUT_FILE) / 1e6, 1))

# checksum for reproducibility
import hashlib
h = hashlib.sha256()
for f in sorted(os.listdir(DST)):
    h.update(f.encode())
    with open(os.path.join(DST, f), "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
print("PARQUET_SHA256:", h.hexdigest())
with open(os.path.join(os.path.dirname(DST), "ratings.parquet.sha256"), "w", encoding="utf-8") as f:
    f.write(h.hexdigest() + "  ratings/\n")
print("DONE")
