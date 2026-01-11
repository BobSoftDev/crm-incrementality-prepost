# utils/narrative.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import math

def _fmt_num(x: float, decimals: int = 0) -> str:
    try:
        if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
            return "N/A"
        fmt = f"{{:,.{decimals}f}}"
        return fmt.format(float(x))
    except Exception:
        return "N/A"

def _direction(x: float) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "unknown"
    if x > 0:
        return "positive"
    if x < 0:
        return "negative"
    return "neutral"

def _safe_float(x, default=0.0) -> float:
    try:
        if x is None:
            return default
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except Exception:
        return default

@dataclass
class Narrative:
    headline: str
    bullets: list[str]
    recommendation: str
    caveat: str

def render_narrative(n: Narrative, expanded: bool = True) -> None:
    import streamlit as st
    with st.expander("Auto narrative (insights + action)", expanded=expanded):
        st.markdown(f"**{n.headline}**")
        for b in n.bullets:
            st.markdown(f"- {b}")
        st.markdown(f"**Recommendation:** {n.recommendation}")
        st.caption(n.caveat)

# ---------------------------
# Page 1: Summary
# ---------------------------
def narrative_summary(total_inc_rev: float,
                      total_inc_txn: float,
                      avg_delta_aov: float,
                      top_segment: str) -> Narrative:
    total_inc_rev = _safe_float(total_inc_rev)
    total_inc_txn = _safe_float(total_inc_txn)
    avg_delta_aov = _safe_float(avg_delta_aov)

    headline = f"Overall incrementality is {_direction(total_inc_rev)} ({_fmt_num(total_inc_rev)} in incremental revenue)."

    bullets = [
        f"Incremental transactions: {_fmt_num(total_inc_txn)} (direction: {_direction(total_inc_txn)}).",
        f"Average ΔAOV: {_fmt_num(avg_delta_aov, 2)}.",
        f"Top contributing RFM segment: **{top_segment}**."
    ]

    recommendation = (
        "Prioritize targeting and frequency optimization for segments with positive lift; "
        "for segments with negative lift, test lower contact pressure and different message/offer mechanics."
    )

    caveat = (
        "This is a pre/post estimate without a control group: interpret as directional lift. "
        "Seasonality, concurrent promotions, and targeting bias can influence results."
    )
    return Narrative(headline, bullets, recommendation, caveat)

# ---------------------------
# Page 2: Customer Value
# ---------------------------
def narrative_value_split(inc_all: float, inc_hv: float, inc_lv: float,
                          hv_label="High Value", lv_label="Low Value") -> Narrative:
    inc_all = _safe_float(inc_all)
    inc_hv = _safe_float(inc_hv)
    inc_lv = _safe_float(inc_lv)

    headline = f"Incremental revenue by customer value is {_direction(inc_all)} overall ({_fmt_num(inc_all)})."

    bullets = [
        f"{hv_label}: {_fmt_num(inc_hv)} (direction: {_direction(inc_hv)}).",
        f"{lv_label}: {_fmt_num(inc_lv)} (direction: {_direction(inc_lv)}).",
        "A strongly negative Low Value result often indicates offer/message mismatch or excessive contact pressure."
    ]

    recommendation = (
        "For Low Value, test simpler messaging and stricter contact limits; "
        "for High Value, focus on retention and cross-sell while monitoring cannibalization."
    )

    caveat = (
        "Negative incrementality means POST < PRE baseline within the 7-day impact window; "
        "it is not causal proof without a control group."
    )
    return Narrative(headline, bullets, recommendation, caveat)

