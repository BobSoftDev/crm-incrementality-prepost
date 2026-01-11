import streamlit as st
from utils.narrative import render_narrative, Narrative

st.title("Definitions")

render_narrative(
    Narrative(
        headline="How to read these results",
        bullets=[
            "This is a pre/post model without a control group: treat outputs as directional lift.",
            "Negative incrementality means POST < PRE baseline within the 7-day impact window.",
            "Segments help prioritize actions; they do not prove causality."
        ],
        recommendation="Use findings to drive iterative tests: frequency, targeting, and message/offer mechanics.",
        caveat="For causal inference, you need a control design or a strong quasi-experimental method."
    ),
    expanded=False
)

st.markdown("""
### Core Concept (No Control Group)
This model estimates **directional incrementality** by comparing each customer’s behavior
**after CRM exposure** vs their **own historical baseline**.

**Incremental Revenue (proxy)**  
**Incremental Revenue = (POST revenue/day − PRE revenue/day) × 7**

### Windows
- **PRE baseline**: 28 days before the anchor exposure date (default)
- **POST impact**: 7 days starting on the anchor exposure date

### Metrics
- **Transactions count**: number of transactions in the window
- **Purchase frequency (proxy)**: active purchase days / window days
- **AOV (proxy)**: revenue / transactions

### Segments
- **Active vs Non-Active**: from customer attributes (flag)
- **High-value vs Low-value**: from customer attributes (flag)
- **RFM**: simplified monthly RFM based on trailing 90 days:
  - Recency: days since last purchase
  - Frequency: transaction count
  - Monetary: revenue

### Limitations
- No randomized control → results are **directional**, not causal proof
- Promotions/seasonality may influence observed lift
- CRM targeting bias may inflate estimates
""")
