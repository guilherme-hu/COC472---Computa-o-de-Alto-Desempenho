import sys
import csv
import statistics
from collections import defaultdict


INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "results_raw.csv"

rows = []
with open(INPUT_FILE, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append({
            "p":          int(row["p"]),
            "func":       row["func"],
            "n":          int(row["n"]),
            "result":     float(row["result"]),
            "T_total":    float(row["T_total"]),
            "T_compute":  float(row["T_compute"]),
        })

# Agrupar por (func, n)
groups = defaultdict(list)
for r in rows:
    groups[(r["func"], r["n"])].append(r)

for key in groups:
    groups[key].sort(key=lambda x: x["p"])


# Print da análise 

SEP = "-" * 75

for (func, n), data in sorted(groups.items()):
    # T_serial = T_compute quando p=1
    serial_rows = [r for r in data if r["p"] == 1]
    if not serial_rows:
        print(f"WARNING: no p=1 row for func={func} n={n}, skipping.")
        continue
    T_s = serial_rows[0]["T_compute"]

    print(SEP)
    print(f"  Function : {func}")
    print(f"  n        : {n:,}")
    print(f"  T_serial : {T_s:.6f} s")
    print(SEP)
    print(f"  {'p':>4}  {'T_compute':>12}  {'T_total':>12}  "
          f"{'Sp':>8}  {'Ep':>8}  {'result':>18}")
    print(f"  {'--':>4}  {'----------':>12}  {'--------':>12}  "
          f"{'--':>8}  {'--':>8}  {'--':>18}")

    for r in data:
        p   = r["p"]
        Tp  = r["T_compute"]
        Sp  = T_s / Tp if Tp > 0 else float("inf")
        Ep  = Sp / p
        print(f"  {p:>4}  {Tp:>12.6f}  {r['T_total']:>12.6f}  "
              f"{Sp:>8.3f}  {Ep:>8.3f}  {r['result']:>18.10f}")

    print()

print("Done.")
