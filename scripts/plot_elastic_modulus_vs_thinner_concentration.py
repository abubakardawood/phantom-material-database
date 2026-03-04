import csv
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from matplotlib.patches import Patch

# Keep text editable in the exported SVG
plt.rcParams["svg.fonttype"] = "none"

# ------------------------------------------------
# Load phantom data from CSV (Table)
# ------------------------------------------------
CSV_PATH = "data/processed/phantoms_table.csv"

def parse_thinner_pct(label: str) -> float:
    """
    Robustly parse thinner percentage from labels like:
      EF10_12_5T, EF10_12.5T, EF50_0T, EF30_25T, EF10_37_5T
    """
    parts = label.strip().split("_")
    if len(parts) < 2:
        raise ValueError(f"Cannot parse thinner% from label: {label}")

    # Most common:
    # EF10_12_5T -> ["EF10","12","5T"]
    # EF10_12.5T -> ["EF10","12.5T"]
    # EF50_0T    -> ["EF50","0T"]
    fam = parts[0]
    rest = label[len(fam) + 1:]  # everything after "EFxx_"

    # Keep only the first "...T" chunk (some labels may have sample suffixes elsewhere)
    m = re.search(r"([0-9]+(?:[._][0-9]+)?)T", rest)
    if m:
        token = m.group(1).replace("_", ".")
        return float(token)

    # Fallback for patterns like "12_5T" where regex above might miss in weird cases
    token = parts[1].replace("T", "").replace("_", ".")
    return float(token)


PHANTOMS = []
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        label = row["sample_label"].strip()
        family = label.split("_")[0]

        thinner_pct = parse_thinner_pct(label)

        E_mean = float(row["elastic_modulus_mean_kPa"])
        PHANTOMS.append((label, family, thinner_pct, E_mean))

# ------------------------------------------------
# Organise data by silicone family for interpolation
# ------------------------------------------------
families = {}
for label, fam, t, E in PHANTOMS:
    families.setdefault(fam, {"t": [], "E": []})
    families[fam]["t"].append(t)
    families[fam]["E"].append(E)

# Sort by thinner concentration and build monotonic interpolators
for fam, d in families.items():
    order = np.argsort(d["t"])
    d["t"] = np.array(d["t"], float)[order]
    d["E"] = np.array(d["E"], float)[order]

    # Only build interpolator if we have enough points
    if len(d["t"]) >= 2:
        d["interp"] = PchipInterpolator(d["t"], d["E"], extrapolate=False)
        d["tmin"], d["tmax"] = float(d["t"].min()), float(d["t"].max())

# ------------------------------------------------
# Plot
# ------------------------------------------------
plt.figure(figsize=(9, 6))

t_meas = np.array([p[2] for p in PHANTOMS], dtype=float)
E_meas = np.array([p[3] for p in PHANTOMS], dtype=float)

# Updated elastic modulus "gap-policy" reference levels (from your new means)
levels = sorted([
    111.09930866645567,   # EF50_12_5T
    97.25997744487732,    # EF30_0T
    73.18310906168253,    # EF30_12_5T
    54.20947752233499     # EF10_0T
])

# Set y-axis limits with a small margin for clarity
ymin = float(E_meas.min())
ymax = float(E_meas.max())
pad = 0.05 * (ymax - ymin)
ymin_plot = ymin - pad
ymax_plot = ymax + pad
plt.ylim(ymin_plot, ymax_plot)

# Shade alternating horizontal bands to highlight non-validated regions
bounds = [ymin_plot] + levels + [ymax_plot]
for i in range(len(bounds) - 1):
    if i % 2 == 1:
        plt.axhspan(bounds[i], bounds[i + 1], alpha=0.10)

# Draw dotted reference lines at the selected modulus levels
for y in levels:
    plt.axhline(y=y, linestyle=":", linewidth=1.2, alpha=0.8)

# Plot measured phantom data
plt.plot(t_meas, E_meas, "o", label="Measured (phantoms)")

# Plot family-wise monotonic interpolations (all families present)
for fam in sorted(families.keys()):
    d = families[fam]
    if "interp" in d:
        t_fine = np.linspace(d["tmin"], d["tmax"], 300)
        plt.plot(t_fine, d["interp"](t_fine), label=f"{fam} interpolation")

plt.xlabel("Thinner concentration (%)")
plt.ylabel("Elastic modulus (kPa)")
plt.title("Elastic modulus vs thinner concentration")
plt.grid(True, alpha=0.3)

# Add a single legend entry for the shaded gap regions
gap_patch = Patch(alpha=0.10, label="Non-validated gaps")
handles, labels_ = plt.gca().get_legend_handles_labels()
handles.append(gap_patch)
labels_.append("Non-validated gaps")
plt.legend(handles, labels_)

plt.tight_layout()

# ------------------------------------------------
# Save and download safely (Colab / local)
# ------------------------------------------------
out_path = "Inverse_with_gap_shading.svg"
plt.savefig(out_path, format="svg", bbox_inches="tight")
plt.show()

try:
    from google.colab import files
    files.download(out_path)
except Exception:
    print(f"Figure saved to: {out_path}")