# ---------------------------
# Page 3: Active vs Non-Active
# ---------------------------
def narrative_active_vs_nonactive(active_rev: float, nonactive_rev: float,
                                  active_txn: float, nonactive_txn: float) -> Narrative:
    active_rev = _safe_float(active_rev)
    nonactive_rev = _safe_float(nonactive_rev)
    active_txn = _safe_float(active_txn)
    nonactive_txn = _safe_float(nonactive_txn)

    headline = (
        f"Active group is {_direction(active_rev)} ({_fmt_num(active_rev)}), "
        f"Non-Active is {_direction(nonactive_rev)} ({_fmt_num(nonactive_rev)})."
    )

    bullets = [
        f"Active incremental transactions: {_fmt_num(active_txn)} (direction: {_direction(active_txn)}).",
        f"Non-Active incremental transactions: {_fmt_num(nonactive_txn)} (direction: {_direction(nonactive_txn)}).",
        "If Non-Active is negative, it may reflect baseline distortion, poor offer fit, or an overly broad reactivation push."
    ]

    recommendation = (
        "Split communication by lifecycle: grow frequency/AOV for Active, "
        "and use reactivation-specific mechanics with stricter contact limits for Non-Active."
    )

    caveat = (
        "Without a control group, segments may differ in seasonality and purchase propensity; "
        "validate via sensitivity testing (pre/post window variants) and additional diagnostics."
    )
    return Narrative(headline, bullets, recommendation, caveat)

# ---------------------------
# Page 4: RFM Deep Dive
# ---------------------------
def narrative_rfm(top_seg: str, top_rev: float, total_rev: float,
                  bottom_seg: Optional[str] = None, bottom_rev: Optional[float] = None) -> Narrative:
    top_rev = _safe_float(top_rev)
    total_rev = _safe_float(total_rev)
    bottom_rev_val = _safe_float(bottom_rev) if bottom_rev is not None else None

    share = (top_rev / total_rev) if total_rev != 0 else None
    share_txt = f"{_fmt_num(share*100, 1)}%" if share is not None else "N/A"

    headline = f"Top RFM segment is **{top_seg}** with {_fmt_num(top_rev)} incremental revenue (share: {share_txt})."

    bullets = [
        f"Total incremental revenue across segments: {_fmt_num(total_rev)}.",
        "RFM ranking helps prioritize budget and message frequency by customer lifecycle/value proxies."
    ]
    if bottom_seg is not None:
        bullets.append(f"Weakest segment: **{bottom_seg}** with {_fmt_num(bottom_rev_val)} (direction: {_direction(bottom_rev_val)}).")

    recommendation = (
        "Scale the best-performing segment using relevant triggers and offers; "
        "for underperforming segments, reduce contact pressure and adjust mechanics (e.g., education → offer)."
    )

    caveat = (
        "RFM segments are proxy-based (e.g., trailing 90 days). If the segmentation definition changes over time, "
        "month-to-month comparisons may be unstable."
    )
    return Narrative(headline, bullets, recommendation, caveat)

# ---------------------------
# Page 5: Diagnostics
# ---------------------------
def narrative_diagnostics(rows: int, customers: int,
                         zero_pre: int, zero_post: int,
                         inc_rev_median: Optional[float] = None) -> Narrative:
    rows = int(rows) if rows is not None else 0
    customers = int(customers) if customers is not None else 0
    zero_pre = int(zero_pre) if zero_pre is not None else 0
    zero_post = int(zero_post) if zero_post is not None else 0

    pre_pct = (zero_pre / rows) if rows else None
    post_pct = (zero_post / rows) if rows else None

    headline = f"Coverage check: {rows:,} rows, {customers:,} unique customers."

    bullets = [
        f"Zero PRE revenue rows: {zero_pre:,} ({_fmt_num(pre_pct*100, 1) + '%' if pre_pct is not None else 'N/A'}).",
        f"Zero POST revenue rows: {zero_post:,} ({_fmt_num(post_pct*100, 1) + '%' if post_pct is not None else 'N/A'})."
    ]
    if inc_rev_median is not None:
        bullets.append(f"Median incremental revenue: {_fmt_num(_safe_float(inc_rev_median), 2)}.")

    recommendation = (
        "If zero PRE/POST shares are high, review window definitions (e.g., 28-day pre, 7-day post) and anchor exposure logic. "
        "Run sensitivity tests (pre: 14/28/56; post: 3/7/14) to validate robustness."
    )

    caveat = (
        "These diagnostics are row-based; if the fact table is not unique by (customer_id, month_id), counts may be inflated."
    )
    return Narrative(headline, bullets, recommendation, caveat)
