import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from google.colab import files
from matplotlib.patches import Patch

# Keep text editable in the exported SVG
plt.rcParams["svg.fonttype"] = "none"

# Phantom dataset: (label, family, thinner %, elastic modulus in kPa)
PHANTOMS = [
    ("EF50_0T",    "EF50", 0.0,   152.70),
    ("EF50_12.5T", "EF50", 12.5,  111.10),
    ("EF30_0T",    "EF30", 0.0,    97.26),
    ("EF30_12.5T", "EF30", 12.5,   73.18),
    ("EF10_0T",    "EF10", 0.0,    54.21),
    ("EF10_12.5T", "EF10", 12.5,   37.30),
    ("EF10_25T",   "EF10", 25.0,   27.39),
    ("EF10_37.5T", "EF10", 37.5,   19.37),
    ("EF10_50T",   "EF10", 50.0,   15.52),
    ("EF10_62.5T", "EF10", 62.5,   12.17),
    ("EF10_75T",   "EF10", 75.0,    8.81),
    ("EF10_87.5T", "EF10", 87.5,    7.92),
    ("EF10_100T",  "EF10", 100.0,   5.42),
]

# Organise data by silicone family for interpolation
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

# --- Plot setup ---
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

# Save and download the figure
out_path = "Inverse_with_gap_shading.svg"
plt.savefig(out_path, format="svg", bbox_inches="tight")
plt.show()
files.download(out_path)
