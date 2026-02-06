import csv
from pathlib import Path

import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

# -----------------------------
# Settings
# -----------------------------
DATA_PATH = Path("data/processed/phantoms_table.csv")
FAMILIES_ORDER = ["EF50", "EF30", "EF10"]
GAP_LEVELS_KPA = sorted([111.10, 97.26, 73.18, 54.21])


# -----------------------------
# Helpers
# -----------------------------
def parse_thinner_from_label(label: str) -> float:
    # Handles EF10_12.5T and EF10_12_5T
    t_part = label.split("_", 1)[1].replace("T", "").replace("_", ".")
    return float(t_part)


def load_phantoms(csv_path: Path):
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Missing {csv_path}. Run the app from the repo root so it can find data/processed/phantoms_table.csv."
        )

    phantoms = []  # (label, family, thinner_pct, E_mean)
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row["sample_label"].strip()
            family = label.split("_", 1)[0].strip()
            thinner_pct = parse_thinner_from_label(label)
            E_mean = float(row["elastic_modulus_mean_kPa"])
            phantoms.append((label, family, thinner_pct, E_mean))
    return phantoms


def build_family_models(phantoms):
    families = {}
    for label, fam, t, E in phantoms:
        families.setdefault(fam, {"t": [], "E": [], "labels": []})
        families[fam]["t"].append(float(t))
        families[fam]["E"].append(float(E))
        families[fam]["labels"].append(label)

    for fam, d in families.items():
        t = np.array(d["t"], dtype=float)
        E = np.array(d["E"], dtype=float)
        order = np.argsort(t)
        t = t[order]
        E = E[order]
        labels = list(np.array(d["labels"], dtype=object)[order])

        d["t"] = t
        d["E"] = E
        d["labels"] = labels
        d["interp"] = PchipInterpolator(t, E, extrapolate=False)
        d["tmin"], d["tmax"] = float(t.min()), float(t.max())
        d["Emin"], d["Emax"] = float(E.min()), float(E.max())

    return families


def invert_family(family_model, E_target):
    f = family_model["interp"]

    def g(t):
        return float(f(t) - E_target)

    t_star = float(brentq(g, family_model["tmin"], family_model["tmax"]))
    E_pred = float(f(t_star))
    return t_star, E_pred


def nearest_bounds(all_measured, E_target):
    # all_measured: sorted list of (E, label, fam, t)
    lower = None
    upper = None
    for E, label, fam, t in all_measured:
        if E <= E_target:
            lower = (E, label, fam, t)
        if E >= E_target and upper is None:
            upper = (E, label, fam, t)
    return lower, upper


def make_plot(phantoms, families):
    t_meas = np.array([p[2] for p in phantoms], dtype=float)
    E_meas = np.array([p[3] for p in phantoms], dtype=float)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    # y-limits with small margin
    ymin, ymax = float(E_meas.min()), float(E_meas.max())
    pad = 0.05 * (ymax - ymin) if ymax > ymin else 1.0
    ymin_plot, ymax_plot = ymin - pad, ymax + pad
    ax.set_ylim(ymin_plot, ymax_plot)

    # Shade alternating gap bands using the same levels as your paper figure
    bounds = [ymin_plot] + GAP_LEVELS_KPA + [ymax_plot]
    for i in range(len(bounds) - 1):
        if i % 2 == 1:
            ax.axhspan(bounds[i], bounds[i + 1], alpha=0.10)

    for y in GAP_LEVELS_KPA:
        ax.axhline(y=y, linestyle=":", linewidth=1.2, alpha=0.8)

    ax.plot(t_meas, E_meas, "o", label="Measured (phantoms)")

    for fam in FAMILIES_ORDER:
        d = families.get(fam)
        if not d or len(d["t"]) < 2:
            continue
        t_fine = np.linspace(d["tmin"], d["tmax"], 300)
        ax.plot(t_fine, d["interp"](t_fine), label=f"{fam} interpolation")

    ax.set_xlabel("Thinner concentration (%)")
    ax.set_ylabel("Elastic modulus (kPa)")
    ax.set_title("Elastic modulus vs thinner concentration")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    return fig


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Phantom Material Designer", layout="wide")
st.title("Phantom Material Designer")
st.write(
    "Design a silicone phantom composition from a target elastic modulus using experimentally validated data "
    "and a gap-aware policy (no extrapolation)."
)

