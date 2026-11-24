# Equity valuation: Section 9

Part of the `equity-valuation` skill ([SKILL.md](../SKILL.md)). Section numbers and cross-references (for example 2.6, A.9, T-13) are those of the full standard; the section map in SKILL.md says which file holds each section.

## Contents

- [9.1 Principles](#91-principles)
- [9.2 Provenance tags and citation format](#92-provenance-tags-and-citation-format)
- [9.3 Report template (headings in this order)](#93-report-template-headings-in-this-order)
- [9.4 Required tables](#94-required-tables)
- [9.5 Assumption Register format](#95-assumption-register-format)
- [9.6 Numerical conventions](#96-numerical-conventions)
- [9.7 Confidence rubric](#97-confidence-rubric)
- [9.8 Machine-readable summary (append as a fenced JSON block)](#98-machine-readable-summary-append-as-a-fenced-json-block)
- [9.9 Language](#99-language)

## 9. Reporting standard

### 9.1 Principles

1. **Conclusion first**, then evidence, then method.
2. **Traceable:** every number links to a source ID, a formula or an assumption ID.
3. **Consistent:** the same section order, table IDs, units and conventions in every report, so reports on different companies can be compared side by side.
4. **Complete about uncertainty:** ranges, sensitivities, data gaps and confidence are always shown.
5. **Reproducible:** the report, the calculation script and the data files form one package.

### 9.2 Provenance tags and citation format

- Inline tags after each value: `$394.3bn [F3]`, `4.21% [D1]`, `21.0% [X2]`, `8.4% [C7]`, `3.0% [A4]`.
- **Source Ledger entry:** `ID | Tier | Source | Exact query/locator | As-of / vintage | Retrieved (UTC) | Notes`.
  - fafnir: the tool and its arguments, for example `statements_as_of(symbol=AAPL, statement=income, period=annual, as_of=2026-11-20)`.
  - dismal: the command, for example `dismal fred data DGS10 --start 2026-11-20 --end 2026-11-20 -f json`.
  - EDGAR: company, form, period, accession number, page/note, for example `AAPL 10-K FY2025, 0000320193-25-000xxx, Note 9 Debt`.
  - Web: URL, page title, table name, publication date.
  - fit (in the Computation Register): the full command line, input CSV file names (each CSV's header comment cites its own source IDs), `fit --version`, and the output fields used, for example `C12 | fit curve query --curve ust_2026-11-20.csv --asof 2026-11-20 --interp monotone-convex --tenors 10Y -f json | D1–D11 | par_sa_pct(10Y) = 4.2163%` (illustrative).
- **Computed entry:** `ID | Formula | Inputs (IDs) | Value`.
- **Assumption entry:** see 9.5.

### 9.3 Report template (headings in this order)

```
# [Company] ([TICKER]): [Task] Report
As of [knowledge date] · Price date [date] · Currency [ccy] · Prepared [timestamp]

## 1. Summary
   - Box (T-1): price; fair value point and range (or the relative-value verdict,
     or key decomposition and capital-structure findings, for those tasks);
     upside/downside vs price; primary and cross-check methods; confidence
     (9.7); top 3 value drivers; top 3 risks.
   - Rating, only if the user configured a vocabulary. Default: "Estimated value
     is X% above/below the current price."
   - Thesis in at most 5 bullets, each tied to evidence in the body.
## 2. Company and security
   Identity (security_id, CIK, share class, exchange), business-model summary
   [S], segment mix if known, data-integrity results (Phase 2).
## 3. Historical performance (Module C)
## 4. Capital structure and cost of capital (Module D + A.2)
   Risk-free curve (T-13), debt valuation (T-14), cost-of-capital build (T-12).
## 5. Forecast and assumptions
   Driver table (T-7), Assumption Register reference, scenario definitions.
## 6. Intrinsic valuation (Module A)
   Model choice and rationale; valuation table (T-8); EV-to-equity bridge (T-9);
   sensitivity grids (T-10); scenarios; reverse DCF; cross-check reconciliation.
## 7. Relative valuation (Module B)
   Peer selection log; peer table (T-4); own-history percentiles; justified
   multiples; implied values.
## 8. Valuation synthesis
   Football-field (T-11, plus chart): each method's range vs price; final
   point and range with weighting rationale.
## 9. Risks and what would change the view
   Key risks with the assumption each would move and its value impact (from
   sensitivities).
## 10. Data gaps, limitations and deviations from this standard
## 11. Appendices
   A. Source Ledger · B. Assumption Register · C. Computation Register
   D. Standardized statements (annual + TTM) · E. Methodology notes
   F. Reproducibility: script and data file names, tool versions
## 12. Disclaimer
   "This analysis is for informational purposes. It is not investment advice or
   a recommendation to buy or sell any security. It relies on data whose
   sources are listed in Appendix A, and on assumptions listed in Appendix B
   that may prove wrong."
```

For a single-module task, keep §1, §2, the relevant module section(s), §10, §11 and §12, and mark the other sections "out of scope."

### 9.4 Required tables

| ID | Table | Minimum columns |
|---|---|---|
| T-1 | Summary box | Price, date, FV point, FV low/high, % vs price, methods, confidence, drivers, risks |
| T-2 | Security identity | Ticker, security_id, CIK, ISIN, class, exchange, currency, sector/industry (today's), status |
| T-3 | Data-integrity log | Check, result, evidence ID, action |
| T-4 | Peer comparison | Peer, inclusion reason, mcap, EV, P/E, EV/EBITDA, EV/Sales, P/B, ROIC, op. margin, revenue growth, D/E; then n, median, harmonic mean, p25, p75; target and its percentile |
| T-5 | Driver dashboard | Metric × years (≥ 5 + TTM), peer median, own 10-y median |
| T-6 | Capital structure | Component, book, market/fair, % of capital, cost, source |
| T-7 | Forecast drivers | Driver × forecast years + terminal, with anchor and assumption ID |
| T-8 | DCF/valuation build | Year, revenue, EBIT, NOPAT, D&A, capex, ΔNWC, FCFF (or FCFE/RI), discount factor, PV; TV; total |
| T-9 | EV → equity bridge | Item, amount, source ID |
| T-10 | Sensitivity grids | WACC × g; margin × growth (value per share) |
| T-11 | Football field | Method, low, base, high, vs price |
| T-12 | Cost of capital build | r_f, ERP, β (method, SE, R²), CRP, r_e, r_d, t, weights, WACC, each with a source ID |
| T-13 | Risk-free curve | Tenor, quote type, input yield [D], zero (cc), par (sa), forward, discount factor, repricing error (bp); interpolation and extrapolation used |
| T-14 | Debt valuation | Instrument, face, coupon, maturity, mark (price or z-spread with source), clean price, market value, duration, DV01; totals vs book `total_debt` [F]; out-of-scope instruments and their treatment |

### 9.5 Assumption Register format

| ID | Assumption | Value | Type (forecast / methodological / parameter) | Anchor evidence (IDs) | Rationale | Sensitivity (value Δ for ±1 step) |
|---|---|---|---|---|---|---|
| A1 | Terminal nominal growth *(illustrative row; the figures are placeholders, not data)* | 3.0% | parameter | D1 (DGS10 4.2%), D3 (T10YIE 2.3%), D4 (GDPPOT 10-y CAGR 1.9%) | Below r_f; ≈ expected inflation + sub-potential real growth for a mature firm | ±0.5% → +8% / −6% |

Rules: every assumption cites at least one anchor, or is marked "no direct evidence; judgment" with a reason and is then shown in a sensitivity. User-supplied assumptions are tagged "user-supplied."

### 9.6 Numerical conventions

- Currency amounts in millions with one decimal ($394,328.0m) in tables. Per-share values to 2 decimals. Ratios and percentages to 1 decimal (yields and costs of capital to 2: 8.47%). Multiples to 1 decimal followed by "x" (24.6x).
- Dates in ISO format (YYYY-MM-DD). Fiscal periods as FY2025, 2025-Q3 or TTM 2026-Q3, with the fiscal year-end month stated once.
- Negative values in parentheses in tables. "n.m." for not meaningful; "n.a." for not available. Never a blank.
- Label every figure's basis: TTM / FY / forward; basic / diluted; book / market; reported / adjusted.
- Round only at presentation; compute at full precision (fafnir exact decimals).

### 9.7 Confidence rubric

Report **High**, **Medium** or **Low** with the reasons:

| Factor | High | Low |
|---|---|---|
| Data completeness | No gap items in 2.6 affect value by > 5% | A material gap was filled with a proxy |
| Model agreement | Primary vs cross-checks within 15% | > 30% apart |
| Sensitivity | FV range width < 30% of point | > 60% |
| TV share | < 60% | > 80% |
| Business predictability | Stable ROIC, low earnings volatility (Module C) | Loss-making, cyclical peak/trough, restructuring |
| Peer quality | ≥ 8 close peers | < 5 or weak comparability |

Overall confidence is the lowest factor, unless the report explains why that factor is not binding.

### 9.8 Machine-readable summary (append as a fenced JSON block)

```json
{
  "schema": "equity-valuation-report/1.0",
  "security": {"ticker": "", "security_id": 0, "cik": "", "share_class": "", "currency": ""},
  "as_of": "YYYY-MM-DD", "price_date": "YYYY-MM-DD", "price": 0.0,
  "tasks": ["fair_value", "relative_value", "decomposition", "capital_structure"],
  "fair_value": {"point": 0.0, "low": 0.0, "high": 0.0, "vs_price_pct": 0.0,
                 "primary_method": "", "cross_checks": [{"method": "", "value": 0.0}],
                 "weights": {}},
  "cost_of_capital": {"rf": 0.0, "erp": 0.0, "beta": 0.0, "beta_method": "", "re": 0.0,
                      "rd_pre_tax": 0.0, "rd_method": "market|rating|synthetic",
                      "credit_spread_bp": 0.0, "tax_marginal": 0.0, "wd": 0.0, "wacc": 0.0},
  "rates_curve": {"source": "dismal fred", "builder": "fit", "fit_version": "",
                  "interp": "monotone-convex", "max_repricing_error_bp": 0.0,
                  "par_10y": 0.0, "zero_10y_cc": 0.0, "fwd_10y10y": 0.0},
  "debt": {"book_total": 0.0, "fair_value": 0.0, "fair_value_method": "fit|10-K|book",
           "duration": 0.0, "dv01": 0.0, "out_of_scope_instruments": []},
  "terminal": {"g": 0.0, "roic_new": 0.0, "tv_share_pct": 0.0},
  "relative": {"peer_count": 0, "multiples": {"pe": {"target": 0.0, "median": 0.0, "pct_rank": 0.0}}},
  "decomposition": {"roe": 0.0, "dupont5": {"tax_burden": 0.0, "interest_burden": 0.0,
                    "ebit_margin": 0.0, "asset_turnover": 0.0, "leverage": 0.0},
                    "roic": 0.0, "roic_minus_wacc": 0.0, "sustainable_g": 0.0},
  "capital_structure": {"net_debt_to_ebitda": 0.0, "interest_coverage": 0.0,
                        "synthetic_rating": "", "optimal_debt_ratio_range": [0.0, 0.0]},
  "confidence": "high|medium|low",
  "data_gaps": [{"item": "", "impact": "", "treatment": ""}],
  "sources": [{"id": "F1", "tier": 1, "locator": "", "retrieved_utc": ""}],
  "assumptions": [{"id": "A1", "name": "", "value": 0.0, "anchors": ["D1"]}]
}
```

Rates are decimals (0.0847). Values are in the valuation currency, per share unless the key says otherwise.

### 9.9 Language

- Use: "estimated", "implies", "the evidence suggests", "under these assumptions". Avoid: "will", "guaranteed", "clearly undervalued".
- Attribute every claim about the company's strategy or outlook to its source ("management guided to … [S4]").
- Quote filings sparingly (short excerpts only) and paraphrase otherwise.
