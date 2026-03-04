import numpy as np
import pandas as pd
import streamlit as st

from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq


# =========================
# Page setup
# =========================
st.set_page_config(page_title="Inverse Phantom Design", page_icon="🧪", layout="centered")
st.title("🧪 Inverse Design for Silicone Phantoms")
st.caption("Select a target Young’s modulus (kPa). If multiple Ecoflex series overlap, choose the material family.")


# =========================
# Data loading
# =========================
@st.cache_data
def load_phantoms_csv(path: str):
    """
    Expected columns (case-insensitive):
      - Sample Label (e.g., EF50_12_5T)
      - Mean Elastic Modulus (kPa)  OR  Mean Elastic Modulus (kPa)
      - (optional) Thinner concentration (%) or we infer from label
      - (optional) Family / Series (EF10 / EF30 / EF50) or inferred from label
    """
    df = pd.read_csv(path)

    # normalize column names for easier access
    df.columns = [c.strip() for c in df.columns]

    # try to find label + modulus columns robustly
    label_col = None
    for c in df.columns:
        if c.lower() in ["sample label", "label", "sample_label"]:
            label_col = c
            break
    if label_col is None:
        raise ValueError("CSV must contain a 'Sample Label' column.")

    mod_col = None
    for c in df.columns:
        if "mean" in c.lower() and "modulus" in c.lower():
            mod_col = c
            break
    if mod_col is None:
        raise ValueError("CSV must contain a mean elastic modulus column (e.g., 'Mean Elastic Modulus (kPa)').")

    # infer family and thinner % from label if not present
    labels = df[label_col].astype(str).tolist()
    families = []
    thinners = []

    for lab in labels:
        # family: first token like EF50 / EF30 / EF10
        fam = lab.split("_")[0]
        families.append(fam)

        # thinner% parsing:
        # labels like EF50_12_5T or EF10_37_5T or EF30_25T or EF10_0T
        # Take the token after family, strip trailing 'T', convert '_' to '.'
        parts = lab.split("_")
        if len(parts) >= 2:
            t_token = parts[1]
            # if label is EF50_12_5T -> parts[1]="12", parts[2]="5T"
            if len(parts) >= 3 and parts[2].endswith("T"):
                t_token = parts[1] + "_" + parts[2].replace("T", "")
            else:
                t_token = t_token.replace("T", "")
            t_token = t_token.replace("_", ".")
            try:
                t_val = float(t_token)
            except Exception:
                t_val = np.nan
        else:
            t_val = np.nan

        thinners.append(t_val)

    out = pd.DataFrame({
        "label": labels,
        "family": families,
        "thinner_pct": thinners,
        "E_kPa": pd.to_numeric(df[mod_col], errors="coerce"),
    }).dropna(subset=["E_kPa", "thinner_pct"])

    return out


def fallback_phantoms():
    # Updated list including EF50_25T and EF30_25T
    return pd.DataFrame({
        "label": [
            "EF50_0T", "EF50_12_5T", "EF50_25T",
            "EF30_0T", "EF30_12_5T", "EF30_25T",
            "EF10_0T", "EF10_12_5T", "EF10_25T", "EF10_37_5T",
            "EF10_50T", "EF10_62_5T", "EF10_75T", "EF10_87_5T", "EF10_100T"
        ],
        "family": [
            "EF50", "EF50", "EF50",
            "EF30", "EF30", "EF30",
            "EF10", "EF10", "EF10", "EF10",
            "EF10", "EF10", "EF10", "EF10", "EF10"
        ],
        "thinner_pct": [
            0.0, 12.5, 25.0,
            0.0, 12.5, 25.0,
            0.0, 12.5, 25.0, 37.5,
            50.0, 62.5, 75.0, 87.5, 100.0
        ],
        "E_kPa": [
            152.70070288580004, 111.09930866645567, 89.49278526799354,
            97.25997744487732, 73.18310906168253, 65.68354113025582,
            54.20947752233499, 37.2970482769499, 27.397220287652036, 19.37489905967659,
            15.5213581416756, 12.174085251987634, 8.814412371336129, 7.915154597748689, 5.422521729130547
        ]
    })


