from pathlib import Path

TABLE_DIR = Path("data/interim/tables")

for path in TABLE_DIR.glob("*.sql"):
    data = path.read_bytes()

    if data.endswith(b")COMMIT;\n"):
        path.write_bytes(
            data[:-len(b")COMMIT;\n")]
            + b");\nCOMMIT;\n"
        )
        print(f"Fixed: {path.name}")
    else:
        print(f"OK:    {path.name}")