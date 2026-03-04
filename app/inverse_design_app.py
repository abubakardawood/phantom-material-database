import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq
from matplotlib.patches import Patch


# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Inverse Design Tool", page_icon="🧪", layout="wide")
st.title("Inverse Design Framework (Silicone Phantoms)")
st.caption("Enter a target Young’s modulus (kPa). If multiple Ecoflex series overlap, choose the family.")


# -----------------------------
# Data (UPDATED with EF50_25T + EF30_25T)
# -----------------------------
PHANTOMS = [
    ("EF50_0T",    "EF50", 0.0,   152.70070288580004),
    ("EF50_12_5T", "EF50", 12.5,  111.09930866645567),
    ("EF50_25T",   "EF50", 25.0,   89.49278526799354),

    ("EF30_0T",    "EF30", 0.0,    97.25997744487732),
    ("EF30_12_5T", "EF30", 12.5,   73.18310906168253),
    ("EF30_25T",   "EF30", 25.0,   65.68354113025582),

    ("EF10_0T",    "EF10", 0.0,    54.20947752233499),
    ("EF10_12_5T", "EF10", 12.5,   37.29704827694990),
    ("EF10_25T",   "EF10", 25.0,   27.397220287652036),
    ("EF10_37_5T", "EF10", 37.5,   19.37489905967659),
    ("EF10_50T",   "EF10", 50.0,   15.5213581416756),
    ("EF10_62_5T", "EF10", 62.5,   12.174085251987634),
    ("EF10_75T",   "EF10", 75.0,    8.814412371336129),
    ("EF10_87_5T", "EF10", 87.5,    7.915154597748689),
    ("EF10_100T",  "EF10", 100.0,   5.422521729130547),
]


# -----------------------------
# Build per-family interpolators
# -----------------------------
def build_families(phantoms):
    families = {}
    for label, fam, t, E in phantoms:
        families.setdefault(fam, {"t": [], "E": [], "labels": []})
        families[fam]["t"].append(float(t))
        families[fam]["E"].append(float(E))
        families[fam]["labels"].append(label)

    for fam, d in families.items():
        order = np.argsort(d["t"])
        d["t"] = np.array(d["t"], dtype=float)[order]
        d["E"] = np.array(d["E"], dtype=float)[order]
        d["labels"] = list(np.array(d["labels"], dtype=object)[order])

        if len(d["t"]) >= 2:
            d["interp"] = PchipInterpolator(d["t"], d["E"], extrapolate=False)
            d["tmin"], d["tmax"] = float(d["t"].min()), float(d["t"].max())
            d["Emin"], d["Emax"] = float(d["E"].min()), float(d["E"].max())
    return families


families = build_families(PHANTOMS)

ALL_MEASURED = sorted(
    [(float(E), fam, float(t), label) for (label, fam, t, E) in PHANTOMS],
    key=lambda x: x[0]
)


def invert_family(fam_name, E_target):
    d = families[fam_name]
    f = d["interp"]

    def g(t):
        return float(f(t) - E_target)

    t_star = float(brentq(g, d["tmin"], d["tmax"]))
    E_pred = float(f(t_star))

    j = int(np.argmin(np.abs(d["E"] - E_target)))
    nearest_label = d["labels"][j]
    nearest_E = float(d["E"][j])

    return t_star, E_pred, nearest_label, nearest_E


def nearest_bounds(E_target):
    lower = None
    upper = None
    for E, fam, t, label in ALL_MEASURED:
        if E <= E_target:
            lower = (E, fam, t, label)
        if E >= E_target and upper is None:
            upper = (E, fam, t, label)
    return lower, upper


# -----------------------------
# Layout: controls (left) + plot (right)
# -----------------------------
left, right = st.columns([1, 1.3], gap="large")

