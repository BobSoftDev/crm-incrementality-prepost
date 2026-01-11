<!-- README.md (HTML-tagged) -->

<h1>CRM Incrementality (Pre/Post Baseline, No Control Group)</h1>

<p>
This repository contains an end-to-end, production-like workflow to estimate <b>directional CRM incrementality</b>
in an omnichannel retail context using a <b>pre/post behavioral baseline</b> approach (no control group).
</p>

<hr/>

<h2>What this project delivers</h2>
<ul>
  <li><b>Databricks Lakehouse</b> pipeline with <code>00_bronze</code>, <code>01_silver</code>, <code>02_gold</code> layers</li>
  <li><b>Gold exports</b> to CSV for BI consumption</li>
  <li><b>Streamlit app</b> mirroring the KPI narrative and dashboards (with automatic executive narratives)</li>
  <li><b>Power BI model</b> (PBIX) + DAX measures + Tabular Editor scripts</li>
  <li><b>PPT storyline</b> aligned to an executive (McKinsey-style) narrative</li>
</ul>

<hr/>

<h2>Method summary (executive)</h2>
<p>
We estimate incrementality by comparing each customer’s <b>POST</b> behavior after CRM exposure to their own
historical <b>PRE</b> baseline, then scaling by the post period length.
</p>

<ul>
  <li><b>Impact window (POST):</b> 7 days</li>
  <li><b>Baseline window (PRE):</b> 28 days (default)</li>
  <li><b>Core formula:</b> <code>Incremental Revenue = (POST behavior − PRE baseline) × POST period length</code></li>
</ul>

<p>
<b>Important:</b> Without a control group, results should be treated as <b>directional lift</b> (not causal proof).
</p>

<hr/>

<h2>Key metrics</h2>
<ul>
  <li><b>Average Order Value per day</b> (proxy)</li>
  <li><b>Transaction count</b></li>
  <li><b>Purchase frequency</b> (proxy: active purchase days / window days)</li>
</ul>

<hr/>

<h2>Segmentation cuts</h2>
<ul>
  <li><b>RFM segments</b></li>
  <li><b>Active vs Non-Active</b></li>
  <li><b>High Value vs Low Value</b></li>
</ul>

<hr/>

<h2>Repository structure</h2>
<ul>
  <li><code>databricks/</code> – SQL DDL + transformations for Bronze/Silver/Gold</li>
  <li><code>scripts/</code> – Python utilities (synthetic data, uploads, exports)</li>
  <li><code>streamlit_app/</code> – Streamlit dashboard + auto narratives</li>
  <li><code>powerbi/</code> – PBIX, DAX measures, Tabular Editor scripts, theme</li>
  <li><code>docs/</code> – methodology one-pager, limitations, storyline</li>
  <li><code>data/</code> – local synthetic samples (optional) and exported gold CSVs (usually gitignored)</li>
</ul>

<hr/>

<h2>Quick start (local)</h2>

<h3>1) Python environment</h3>
<ol>
  <li>Create a virtual environment</li>
  <li>Install dependencies for Streamlit</li>
</ol>

<pre><code>cd streamlit_app
pip install -r requirements.txt
</code></pre>

<h3>2) Put Gold exports where Streamlit expects them</h3>
<p>
By default, the app reads CSVs from:
</p>
<pre><code>data/gold_exports/
</code></pre>

<p>
Exported files should include (names can be adjusted, but must match the app’s loaders):
</p>
<ul>
  <li><code>agg_incrementality_month.csv</code></li>
  <li><code>agg_incrementality_active_value.csv</code></li>
  <li><code>agg_incrementality_rfm.csv</code></li>
  <li><code>fact_customer_month_incrementality.csv</code></li>
</ul>

<h3>3) Run Streamlit</h3>
<pre><code>streamlit run app.py
</code></pre>

<hr/>

<h2>Databricks run order (high level)</h2>
<ol>
  <li>Create catalog/schema + volumes (<code>databricks/volumes/create_volumes.sql</code>)</li>
  <li>Create Bronze tables + ingest</li>
  <li>Create Silver transformations</li>
  <li>Create Gold fact + aggregations</li>
  <li>Export Gold to CSV files for BI</li>
</ol>

<hr/>

<h2>Power BI</h2>
<ul>
  <li>Open <code>powerbi/CRM_Incrementality.pbix</code></li>
  <li>Refresh data pointing to exported Gold CSVs</li>
  <li>Measures live in <code>powerbi/dax/</code></li>
  <li>Tabular Editor scripts live in <code>powerbi/tabular_editor/</code></li>
</ul>

<hr/>

<h2>Interpreting “Top segment exceeds net total”</h2>
<p>
In segmented incrementality, negative segments can offset positive gains.
Therefore, the leading segment can exceed the <b>net</b> incremental total in a given month.
</p>

<hr/>

<h2>Limitations</h2>
<ul>
  <li>No randomized control group → directional results, not causal proof</li>
  <li>Seasonality and concurrent promotions can bias the estimate</li>
  <li>Targeting bias can inflate observed lift</li>
  <li>Segment definitions (e.g., RFM) may shift over time</li>
</ul>

<hr/>

<h2>Validation checklist</h2>
<ul>
  <li>Run sensitivity tests: PRE (14/28/56) × POST (3/7/14)</li>
  <li>Check Zero PRE/POST revenue shares</li>
  <li>Review outliers (top positive and negative customer-month rows)</li>
  <li>Confirm month scoping consistency across pages and aggregates</li>
</ul>

<hr/>

<h2>License</h2>
<p>
Add your license here (MIT, Apache-2.0, or internal).
</p>
