"""
geography.py
------------
Risk-geography lookup tables used by the decision pipeline.

Why this exists
---------------
The raw Isolation Forest is geography-blind: it treats every pincode as
equal. In reality, Aadhaar enrollment fraud is overwhelmingly concentrated
near India's **porous land borders** (Nepal, Bangladesh, Myanmar, Pakistan,
China) because those are the corridors used for document-laundering and
proxy enrollment. Conversely, low-population Union Territories like the
Andaman & Nicobar Islands record so few enrollments per day that any
random blip looks like a 3σ event — producing a flood of false positives.

This module encodes that domain knowledge so the decision layer can:
  1. Skip flagging records from very-low-volume UTs (tiny islands).
  2. Boost the priority of flags from border states so the "Top Flag"
     report the frontend generates lands on a genuinely sensitive area
     (West Bengal, Assam, Punjab, …) rather than Andaman & Nicobar.

All names are compared after `str.strip().str.title()` normalisation,
matching what the preprocessor applies.
"""

from __future__ import annotations


# ── High-priority border states / UTs ───────────────────────────────
# Indian states sharing land borders with neighbouring countries that
# have historically been routes for undocumented migration / identity
# laundering. Source: MHA border-area list (abridged).
BORDER_STATES: frozenset[str] = frozenset({
    # Bangladesh border
    "West Bengal", "Assam", "Tripura", "Mizoram", "Meghalaya",
    # Myanmar border
    "Manipur", "Nagaland", "Arunachal Pradesh",
    # Nepal border
    "Bihar", "Uttar Pradesh", "Uttarakhand", "Sikkim",
    # Pakistan border
    "Punjab", "Rajasthan", "Gujarat",
    # Pakistan + China border
    "Jammu And Kashmir", "Ladakh",
    # China border
    "Himachal Pradesh",
})


# ── Low-population UTs where sample noise dominates ─────────────────
# These territories record so few daily enrollments per pincode that
# rolling-window statistics become unreliable; suppress them unless the
# signal is overwhelming (very high severity with real volume).
LOW_POPULATION_TERRITORIES: frozenset[str] = frozenset({
    "Andaman And Nicobar Islands",
    "Lakshadweep",
    "Dadra And Nagar Haveli And Daman And Diu",
})


def is_border_state(state: str | None) -> bool:
    if not state:
        return False
    return state.strip().title() in BORDER_STATES


def is_low_population_territory(state: str | None) -> bool:
    if not state:
        return False
    return state.strip().title() in LOW_POPULATION_TERRITORIES


def priority_score(state: str | None, severity: str, anomaly_score: float,
                   total_enrollments: int) -> tuple:
    """
    Sort key used by `decision_logic.route()` to order red flags so that
    the most actionable records sit at the top of the list.

    Ordering (descending priority):
        1. Severity bucket               HIGH > MEDIUM > LOW
        2. Border-state bonus            True > False
        3. Anomaly score                 more negative = more suspicious
        4. Volume                        higher = more impactful
    Returned as a tuple suitable for `sorted(..., reverse=True)`.
    """
    severity_rank = {"HIGH": 2, "MEDIUM": 1, "LOW": 0}.get(severity, 0)
    return (
        severity_rank,
        1 if is_border_state(state) else 0,
        -float(anomaly_score),   # more negative score → higher priority
        int(total_enrollments),
    )
