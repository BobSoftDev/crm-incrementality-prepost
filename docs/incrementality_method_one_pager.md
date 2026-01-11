# CRM Incrementality Measurement — One-Pager

## Purpose
This document describes the **directional CRM incrementality methodology** used to estimate the business impact of CRM communications when a randomized control group is not available.

The objective is to support **decision-making and prioritization**, not to provide causal proof.

---

## Core Concept (No Control Group)
Incrementality is estimated by comparing each customer’s behavior **after CRM exposure (POST)** to their **own historical behavior (PRE baseline)**.

This within-customer comparison reduces structural bias and enables scalable measurement across the full customer base.

---

## Key Formula
**Incremental Revenue (proxy)**  
Incremental Revenue = (POST revenue per day − PRE revenue per day) × POST period length

yaml
Copy code

---

## Time Windows
- **PRE baseline window:** 28 days before the anchor exposure date (default)
- **POST impact window:** 7 days starting from the anchor exposure date

> These defaults are chosen to balance stability (PRE) and responsiveness (POST) and are validated through sensitivity testing.

---

## Metrics Used
- **Incremental Revenue (proxy)**
- **Incremental Transactions**
- **Purchase Frequency (proxy)**  
  Active purchase days ÷ window days
- **Average Order Value (proxy)**  
  Revenue ÷ transactions

All metrics are calculated at **customer-month grain** and aggregated for reporting.

---

## Segmentation Cuts
Results are analyzed across multiple business-relevant dimensions:
- **RFM segments**
- **Active vs Non-Active customers**
- **High Value vs Low Value customers**

Segmentation is used for **prioritization and optimization**, not causal attribution.

---

## Interpretation Guidance
- Positive incrementality → POST behavior exceeds historical baseline
- Negative incrementality → POST behavior underperforms baseline
- A single segment can exceed the net total if other segments are negative

---

## What This Method Is Good For
- Identifying **where CRM creates value**
- Detecting **segments where CRM destroys value**
- Prioritizing **targeting, frequency, and offer strategy**
- Supporting **test-and-learn roadmaps**

---

## What This Method Is NOT
- A randomized experiment
- A causal attribution model
- A replacement for A/B testing

---

## Executive Takeaway
This method provides a **transparent, scalable, and decision-ready view** of CRM performance, suitabl
