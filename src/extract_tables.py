# src/extract_tables.py
import re
from pathlib import Path

SRC = Path("data/Cafeteria Order Data.sql")
OUT = Path("data/interim/tables")
OUT.mkdir(parents=True, exist_ok=True)

WANT = {"branches", "counters", "dishes", "categories",
        "orders", "order_details", "order_has_statuses"}
HEADER = b"SET NAMES utf8mb4; SET time_zone='+00:00'; SET foreign_key_checks=0; SET unique_checks=0; SET autocommit=0;\n"
marker = re.compile(rb"^-- Table structure for table `(\w+)`")

done, cur, fh = set(), None, None
with open(SRC, "rb") as f:
    for i, line in enumerate(f, 1):
        m = marker.match(line)
        if m:
            if fh:
                fh.write(b"COMMIT;\n"); fh.close(); fh = None
            cur = m.group(1).decode()
            if cur in WANT:
                fh = open(OUT / f"{cur}.sql", "wb"); fh.write(HEADER)
                done.add(cur); print(f"line {i}: extracting {cur}", flush=True)
            elif done == WANT:
                break
        if fh:
            fh.write(line)
    if fh:
        fh.write(b"COMMIT;\n"); fh.close()