# =========================
# Build interpolators
# =========================
def build_families(df: pd.DataFrame):
    fams = {}
    for fam, sub in df.groupby("family"):
        sub = sub.sort_values("thinner_pct")
        t = sub["thinner_pct"].to_numpy(dtype=float)
        E = sub["E_kPa"].to_numpy(dtype=float)
        labels = sub["label"].astype(str).tolist()

        # Need at least 2 points to interpolate
        if len(t) < 2:
            continue

        interp = PchipInterpolator(t, E, extrapolate=False)

        fams[fam] = {
            "t": t,
            "E": E,
            "labels": labels,
            "interp": interp,
            "tmin": float(np.min(t)),
            "tmax": float(np.max(t)),
            "Emin": float(np.min(E)),
            "Emax": float(np.max(E)),
        }
    return fams


def invert_family(fam_dict, E_target):
    f = fam_dict["interp"]

    def g(t):
        return float(f(t) - E_target)

    t_star = float(brentq(g, fam_dict["tmin"], fam_dict["tmax"]))
    E_pred = float(f(t_star))

    # nearest measured phantom in that family
    E_arr = fam_dict["E"]
    labels = fam_dict["labels"]
    j = int(np.argmin(np.abs(E_arr - E_target)))
    nearest_label = labels[j]
    nearest_E = float(E_arr[j])
    return t_star, E_pred, nearest_label, nearest_E


def nearest_bounds(all_measured_sorted, E_target):
    lower = None
    upper = None
    for E, fam, t, label in all_measured_sorted:
        if E <= E_target:
            lower = (E, fam, t, label)
        if E >= E_target and upper is None:
            upper = (E, fam, t, label)
    return lower, upper


# =========================
# UI: data source
# =========================
with st.expander("Data source", expanded=False):
    st.write("If you have a CSV in the repo (recommended), point the app to it.")
    use_csv = st.checkbox("Load phantoms from CSV file", value=True)
    csv_path = st.text_input("CSV path", value="data/tables/phantoms_elastic_modulus.csv")

if use_csv:
    try:
        ph_df = load_phantoms_csv(csv_path)
    except Exception as e:
        st.warning(f"Could not load CSV ({e}). Using embedded values instead.")
        ph_df = fallback_phantoms()
else:
    ph_df = fallback_phantoms()

families = build_families(ph_df)
ALL_MEASURED = sorted(
    [(float(r.E_kPa), r.family, float(r.thinner_pct), r.label) for r in ph_df.itertuples()],
    key=lambda x: x[0]
)

# =========================
# UI: target input
# =========================
st.subheader("Target modulus")
E_target = st.number_input("Enter target Young’s modulus (kPa)", min_value=0.0, value=50.0, step=1.0)

# feasible families
feasible = [fam for fam, d in families.items() if d["Emin"] <= E_target <= d["Emax"]]
feasible_sorted = sorted(feasible)

st.divider()

# =========================
# Main logic + overlapping choice
# =========================
if feasible_sorted:
    st.success("Target is within validated range for at least one material family.")

    if len(feasible_sorted) > 1:
        st.write("Multiple families can achieve this modulus (overlapping ranges). Choose one:")
        chosen_fam = st.selectbox("Material family", feasible_sorted, index=0)
    else:
        chosen_fam = feasible_sorted[0]
        st.info(f"Only one feasible family covers this target: **{chosen_fam}**")

    fam_dict = families[chosen_fam]
    t_star, E_pred, nearest_label, nearest_E = invert_family(fam_dict, E_target)

    st.subheader("Design output")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Chosen family", chosen_fam)
        st.metric("Predicted thinner (%)", f"{t_star:.2f}")
    with c2:
        st.metric("Predicted modulus (kPa)", f"{E_pred:.2f}")
        st.metric("Nearest measured phantom", f"{nearest_label} ({nearest_E:.2f} kPa)")

    st.caption("Composition: (A + B) + predicted thinner percentage (by weight of A+B).")

else:
    st.error("Target is outside validated ranges (gap/out-of-range). No extrapolation performed.")

    lower, upper = nearest_bounds(ALL_MEASURED, E_target)

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

st.divider()

with st.expander("Show phantom table used by the app"):
    st.dataframe(ph_df.sort_values(["family", "thinner_pct"]), use_container_width=True)