phantoms = load_phantoms(DATA_PATH)
families = build_family_models(phantoms)

all_measured = sorted(
    [(E, label, fam, t) for (label, fam, t, E) in phantoms],
    key=lambda x: x[0],
)

left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("Target specification")
    E_target = st.number_input(
        "Target elastic modulus (kPa)",
        min_value=0.0,
        value=50.0,
        step=1.0,
        format="%.2f",
    )

    mode = st.radio(
        "Design mode",
        ["Auto-select family (if feasible)", "Force a specific family"],
        index=0,
    )

    chosen_family = None
    if mode == "Force a specific family":
        chosen_family = st.selectbox("Choose family", FAMILIES_ORDER, index=2)

    st.subheader("Result")

    feasible = [
        fam for fam, d in families.items()
        if d["Emin"] <= E_target <= d["Emax"]
    ]
    feasible_sorted = [f for f in FAMILIES_ORDER if f in feasible]

    if mode == "Force a specific family":
        fam = chosen_family
        d = families[fam]
        if d["Emin"] <= E_target <= d["Emax"]:
            t_star, E_pred = invert_family(d, E_target)
            st.success(f"Feasible within {fam}")
            st.write(f"**Predicted thinner:** {t_star:.2f}%")
            st.write(f"**Predicted modulus (interp):** {E_pred:.2f} kPa")
            st.code(
                f"{fam} (A+B) + {t_star:.2f}% thinner (by weight of A+B)",
                language="text",
            )
        else:
            st.error(f"{fam} cannot cover {E_target:.2f} kPa (validated range: {d['Emin']:.2f}–{d['Emax']:.2f} kPa)")
            lower, upper = nearest_bounds(all_measured, E_target)
            st.write("Nearest validated bounds:")
            if lower:
                E, label, fam_l, t = lower
                st.write(f"- Lower: **{label}** ({fam_l}, {t:.1f}%): **{E:.2f} kPa**")
            else:
                st.write("- Lower: none")
            if upper:
                E, label, fam_u, t = upper
                st.write(f"- Upper: **{label}** ({fam_u}, {t:.1f}%): **{E:.2f} kPa**")
            else:
                st.write("- Upper: none")
    else:
        if feasible_sorted:
            st.success("Covered by validated data")
            for fam in feasible_sorted:
                d = families[fam]
                t_star, E_pred = invert_family(d, E_target)
                with st.expander(f"{fam}: predicted recipe", expanded=(fam == feasible_sorted[0])):
                    st.write(f"**Predicted thinner:** {t_star:.2f}%")
                    st.write(f"**Predicted modulus (interp):** {E_pred:.2f} kPa")
                    st.code(
                        f"{fam} (A+B) + {t_star:.2f}% thinner (by weight of A+B)",
                        language="text",
                    )
        else:
            st.warning("Target is in a non-validated gap / out of range (no extrapolation).")
            lower, upper = nearest_bounds(all_measured, E_target)
            st.write("Nearest validated bounds:")
            if lower:
                E, label, fam_l, t = lower
                st.write(f"- Lower: **{label}** ({fam_l}, {t:.1f}%): **{E:.2f} kPa**")
            else:
                st.write("- Lower: none")
            if upper:
                E, label, fam_u, t = upper
                st.write(f"- Upper: **{label}** ({fam_u}, {t:.1f}%): **{E:.2f} kPa**")
            else:
                st.write("- Upper: none")

with right:
    st.subheader("Dataset overview")
    fig = make_plot(phantoms, families)
    st.pyplot(fig)
    st.caption("Shaded bands indicate non-validated regions (visual guide).")
