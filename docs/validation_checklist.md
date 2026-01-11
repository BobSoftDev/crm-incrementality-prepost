# Incrementality Validation Checklist

This checklist ensures results are **robust, interpretable, and decision-safe** before executive presentation.

---

## A. Data Integrity
- [ ] One row per customer-month in fact tables
- [ ] No duplicate exposures per customer per anchor
- [ ] Numeric fields properly typed (no text sums)
- [ ] Month scoping consistent across all pages

---

## B. Window Sanity
- [ ] PRE window = 28 days (default)
- [ ] POST window = 7 days
- [ ] Anchor exposure date correctly assigned
- [ ] Customers with no PRE or POST data reviewed

---

## C. Sensitivity Testing
Run and compare results for:
- [ ] PRE: 14 / 28 / 56 days
- [ ] POST: 3 / 7 / 14 days

Confirm:
- Direction of lift remains stable
- Major segments do not flip sign arbitrarily

---

## D. Zero Revenue Diagnostics
- [ ] % Zero PRE revenue rows reviewed
- [ ] % Zero POST revenue rows reviewed
- [ ] High zero shares explained or excluded

---

## E. Segment Consistency
- [ ] Top segment calculated from same scope as totals
- [ ] Positive and negative contributions separated
- [ ] “Top > Net” explained via negative offsets

---

## F. Outlier Review
- [ ] Top 20 positive customer-month rows reviewed
- [ ] Top 20 negative customer-month rows reviewed
- [ ] Outliers explainable (promos, returns, bulk orders)

---

## G. Narrative Alignment
- [ ] Executive narrative matches numbers shown
- [ ] Time scope (annual vs monthly) clearly labeled
- [ ] Limitations explicitly stated

---

## Final Gate
Only present results if:
- [ ] Direction is stable across sensitivity tests
- [ ] Negative segments are acknowledged
- [ ] Actions are framed as **tests**, not final decisions
