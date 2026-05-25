import sys
import csv
import os
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")          # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "results_raw.csv"
OUT_DIR    = "plots"
os.makedirs(OUT_DIR, exist_ok=True)


# Carregamento dos dados do CSV
rows = []
with open(INPUT_FILE, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append({
            "p":         int(row["p"]),
            "func":      row["func"],
            "n":         int(row["n"]),
            "T_compute": float(row["T_compute"]),
        })

groups = defaultdict(list)
for r in rows:
    groups[(r["func"], r["n"])].append(r)
for key in groups:
    groups[key].sort(key=lambda x: x["p"])


# Curvas da Lei de Amdahl para referência                                        
# Assumindo serial fraction s = 0.01, 0.05, 0.10                         

def amdahl(p, s):
    return 1.0 / (s + (1.0 - s) / p)

STYLE = {
    "font.family":  "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":    True,
    "grid.alpha":   0.35,
}


for (func, n), data in sorted(groups.items()):
    serial_rows = [r for r in data if r["p"] == 1]
    if not serial_rows:
        continue
    T_s = serial_rows[0]["T_compute"]

    procs = [r["p"]         for r in data]
    Sp    = [T_s / r["T_compute"] for r in data]
    Ep    = [sp / p for sp, p in zip(Sp, procs)]

    slug = f"{func.replace('/', '_').replace('^','').replace('(','').replace(')','')}_n{n}"

    # Speedup plot
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(6, 4.5))

        # Amdahl reference lines
        p_range = range(1, max(procs) + 1)
        for s, ls in [(0.01, "--"), (0.05, ":"), (0.10, "-.")]:
            ax.plot(list(p_range),
                    [amdahl(p, s) for p in p_range],
                    color="gray", linestyle=ls, linewidth=1,
                    label=f"Amdahl s={s:.0%}")

        # Ideal
        ax.plot(list(p_range), list(p_range),
                color="silver", linestyle="-", linewidth=1, label="Ideal")

        # Measured
        ax.plot(procs, Sp, "o-", color="#1f77b4",
                linewidth=2, markersize=7, label="Measured")

        ax.set_xlabel("Number of processes (p)")
        ax.set_ylabel("Speedup  $S_p = T_s / T_p$")
        ax.set_title(f"Speedup — {func}  (n = {n:,})")
        ax.set_xticks(procs)
        ax.legend(fontsize=8)
        fig.tight_layout()
        path = os.path.join(OUT_DIR, f"speedup_{slug}.png")
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"  Saved: {path}")

    # Efficiency plot
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(6, 4.5))

        ax.axhline(1.0, color="silver", linestyle="-",
                   linewidth=1, label="Ideal (E=1)")
        ax.axhline(0.7, color="orange", linestyle="--",
                   linewidth=1, label="70 % threshold")

        ax.plot(procs, Ep, "s-", color="#d62728",
                linewidth=2, markersize=7, label="Measured")

        ax.set_ylim(0, 1.15)
        ax.set_xlabel("Number of processes (p)")
        ax.set_ylabel("Efficiency  $E_p = S_p / p$")
        ax.set_title(f"Efficiency — {func}  (n = {n:,})")
        ax.set_xticks(procs)
        ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
        ax.legend(fontsize=8)
        fig.tight_layout()
        path = os.path.join(OUT_DIR, f"efficiency_{slug}.png")
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"  Saved: {path}")

print("\nAll plots saved in:", OUT_DIR)
