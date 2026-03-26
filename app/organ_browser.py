import streamlit as st
import streamlit.components.v1 as components

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Organ Browser — Phantom Material Database",
    page_icon="🫀",
    layout="wide",
)

# ── Minimal style overrides ────────────────────────────────────────────────────
st.markdown("""
<style>
    /* hide default Streamlit padding at top */
    .block-container { padding-top: 1.5rem; }
    h1 { font-size: 1.4rem; font-weight: 500; margin-bottom: 0.2rem; }
    p.subtitle { color: #888; font-size: 0.85rem; margin-top: 0; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("## Organ Browser")
st.markdown(
    "<p class='subtitle'>Select an organ to view its literature stiffness range "
    "and matching phantom compositions from the database.</p>",
    unsafe_allow_html=True,
)
st.divider()

# ── Embed the interactive organ browser ───────────────────────────────────────
# The entire app is a self-contained HTML/JS/SVG component.
# To add more organs: extend ORGANS and ILLUS in the script block,
# and add the corresponding SVG group in the body diagram.

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'DM Sans', sans-serif;
    background: transparent;
    color: #1a1a1a;
  }

  /* ── Layout ── */
  .app {
    display: grid;
    grid-template-columns: 340px 1fr;
    height: 780px;
    border: 1px solid #e5e5e5;
    border-radius: 12px;
    overflow: hidden;
  }

  /* ── Left panel ── */
  .left-panel {
    border-right: 1px solid #e5e5e5;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px 16px;
    background: #f9f9f8;
    overflow-y: auto;
  }

  .panel-label {
    font-size: 10px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 16px;
    align-self: flex-start;
  }

  .body-svg { width: 260px; cursor: default; }

  /* organ hover / active */
  .organ-region { cursor: pointer; }
  .organ-region:hover .organ-hit { opacity: 0.18; }
  .organ-hit { fill: #fff; opacity: 0; transition: opacity 0.15s; }
  .organ-region.active .organ-hit { opacity: 0.28; }

  /* ── Right panel ── scrolls internally so recipe is always reachable */
  .right-panel {
    padding: 24px;
    background: #fff;
    overflow-y: scroll;
    height: 100%;
  }

  /* empty state */
  .empty-state {
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #bbb;
    gap: 10px;
  }
  .empty-state p { font-size: 13px; }

  /* organ header */
  .organ-header {
    display: grid;
    grid-template-columns: 96px 1fr;
    gap: 16px;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid #f0f0f0;
  }
  .organ-illustration { width: 96px; height: 96px; }
  .organ-name  { font-size: 20px; font-weight: 500; line-height: 1.2; }
  .organ-subtitle { font-size: 12px; color: #888; margin-top: 4px; }

  /* section label */
  .section-title {
    font-size: 10px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 10px;
  }

  /* stiffness bar */
  .stiffness-range-labels {
    display: flex; justify-content: space-between;
    font-size: 11px; color: #888;
    margin-bottom: 5px; font-family: 'DM Mono', monospace;
  }
  .stiffness-track {
    height: 6px; background: #eee; border-radius: 3px;
    position: relative; margin-bottom: 4px;
  }
  .stiffness-fill {
    position: absolute; top: 0; bottom: 0; border-radius: 3px;
    background: #3b82f6; opacity: 0.65;
  }
  .stiffness-label { font-size: 10px; color: #bbb; text-align: right; margin-bottom: 14px; }

  /* literature rows */
  .lit-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 0; border-bottom: 1px solid #f5f5f5; font-size: 12px;
  }
  .lit-row:last-child { border-bottom: none; }
  .lit-key { color: #555; }
  .lit-val { font-family: 'DM Mono', monospace; font-size: 11px; font-weight: 500; }

  /* badges */
  .badge {
    display: inline-block; font-size: 9px; padding: 1px 7px;
    border-radius: 8px; font-weight: 500; margin-left: 6px;
  }
  .badge-healthy { background: #dcfce7; color: #166534; }
  .badge-patho   { background: #fee2e2; color: #991b1b; }

  .section-divider { height: 1px; background: #f0f0f0; margin: 16px 0; }

  /* phantom cards */
  .phantom-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }

  .phantom-card {
    border: 1px solid #e5e5e5; border-radius: 8px;
    padding: 10px 12px; cursor: pointer;
    transition: background 0.12s, border-color 0.12s;
  }
  .phantom-card:hover { background: #f5f5f5; border-color: #d0d0d0; }
  .phantom-card.selected {
    background: #eff6ff; border-color: #93c5fd; border-width: 1.5px;
  }
  .phantom-card.selected .phantom-label { color: #1d4ed8; }

  .phantom-label {
    font-size: 11px; font-weight: 500;
    font-family: 'DM Mono', monospace; margin-bottom: 2px;
    transition: color 0.12s;
  }
  .phantom-modulus { font-size: 10px; color: #888; }

  /* recipe box */
  .recipe-box {
    border: 1px solid #bfdbfe; border-radius: 8px;
    padding: 14px 16px; background: #eff6ff;
    margin-top: 12px; display: none;
  }
  .recipe-box.visible { display: block; }
  .recipe-title {
    font-size: 10px; letter-spacing: 0.08em;
    text-transform: uppercase; color: #1d4ed8; margin-bottom: 10px;
  }
  .recipe-row {
    display: flex; justify-content: space-between; align-items: baseline;
    padding: 4px 0; border-bottom: 1px solid #bfdbfe; font-size: 12px;
  }
  .recipe-row:last-child { border-bottom: none; }
  .recipe-key { color: #555; }
  .recipe-val { font-family: 'DM Mono', monospace; font-size: 11px; font-weight: 500; }

  .no-phantom { font-size: 12px; color: #aaa; grid-column: span 2; padding: 8px 0; }
  .note-text  { font-size: 11px; color: #aaa; margin-top: 8px; font-style: italic; }
</style>
</head>
<body>

<div class="app">

  <!-- ════════════════════════════════════════
       LEFT — body schematic with organ SVGs
       ════════════════════════════════════════ -->
  <div class="left-panel">
    <div class="panel-label">Select an organ</div>

    <!--
      ANTERIOR VIEW  (patient faces viewer)
      Patient's RIGHT = diagram LEFT
      Patient's LEFT  = diagram RIGHT

      Heart   : midline, slight patient-left  → diagram right of centre
      Liver   : patient's right upper abdomen → diagram LEFT
      Stomach : patient's left upper abdomen  → diagram RIGHT
      R kidney: patient's right               → diagram LEFT,  slightly lower
      L kidney: patient's left                → diagram RIGHT, slightly higher
      Prostate: midline, lower pelvis
      Muscle  : shown on patient's right arm  → diagram LEFT arm
      Adipose : shown on patient's left flank → diagram RIGHT inner wall
    -->
    <svg class="body-svg" viewBox="0 0 200 500" xmlns="http://www.w3.org/2000/svg">

      <!-- Body outline -->
      <ellipse cx="100" cy="38" rx="30" ry="34" fill="none" stroke="#ccc" stroke-width="0.8"/>
      <rect x="88" y="68" width="24" height="16" rx="4" fill="none" stroke="#ccc" stroke-width="0.8"/>
      <path d="M52 84 Q42 92 40 120 L36 268 Q36 278 48 280 L152 280 Q164 278 164 268 L160 120 Q158 92 148 84 Z" fill="none" stroke="#ccc" stroke-width="0.8"/>
      <path d="M52 90 Q36 98 30 136 L22 228 Q20 240 28 242 L44 242 Q52 240 50 228 L54 136 Z" fill="none" stroke="#ccc" stroke-width="0.8"/>
      <path d="M148 90 Q164 98 170 136 L178 228 Q180 240 172 242 L156 242 Q148 240 150 228 L146 136 Z" fill="none" stroke="#ccc" stroke-width="0.8"/>
      <path d="M48 280 L44 366 Q42 382 50 384 L78 384 Q86 382 86 366 L88 280 Z" fill="none" stroke="#ccc" stroke-width="0.8"/>
      <path d="M152 280 L156 366 Q158 382 150 384 L122 384 Q114 382 114 366 L112 280 Z" fill="none" stroke="#ccc" stroke-width="0.8"/>
      <ellipse cx="64"  cy="390" rx="14" ry="8" fill="none" stroke="#ccc" stroke-width="0.8"/>
      <ellipse cx="136" cy="390" rx="14" ry="8" fill="none" stroke="#ccc" stroke-width="0.8"/>

      <!-- BRAIN -->
      <g class="organ-region" id="org-brain" onclick="selectOrgan('brain')" transform="translate(100,36)">
        <rect class="organ-hit" x="-22" y="-24" width="44" height="44" rx="6"/>
        <path d="M-18 4 Q-20 -10 -12 -18 Q-4 -24 6 -22 Q18 -20 20 -8 Q22 4 14 12 Q6 18 -4 16 Q-14 14 -18 4 Z" fill="#9FE1CB" stroke="#1D9E75" stroke-width="0.8"/>
        <path d="M-14 -4 Q-8 -10 0 -8 Q8 -6 12 -2" fill="none" stroke="#0F6E56" stroke-width="0.6"/>
        <path d="M-12 4 Q-4 0 4 2 Q10 4 14 8"      fill="none" stroke="#0F6E56" stroke-width="0.6"/>
        <path d="M-6 -16 Q0 -18 8 -14"             fill="none" stroke="#0F6E56" stroke-width="0.6"/>
        <path d="M-4 -8 Q-2 -6 0 -8"               fill="none" stroke="#0F6E56" stroke-width="0.5"/>
        <path d="M4 2 Q6 4 8 2"                     fill="none" stroke="#0F6E56" stroke-width="0.5"/>
      </g>

      <!-- HEART — midline, nudged to patient's left = diagram right -->
      <g class="organ-region" id="org-heart" onclick="selectOrgan('heart')" transform="translate(108,130)">
        <rect class="organ-hit" x="-16" y="-16" width="38" height="38" rx="6"/>
        <path d="M5 22 Q-13 10 -13 0 Q-13 -9 -6 -10 Q0 -12 5 -5 Q10 -12 17 -10 Q24 -8 24 0 Q24 10 5 22Z" fill="#F4C0D1" stroke="#D4537E" stroke-width="0.8"/>
        <line x1="5"  y1="-5" x2="5"  y2="18" stroke="#D4537E" stroke-width="0.6"/>
        <line x1="-10" y1="5" x2="21" y2="5"  stroke="#D4537E" stroke-width="0.6"/>
        <path d="M5 -10 Q5 -18 11 -20" fill="none" stroke="#D4537E" stroke-width="1.2" stroke-linecap="round"/>
      </g>

      <!-- LIVER — patient's right = diagram LEFT -->
      <g class="organ-region" id="org-liver" onclick="selectOrgan('liver')" transform="translate(76,158)">
        <rect class="organ-hit" x="-28" y="-14" width="56" height="30" rx="6"/>
        <path d="M-24 6 Q-24 -10 -10 -12 Q2 -14 10 -9 Q18 -6 22 -11 Q30 -14 26 0 Q24 10 8 12 Q-6 14 -16 8 Z" fill="#B5D4F4" stroke="#378ADD" stroke-width="0.8"/>
        <path d="M6 -10 Q8 0 8 12"   fill="none" stroke="#185FA5" stroke-width="0.6"/>
        <path d="M-10 6 Q0 2 8 6"   fill="none" stroke="#185FA5" stroke-width="0.6"/>
      </g>

      <!-- STOMACH — patient's left = diagram RIGHT -->
      <g class="organ-region" id="org-stomach" onclick="selectOrgan('stomach')" transform="translate(130,178)">
        <rect class="organ-hit" x="-16" y="-16" width="34" height="34" rx="6"/>
        <path d="M-8 -12 Q-14 -12 -14 0 Q-14 12 -6 14 Q4 16 8 8 Q10 2 8 -5 Q6 -13 0 -13 Z" fill="#FAC775" stroke="#BA7517" stroke-width="0.8"/>
        <path d="M8 -5 Q14 -5 14 2 Q14 8 8 8" fill="none" stroke="#BA7517" stroke-width="0.8" stroke-linecap="round"/>
        <path d="M-8 -12 Q-6 -20 0 -20 Q6 -20 6 -14" fill="none" stroke="#854F0B" stroke-width="1" stroke-linecap="round"/>
      </g>

      <!-- KIDNEYS -->
      <!-- R kidney (patient right) → diagram LEFT, lower y=217 -->
      <!-- L kidney (patient left)  → diagram RIGHT, higher y=213 -->
      <g class="organ-region" id="org-kidney" onclick="selectOrgan('kidney')">
        <rect class="organ-hit" x="56"  y="200" width="26" height="34" rx="6"/>
        <rect class="organ-hit" x="118" y="196" width="26" height="34" rx="6"/>
        <g transform="translate(69,217)">
          <path d="M-8 -12 Q-12 -12 -12 0 Q-12 12 -8 12 Q0 12 6 6 Q10 0 6 -6 Q2 -12 -8 -12 Z" fill="#CECBF6" stroke="#7F77DD" stroke-width="0.7"/>
          <ellipse cx="-2" cy="0" rx="5" ry="8" fill="#AFA9EC" fill-opacity="0.5"/>
          <path d="M6 -3 Q8 0 6 3" fill="none" stroke="#7F77DD" stroke-width="0.8"/>
        </g>
        <g transform="translate(131,213) scale(-1,1)">
          <path d="M-8 -12 Q-12 -12 -12 0 Q-12 12 -8 12 Q0 12 6 6 Q10 0 6 -6 Q2 -12 -8 -12 Z" fill="#CECBF6" stroke="#7F77DD" stroke-width="0.7"/>
          <ellipse cx="-2" cy="0" rx="5" ry="8" fill="#AFA9EC" fill-opacity="0.5"/>
          <path d="M6 -3 Q8 0 6 3" fill="none" stroke="#7F77DD" stroke-width="0.8"/>
        </g>
      </g>

      <!-- PROSTATE — midline lower pelvis -->
      <g class="organ-region" id="org-prostate" onclick="selectOrgan('prostate')" transform="translate(100,256)">
        <rect class="organ-hit" x="-16" y="-12" width="32" height="24" rx="6"/>
        <ellipse cx="0" cy="0" rx="13" ry="10" fill="#F4C0D1" stroke="#D4537E" stroke-width="0.8"/>
        <ellipse cx="0" cy="0" rx="4"  ry="6"  fill="#FBEAF0" stroke="#D4537E" stroke-width="0.5"/>
        <path d="M-8 -4 Q0 -6 8 -4" fill="none" stroke="#D4537E" stroke-width="0.4"/>
      </g>

      <!-- SKELETAL MUSCLE — patient right arm = diagram LEFT arm -->
      <g class="organ-region" id="org-muscle" onclick="selectOrgan('muscle')" transform="translate(32,178)">
        <rect class="organ-hit" x="-12" y="-22" width="24" height="44" rx="6"/>
        <ellipse cx="0" cy="0" rx="9" ry="18" fill="#C0DD97" stroke="#639922" stroke-width="0.8"/>
        <line x1="-4" y1="-12" x2="-4" y2="12" stroke="#3B6D11" stroke-width="0.5" opacity="0.7"/>
        <line x1="0"  y1="-15" x2="0"  y2="15" stroke="#3B6D11" stroke-width="0.5" opacity="0.7"/>
        <line x1="4"  y1="-12" x2="4"  y2="12" stroke="#3B6D11" stroke-width="0.5" opacity="0.7"/>
        <rect x="-4" y="-20" width="8" height="5" rx="2" fill="#97C459" stroke="#639922" stroke-width="0.5"/>
        <rect x="-4" y="15"  width="8" height="5" rx="2" fill="#97C459" stroke="#639922" stroke-width="0.5"/>
      </g>

      <!-- ADIPOSE — patient left flank = diagram RIGHT inner torso wall -->
      <g class="organ-region" id="org-adipose" onclick="selectOrgan('adipose')" transform="translate(152,210)">
        <rect class="organ-hit" x="-14" y="-18" width="28" height="36" rx="6"/>
        <circle cx="0"  cy="-6"  r="7"   fill="#F5C4B3" stroke="#F0997B" stroke-width="0.6"/>
        <circle cx="-5" cy="6"   r="6"   fill="#F5C4B3" stroke="#F0997B" stroke-width="0.6"/>
        <circle cx="6"  cy="7"   r="5"   fill="#FAECE7" stroke="#F0997B" stroke-width="0.6"/>
        <circle cx="2"  cy="-13" r="4"   fill="#FAECE7" stroke="#F0997B" stroke-width="0.6"/>
        <circle cx="0"  cy="-6"  r="3"   fill="#F0997B" fill-opacity="0.25"/>
        <circle cx="-5" cy="6"   r="2.5" fill="#F0997B" fill-opacity="0.25"/>
        <circle cx="6"  cy="7"   r="2"   fill="#F0997B" fill-opacity="0.25"/>
      </g>

      <!-- Labels -->
      <text x="100" y="16"  text-anchor="middle" font-size="7" fill="#aaa" font-family="DM Sans,sans-serif">Brain</text>
      <text x="112" y="112" text-anchor="middle" font-size="7" fill="#aaa" font-family="DM Sans,sans-serif">Heart</text>
      <text x="72"  y="143" text-anchor="middle" font-size="7" fill="#aaa" font-family="DM Sans,sans-serif">Liver</text>
      <text x="134" y="162" text-anchor="middle" font-size="7" fill="#aaa" font-family="DM Sans,sans-serif">Stomach</text>
      <text x="69"  y="240" text-anchor="middle" font-size="7" fill="#aaa" font-family="DM Sans,sans-serif">R. Kidney</text>
      <text x="131" y="236" text-anchor="middle" font-size="7" fill="#aaa" font-family="DM Sans,sans-serif">L. Kidney</text>
      <text x="100" y="274" text-anchor="middle" font-size="7" fill="#aaa" font-family="DM Sans,sans-serif">Prostate</text>
      <text x="32"  y="202" text-anchor="middle" font-size="7" fill="#aaa" font-family="DM Sans,sans-serif">Muscle</text>
      <text x="152" y="234" text-anchor="middle" font-size="7" fill="#aaa" font-family="DM Sans,sans-serif">Fat</text>

    </svg>
  </div><!-- end left-panel -->

  <!-- ════════════════════════════════════════
       RIGHT — data panel
       ════════════════════════════════════════ -->
  <div class="right-panel">

    <div class="empty-state" id="empty-state">
      <svg width="44" height="44" viewBox="0 0 44 44">
        <circle cx="22" cy="22" r="21" fill="none" stroke="#ddd" stroke-width="1"/>
        <path d="M14 22 L20 28 L30 16" fill="none" stroke="#ddd" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
      <p>Click an organ to explore tissue data</p>
      <p style="font-size:11px;color:#ccc;margin-top:2px">and matching phantom compositions</p>
    </div>

    <div id="data-panel" style="display:none">

      <!-- organ header: illustration + name -->
      <div class="organ-header">
        <svg class="organ-illustration" id="organ-illus"
             viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"></svg>
        <div>
          <div class="organ-name"    id="organ-name">—</div>
          <div class="organ-subtitle" id="organ-subtitle">—</div>
        </div>
      </div>

      <!-- stiffness range -->
      <div class="section-title">Stiffness range (literature)</div>
      <div class="stiffness-range-labels">
        <span id="e-min">—</span><span id="e-max">—</span>
      </div>
      <div class="stiffness-track">
        <div class="stiffness-fill" id="e-bar"></div>
      </div>
      <div class="stiffness-label">Scale: 0 – 160 kPa</div>
      <div id="lit-rows"></div>

      <div class="section-divider"></div>

      <!-- matching phantoms -->
      <div class="section-title">Matching phantoms</div>
      <div class="phantom-grid" id="phantom-grid"></div>

      <!-- fabrication recipe (appears on phantom click) -->
      <div class="recipe-box" id="recipe-box">
        <div class="recipe-title" id="recipe-title">—</div>
        <div id="recipe-rows"></div>
      </div>

    </div><!-- end data-panel -->
  </div><!-- end right-panel -->

</div><!-- end app -->

<script>
// ════════════════════════════════════════════════════════
// DATA
// ════════════════════════════════════════════════════════

const SCALE_MAX = 160;

// Large organ illustrations (viewBox 0 0 100 100)
// To add a new organ: add an entry here and in ORGANS + the SVG body group above.
const ILLUS = {
  brain: `
    <path d="M16 52 Q14 28 28 14 Q42 2 58 6 Q74 10 80 26 Q86 42 78 58 Q70 72 54 78 Q38 82 26 72 Q16 64 16 52Z"
          fill="#9FE1CB" stroke="#1D9E75" stroke-width="1.2"/>
    <path d="M48 6  Q48 52 48 78"                         fill="none" stroke="#0F6E56" stroke-width="0.8"/>
    <path d="M22 30 Q34 22 48 26 Q62 22 74 30"            fill="none" stroke="#0F6E56" stroke-width="0.9"/>
    <path d="M18 46 Q30 38 48 42 Q66 38 78 46"            fill="none" stroke="#0F6E56" stroke-width="0.9"/>
    <path d="M20 60 Q32 54 48 58 Q64 54 76 60"            fill="none" stroke="#0F6E56" stroke-width="0.9"/>
    <path d="M28 38 Q32 34 36 38"                         fill="none" stroke="#0F6E56" stroke-width="0.6"/>
    <path d="M58 38 Q62 34 66 38"                         fill="none" stroke="#0F6E56" stroke-width="0.6"/>`,

  heart: `
    <path d="M50 82 Q20 60 20 36 Q20 18 34 16 Q44 14 50 26 Q56 14 66 16 Q80 18 80 36 Q80 60 50 82Z"
          fill="#F4C0D1" stroke="#D4537E" stroke-width="1.2"/>
    <line x1="50" y1="26" x2="50" y2="74" stroke="#D4537E" stroke-width="1"/>
    <line x1="24" y1="46" x2="76" y2="46" stroke="#D4537E" stroke-width="1"/>
    <path d="M50 16 Q50 4 62 2"  fill="none" stroke="#D4537E" stroke-width="2"   stroke-linecap="round"/>
    <path d="M50 16 Q44 4 38 6"  fill="none" stroke="#993556" stroke-width="1.5" stroke-linecap="round"/>
    <text x="34" y="38" font-size="8" fill="#712B13" font-family="DM Sans,sans-serif">RA</text>
    <text x="58" y="38" font-size="8" fill="#712B13" font-family="DM Sans,sans-serif">LA</text>
    <text x="34" y="62" font-size="8" fill="#712B13" font-family="DM Sans,sans-serif">RV</text>
    <text x="58" y="62" font-size="8" fill="#712B13" font-family="DM Sans,sans-serif">LV</text>`,

  liver: `
    <path d="M14 55 Q14 24 34 18 Q50 12 62 18 Q76 24 80 36 Q84 48 76 58 Q66 68 44 70 Q24 72 14 55Z"
          fill="#B5D4F4" stroke="#378ADD" stroke-width="1.2"/>
    <path d="M48 18 Q50 44 50 70"          fill="none" stroke="#185FA5" stroke-width="1"/>
    <path d="M28 52 Q40 46 50 52 Q62 58 72 52" fill="none" stroke="#185FA5" stroke-width="0.8"/>
    <text x="30" y="46" font-size="9" fill="#042C53" font-family="DM Sans,sans-serif">Right</text>
    <text x="56" y="46" font-size="9" fill="#042C53" font-family="DM Sans,sans-serif">Left</text>`,

  stomach: `
    <path d="M30 18 Q18 18 16 34 Q14 52 20 64 Q28 76 42 76 Q56 74 60 60 Q64 46 58 30 Q52 16 42 18 Z"
          fill="#FAC775" stroke="#BA7517" stroke-width="1.2"/>
    <path d="M58 30 Q72 28 74 38 Q76 50 60 60" fill="none" stroke="#BA7517" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M30 18 Q28 8 36 6 Q44 4 44 14"    fill="none" stroke="#854F0B" stroke-width="1.2" stroke-linecap="round"/>
    <path d="M24 44 Q36 40 48 44"              fill="none" stroke="#BA7517" stroke-width="0.7"/>
    <path d="M22 54 Q34 50 46 54"              fill="none" stroke="#BA7517" stroke-width="0.7"/>`,

  kidney: `
    <path d="M24 10 Q10 10 10 50 Q10 88 24 88 Q42 88 56 70 Q66 54 56 32 Q44 10 24 10Z"
          fill="#CECBF6" stroke="#7F77DD" stroke-width="1.2"/>
    <ellipse cx="30" cy="50" rx="16" ry="28" fill="#AFA9EC" fill-opacity="0.6"/>
    <ellipse cx="30" cy="50" rx="8"  ry="16" fill="#EEEDFE" stroke="#7F77DD" stroke-width="0.8"/>
    <path d="M56 38 Q68 38 72 50 Q68 62 56 62" fill="none" stroke="#7F77DD" stroke-width="1.5" stroke-linecap="round"/>
    <text x="22" y="26" font-size="8" fill="#26215C" font-family="DM Sans,sans-serif">Cortex</text>
    <text x="16" y="54" font-size="8" fill="#26215C" font-family="DM Sans,sans-serif">Medulla</text>
    <text x="18" y="72" font-size="8" fill="#26215C" font-family="DM Sans,sans-serif">Pelvis</text>`,

  prostate: `
    <ellipse cx="50" cy="50" rx="38" ry="32" fill="#F4C0D1" stroke="#D4537E" stroke-width="1.2"/>
    <ellipse cx="50" cy="50" rx="14" ry="20" fill="#FBEAF0" stroke="#D4537E" stroke-width="0.8"/>
    <ellipse cx="50" cy="50" rx="5"  ry="10" fill="#F4C0D1" stroke="#D4537E" stroke-width="0.6"/>
    <path d="M20 44 Q36 40 50 44 Q64 40 80 44" fill="none" stroke="#D4537E" stroke-width="0.8"/>
    <text x="50" y="22" font-size="8" text-anchor="middle" fill="#4B1528" font-family="DM Sans,sans-serif">Peripheral</text>
    <text x="50" y="56" font-size="8" text-anchor="middle" fill="#4B1528" font-family="DM Sans,sans-serif">Central</text>
    <text x="50" y="76" font-size="8" text-anchor="middle" fill="#72243E" font-family="DM Sans,sans-serif">Urethra</text>`,

  muscle: `
    <ellipse cx="50" cy="50" rx="28" ry="44" fill="#C0DD97" stroke="#639922" stroke-width="1.2"/>
    <line x1="36" y1="16" x2="36" y2="84" stroke="#3B6D11" stroke-width="0.8" opacity="0.8"/>
    <line x1="44" y1="10" x2="44" y2="90" stroke="#3B6D11" stroke-width="0.8" opacity="0.8"/>
    <line x1="50" y1="8"  x2="50" y2="92" stroke="#3B6D11" stroke-width="0.8" opacity="0.8"/>
    <line x1="56" y1="10" x2="56" y2="90" stroke="#3B6D11" stroke-width="0.8" opacity="0.8"/>
    <line x1="64" y1="16" x2="64" y2="84" stroke="#3B6D11" stroke-width="0.8" opacity="0.8"/>
    <rect x="36" y="4"  width="28" height="10" rx="4" fill="#97C459" stroke="#639922" stroke-width="0.8"/>
    <rect x="36" y="86" width="28" height="10" rx="4" fill="#97C459" stroke="#639922" stroke-width="0.8"/>
    <text x="50" y="12" text-anchor="middle" font-size="7" fill="#173404" font-family="DM Sans,sans-serif">Tendon</text>
    <text x="50" y="97" text-anchor="middle" font-size="7" fill="#173404" font-family="DM Sans,sans-serif">Tendon</text>`,

  adipose: `
    <circle cx="42" cy="38" r="20" fill="#F5C4B3" stroke="#F0997B" stroke-width="1"/>
    <circle cx="64" cy="32" r="16" fill="#FAECE7" stroke="#F0997B" stroke-width="1"/>
    <circle cx="38" cy="64" r="18" fill="#F5C4B3" stroke="#F0997B" stroke-width="1"/>
    <circle cx="64" cy="60" r="14" fill="#FAECE7" stroke="#F0997B" stroke-width="1"/>
    <circle cx="42" cy="38" r="8"  fill="#F0997B" fill-opacity="0.25"/>
    <circle cx="64" cy="32" r="6"  fill="#F0997B" fill-opacity="0.25"/>
    <circle cx="38" cy="64" r="7"  fill="#F0997B" fill-opacity="0.25"/>
    <circle cx="64" cy="60" r="5"  fill="#F0997B" fill-opacity="0.25"/>`,
};

// Organ metadata
// eMin / eMax define the range used to filter matching phantoms.
// litRows provide the table shown under "Stiffness range".
// Add new organs here alongside their SVG group in the body diagram above.
const ORGANS = {
  brain: {
    name: 'Brain',
    subtitle: 'Central nervous system — grey and white matter',
    eMin: 0.5, eMax: 30,
    litRows: [
      { k: 'Grey matter (healthy)',  v: '0.5 – 3 kPa',  type: 'healthy' },
      { k: 'White matter (healthy)', v: '2 – 8 kPa',    type: 'healthy' },
      { k: 'Glioma (tumour)',        v: '10 – 30 kPa',  type: 'patho'   },
    ],
    note: 'Brain tissue is significantly softer than most organs. Only the softest phantom formulations approach this range.',
  },
  heart: {
    name: 'Heart (cardiac muscle)',
    subtitle: 'Myocardium — passive and active states',
    eMin: 10, eMax: 80,
    litRows: [
      { k: 'Passive myocardium (diastole)', v: '10 – 30 kPa', type: 'healthy' },
      { k: 'Active myocardium (systole)',   v: '30 – 80 kPa', type: 'healthy' },
    ],
  },
  liver: {
    name: 'Liver',
    subtitle: 'Parenchymal tissue — healthy and pathological states',
    eMin: 3, eMax: 120,
    litRows: [
      { k: 'Healthy liver',                    v: '3 – 8 kPa',    type: 'healthy' },
      { k: 'Cirrhosis',                        v: '15 – 40 kPa',  type: 'patho'   },
      { k: 'CCC / HCC / Malignant lymphoma',   v: '40 – 120 kPa', type: 'patho'   },
    ],
  },
  stomach: {
    name: 'Stomach',
    subtitle: 'Gastric wall — healthy and metastatic states',
    eMin: 40, eMax: 120,
    litRows: [
      { k: 'Healthy gastric wall', v: '40 – 70 kPa',  type: 'healthy' },
      { k: 'Metastatic tumour',    v: '70 – 120 kPa', type: 'patho'   },
    ],
  },
  kidney: {
    name: 'Kidney',
    subtitle: 'Renal parenchyma — cortex and medulla',
    eMin: 5, eMax: 18,
    litRows: [
      { k: 'Cortex (healthy)',  v: '5 – 12 kPa', type: 'healthy' },
      { k: 'Medulla (healthy)', v: '8 – 18 kPa', type: 'healthy' },
    ],
  },
  prostate: {
    name: 'Prostate',
    subtitle: 'Glandular tissue — healthy and cancerous',
    eMin: 20, eMax: 100,
    litRows: [
      { k: 'Healthy prostate', v: '20 – 45 kPa',  type: 'healthy' },
      { k: 'Prostate cancer',  v: '45 – 100 kPa', type: 'patho'   },
    ],
  },
  muscle: {
    name: 'Skeletal muscle',
    subtitle: 'Passive and active loading — longitudinal axis',
    eMin: 8, eMax: 150,
    litRows: [
      { k: 'Relaxed (passive)',    v: '8 – 30 kPa',   type: 'healthy' },
      { k: 'Contracted (active)',  v: '60 – 150 kPa', type: 'healthy' },
    ],
  },
  adipose: {
    name: 'Adipose tissue',
    subtitle: 'Subcutaneous and visceral fat',
    eMin: 2, eMax: 10,
    litRows: [
      { k: 'Subcutaneous fat', v: '2 – 6 kPa',  type: 'healthy' },
      { k: 'Visceral fat',     v: '5 – 10 kPa', type: 'healthy' },
    ],
  },
};

// Phantom database
// Update this array when new phantoms are added (e.g. the 2 gap-bridging ones).
const PHANTOMS = [
  { label: 'EF10_100T',   material: 'EcoFlex 00-10', thinner: '100%',   modulus: 5.42,   sd: 0.77 },
  { label: 'EF10_87_5T',  material: 'EcoFlex 00-10', thinner: '87.5%',  modulus: 7.92,   sd: 0.26 },
  { label: 'EF10_75T',    material: 'EcoFlex 00-10', thinner: '75%',    modulus: 8.81,   sd: 0.12 },
  { label: 'EF10_62_5T',  material: 'EcoFlex 00-10', thinner: '62.5%',  modulus: 12.17,  sd: 0.52 },
  { label: 'EF10_50T',    material: 'EcoFlex 00-10', thinner: '50%',    modulus: 15.52,  sd: 0.40 },
  { label: 'EF10_37_5T',  material: 'EcoFlex 00-10', thinner: '37.5%',  modulus: 19.37,  sd: 0.83 },
  { label: 'EF10_25T',    material: 'EcoFlex 00-10', thinner: '25%',    modulus: 27.39,  sd: 0.79 },
  { label: 'EF10_12_5T',  material: 'EcoFlex 00-10', thinner: '12.5%',  modulus: 37.30,  sd: 1.28 },
  { label: 'EF10_0T',     material: 'EcoFlex 00-10', thinner: '0%',     modulus: 54.21,  sd: 2.38 },
  { label: 'EF30_12_5T',  material: 'EcoFlex 00-30', thinner: '12.5%',  modulus: 73.18,  sd: 1.17 },
  { label: 'EF30_0T',     material: 'EcoFlex 00-30', thinner: '0%',     modulus: 97.26,  sd: 4.16 },
  { label: 'EF50_12_5T',  material: 'EcoFlex 00-50', thinner: '12.5%',  modulus: 111.10, sd: 6.44 },
  { label: 'EF50_0T',     material: 'EcoFlex 00-50', thinner: '0%',     modulus: 152.70, sd: 4.80 },
  // ── Add new phantoms below this line ──────────────────────────────────────
  // { label: 'EF30_25T', material: 'EcoFlex 00-30', thinner: '25%', modulus: XX.XX, sd: X.XX },
];

// ════════════════════════════════════════════════════════
// STATE
// ════════════════════════════════════════════════════════
let selectedOrgan   = null;
let selectedPhantom = null;

// ════════════════════════════════════════════════════════
// ORGAN SELECTION
// ════════════════════════════════════════════════════════
function selectOrgan(key) {
  // Deactivate previous organ
  if (selectedOrgan) {
    document.getElementById('org-' + selectedOrgan)?.classList.remove('active');
  }
  selectedOrgan   = key;
  selectedPhantom = null;
  document.getElementById('org-' + key)?.classList.add('active');

  const organ = ORGANS[key];

  // Show data panel
  document.getElementById('empty-state').style.display = 'none';
  document.getElementById('data-panel').style.display  = 'block';

  // Header
  document.getElementById('organ-name').textContent     = organ.name;
  document.getElementById('organ-subtitle').textContent = organ.subtitle;
  document.getElementById('organ-illus').innerHTML      = ILLUS[key] || '';

  // Stiffness bar
  const pMin = ((organ.eMin / SCALE_MAX) * 100).toFixed(1);
  const pWid = Math.max(2, ((organ.eMax - organ.eMin) / SCALE_MAX) * 100).toFixed(1);
  document.getElementById('e-min').textContent    = organ.eMin + ' kPa';
  document.getElementById('e-max').textContent    = organ.eMax + ' kPa';
  document.getElementById('e-bar').style.left     = pMin + '%';
  document.getElementById('e-bar').style.width    = pWid + '%';

  // Literature rows
  document.getElementById('lit-rows').innerHTML =
    organ.litRows.map(r => `
      <div class="lit-row">
        <span class="lit-key">${r.k}
          <span class="badge ${r.type === 'healthy' ? 'badge-healthy' : 'badge-patho'}">
            ${r.type === 'healthy' ? 'healthy' : 'pathological'}
          </span>
        </span>
        <span class="lit-val">${r.v}</span>
      </div>`).join('')
    + (organ.note ? `<p class="note-text">${organ.note}</p>` : '');

  // Matching phantoms
  const matching = PHANTOMS.filter(p => p.modulus >= organ.eMin && p.modulus <= organ.eMax);
  document.getElementById('phantom-grid').innerHTML = matching.length === 0
    ? `<p class="no-phantom">No phantoms fall within this range.
         Nearest: EF10_100T (${PHANTOMS[0].modulus} kPa).</p>`
    : matching.map(p => `
        <div class="phantom-card" id="card-${p.label}" onclick="selectPhantom('${p.label}')">
          <div class="phantom-label">${p.label}</div>
          <div class="phantom-modulus">${p.modulus.toFixed(2)} &plusmn; ${p.sd} kPa</div>
        </div>`).join('');

  // Hide recipe until a phantom is chosen
  document.getElementById('recipe-box').classList.remove('visible');
}

// ════════════════════════════════════════════════════════
// PHANTOM SELECTION
// ════════════════════════════════════════════════════════
function selectPhantom(label) {
  // Keep selected card highlighted
  document.querySelectorAll('.phantom-card').forEach(c => c.classList.remove('selected'));
  document.getElementById('card-' + label)?.classList.add('selected');

  const p = PHANTOMS.find(x => x.label === label);
  if (!p) return;
  selectedPhantom = label;

  // Build recipe
  document.getElementById('recipe-title').textContent = 'Fabrication recipe — ' + p.label;
  document.getElementById('recipe-rows').innerHTML = [
    { k: 'Silicone family', v: p.material                          },
    { k: 'Part A',          v: '50 parts by weight'                },
    { k: 'Part B',          v: '50 parts by weight'                },
    { k: 'Thinner',         v: p.thinner + ' of total A+B weight'  },
    { k: 'Target modulus',  v: p.modulus.toFixed(2) + ' &plusmn; ' + p.sd + ' kPa' },
    { k: 'Mould geometry',  v: '&Oslash;50 mm &times; 30 mm cylinder' },
    { k: 'Cure condition',  v: 'Room temperature'                  },
  ].map(r => `
    <div class="recipe-row">
      <span class="recipe-key">${r.k}</span>
      <span class="recipe-val">${r.v}</span>
    </div>`).join('');

  document.getElementById('recipe-box').classList.add('visible');

  // Scroll recipe into view within the right panel
  setTimeout(() => {
    document.getElementById('recipe-box').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, 50);
}
</script>

</body>
</html>
"""

components.html(HTML, height=800, scrolling=False)
