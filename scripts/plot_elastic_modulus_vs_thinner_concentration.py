import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from matplotlib.patches import Patch

# Keep text editable in the exported SVG
plt.rcParams["svg.fonttype"] = "none"

# ------------------------------------------------
# Load phantom data from CSV (Table 1)
# ------------------------------------------------
CSV_PATH = "data/processed/phantoms_table.csv"

PHANTOMS = []
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        label = row["sample_label"].strip()
        family = label.split("_")[0]

        # Handle labels like EF10_12.5T or EF10_12_5T
        thinner_str = label.split("_")[1].replace("T", "").replace("_", ".")
        thinner_pct = float(thinner_str)

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
    d["interp"] = PchipInterpolator(d["t"], d["E"], extrapolate=False)
    d["tmin"], d["tmax"] = d["t"].min(), d["t"].max()

# ------------------------------------------------
# Plot
# ------------------------------------------------
plt.figure(figsize=(9, 6))

t_meas = np.array([p[2] for p in PHANTOMS])
E_meas = np.array([p[3] for p in PHANTOMS])

# Elastic modulus levels separating experimentally validated regions
levels = sorted([111.10, 97.26, 73.18, 54.21])

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

# Plot family-wise monotonic interpolations
for fam in ["EF50", "EF30", "EF10"]:
    d = families.get(fam)
    if d and len(d["t"]) > 1:
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