with left:
    st.subheader("Inputs")

    E_target = st.number_input(
        "Target Young’s modulus (kPa)",
        min_value=0.0,
        value=50.0,
        step=1.0
    )

    feasible = [
        fam for fam, d in families.items()
        if ("interp" in d) and (d["Emin"] <= E_target <= d["Emax"])
    ]
    feasible = sorted(feasible)

    chosen_fam = None

    if feasible:
        st.success("Covered by validated range.")

        if len(feasible) > 1:
            chosen_fam = st.selectbox(
                "Choose Ecoflex family (overlap detected)",
                feasible,
                index=0
            )
        else:
            chosen_fam = feasible[0]
            st.write(f"Family: **{chosen_fam}**")

        t_star, E_pred, nearest_label, nearest_E = invert_family(chosen_fam, E_target)

        st.subheader("Result")
        st.write(f"**Predicted thinner:** {t_star:.2f} %")
        st.write(f"**Predicted modulus:** {E_pred:.2f} kPa")
        st.write(f"**Nearest measured phantom:** {nearest_label} ({nearest_E:.2f} kPa)")
        st.write(f"**Composition:** {chosen_fam} (A+B) + {t_star:.2f}% thinner (by weight of A+B)")

    else:
        st.error("Gap/out-of-range (no extrapolation).")

        lower, upper = nearest_bounds(E_target)

        st.subheader("Nearest validated bounds")
        if lower:
            E, fam, t, label = lower
            st.write(f"**Lower:** {label} | {fam} | thinner={t:.1f}% | E={E:.2f} kPa")
        else:
            st.write("**Lower:** none (target below minimum measured modulus).")

        if upper:
            E, fam, t, label = upper
            st.write(f"**Upper:** {label} | {fam} | thinner={t:.1f}% | E={E:.2f} kPa")
        else:
            st.write("**Upper:** none (target above maximum measured modulus).")


with right:
    st.subheader("Measured vs interpolation")

    fig, ax = plt.subplots(figsize=(7.5, 5.2))

    # measured points
    t_meas = np.array([p[2] for p in PHANTOMS], dtype=float)
    E_meas = np.array([p[3] for p in PHANTOMS], dtype=float)
    ax.plot(t_meas, E_meas, "o", label="Measured (phantoms)", zorder=3)

    # ---- GAP SHADING (updated + correct) ----
    # Use your updated boundary levels (kPa)
    levels = sorted([
        # 111.09930866645567,  # EF50_12_5T
        # 97.25997744487732,   # EF30_0T
        65.68354113025582,   # EF30_12_5T
        54.20947752233499    # EF10_0T
    ])

    # Make sure shading spans the visible plot region:
    ymin = float(np.min(E_meas))
    ymax = float(np.max(E_meas))
    pad = 0.05 * (ymax - ymin)
    ymin_plot = ymin - pad
    ymax_plot = ymax + pad
    ax.set_ylim(ymin_plot, ymax_plot)

    # Shade the *gaps* (inverse of validated bands)
    # Bands: [ymin, L1], [L1, L2], [L2, L3], [L3, L4], [L4, ymax]
    # We shade i%2==1 to highlight the "gap" bands (as per your earlier request).
    bounds = [ymin_plot] + levels + [ymax_plot]
    for i in range(len(bounds) - 1):
        if i % 2 == 1:  # highlight gap bands
            ax.axhspan(bounds[i], bounds[i + 1], alpha=0.10, zorder=0)

    # Dotted reference lines at the four boundaries
    for y in levels:
        ax.axhline(y=y, linestyle=":", linewidth=1.2, alpha=0.8, zorder=1)

    # interpolated curves
    for fam in sorted(families.keys()):
        d = families[fam]
        if "interp" not in d:
            continue
        t_fine = np.linspace(d["tmin"], d["tmax"], 300)
        ax.plot(t_fine, d["interp"](t_fine), label=f"{fam} interpolation", zorder=2)

    # show target
    # ax.axhline(E_target, linestyle="--", linewidth=1.2, zorder=2)
    

    ax.set_xlabel("Thinner concentration (%)")
    ax.set_ylabel("Elastic modulus (kPa)")
    ax.grid(True, alpha=0.3)

    # Add a legend item for shaded gaps (without changing your existing legend too much)
    gap_patch = Patch(alpha=0.10, label="Non-validated gaps")
    handles, labels_ = ax.get_legend_handles_labels()
    handles.append(gap_patch)
    labels_.append("Non-validated gaps")
    ax.legend(handles, labels_, loc="best")

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)
