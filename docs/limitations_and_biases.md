# Limitations and Biases — CRM Incrementality

This document outlines the **known limitations** of the pre/post incrementality approach and how they should be handled in decision-making.

---

## 1. No Randomized Control Group
**Limitation**  
The method does not include a true control group.

**Implication**  
Results are **directional**, not causal proof.

**Mitigation**
- Use findings to prioritize tests
- Complement with A/B tests where feasible

---

## 2. Seasonality Effects
**Limitation**  
Customer behavior may change due to seasonality rather than CRM exposure.

**Implication**  
PRE baseline may not fully represent the counterfactual.

**Mitigation**
- Use rolling windows
- Compare multiple months
- Run sensitivity tests on window lengths

---

## 3. Concurrent Promotions and Campaign Overlap
**Limitation**  
Other marketing activities may coincide with CRM exposure.

**Implication**  
Observed lift may be inflated or deflated.

**Mitigation**
- Exclude heavy promo periods where needed
- Annotate major campaigns in analysis
- Compare across quieter periods

---

## 4. Targeting Bias
**Limitation**  
CRM campaigns often target customers with higher purchase propensity.

**Implication**  
Baseline may already reflect higher expected behavior.

**Mitigation**
- Analyze negative segments explicitly
- Compare Active vs Non-Active splits
- Use conservative interpretation

---

## 5. Regression to the Mean
**Limitation**  
Customers selected after extreme behavior may naturally revert.

**Implication**  
Short-term uplift may not persist.

**Mitigation**
- Track trends over time
- Avoid single-month decisions
- Monitor post-impact decay

---

## 6. Segment Definition Instability
**Limitation**  
RFM and value segments may change month-to-month.

**Implication**  
Segment-level comparisons can appear volatile.

**Mitigation**
- Freeze segment definitions per month
- Track transitions separately
- Focus on directional patterns

---

## 7. Negative Segment Offsets
**Limitation**  
Some segments may show strong negative incrementality.

**Implication**  
Top segments can exceed net totals.

**Mitigation**
- Decompose results into positive and negative contributions
- Use “share of positive contribution” for executive reporting

---

## Executive Guidance
Treat this methodology as a **navigation instrument**, not a courtroom proof.  
It tells you **where to look and what to fix**, not absolute truth.
