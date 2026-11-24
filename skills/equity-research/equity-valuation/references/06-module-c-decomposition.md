# Equity valuation: Section 6 (Module C)

Part of the `equity-valuation` skill ([SKILL.md](../SKILL.md)). Section numbers and cross-references (for example 2.6, A.9, T-13) are those of the full standard; the section map in SKILL.md says which file holds each section.

## Contents

- [C.1 DuPont](#c1-dupont)
- [C.2 ROIC tree](#c2-roic-tree)
- [C.3 Margin structure](#c3-margin-structure)
- [C.4 Working capital and cash conversion](#c4-working-capital-and-cash-conversion)
- [C.5 Growth decomposition](#c5-growth-decomposition)
- [C.6 Earnings quality](#c6-earnings-quality)
- [C.7 Output](#c7-output)

## 6. Module C: Decomposition of profitability and growth

All metrics are computed for ≥ 5 fiscal years plus TTM, and benchmarked to the peer median and own history. Use average balances for return ratios (2.3.2).

### C.1 DuPont

- **3-step:** ROE = (NI / Revenue) × (Revenue / Avg Assets) × (Avg Assets / Avg Equity).
- **5-step:** ROE = (NI / EBT) **tax burden** × (EBT / EBIT) **interest burden** × (EBIT / Revenue) **EBIT margin** × (Revenue / Avg Assets) **asset turnover** × (Avg Assets / Avg Equity) **leverage**.
  - Map: NI = `net_income` (or `net_income_common` for common ROE; state which and keep it consistent), EBT = `income_before_tax`, EBIT = `ebit`, equity = `total_equity_parent`.
  - Check: the product of the components equals the directly computed ROE within rounding. Note that NCI makes the leverage term approximate; disclose.
- **Change attribution:** attribute ΔROE between periods to each factor using log decomposition (ln ROE = Σ ln factor_i, so the contributions sum exactly). Present a waterfall table.
- **Leverage-separated (operating) decomposition** (Penman / Nissim-Penman): ROE = RNOA + FLEV × (RNOA − NBC), where RNOA = NOPAT / avg net operating assets, FLEV = avg net debt / avg equity, NBC = after-tax net interest / avg net debt. This separates operating profitability from financing effects.

### C.2 ROIC tree

ROIC = NOPAT margin (NOPAT / Revenue) × invested-capital turnover (Revenue / avg IC). Break down further: gross margin → opex ratios (`selling_general_and_administrative`, `research_and_development` / revenue) → operating margin; IC turnover → NWC / revenue and PP&E / revenue (fixed-asset turnover). Report ROIC with and without goodwill and intangibles. Compare ROIC with WACC (economic spread) and show the spread's trend.

### C.3 Margin structure

A common-size income statement (each line as % of revenue) over time, with a margin bridge (Δ operating margin attributed to the gross margin, SG&A, R&D and other lines). Where there are ≥ 8 years of data, estimate operating leverage: regress %Δ operating income on %Δ revenue (degree of operating leverage). Report the coefficient and R².

### C.4 Working capital and cash conversion

- DSO = avg `receivables` / revenue × 365; DIO = avg `inventory` / `cost_of_revenue` × 365; DPO = avg `payables` / `cost_of_revenue` × 365; CCC = DSO + DIO − DPO.
- Cash conversion: CFO / NI; FCF / NI; FCF / EBITDA.
- Capex intensity: capex / revenue, capex / D&A (reinvestment beyond maintenance).

### C.5 Growth decomposition

- **Historical growth:** revenue, EBIT, NI and EPS CAGRs over 3, 5 and 10 years (stated windows; split-consistent share terms for EPS).
- **EPS growth attribution:** Δ ln EPS = Δ ln revenue + Δ ln net margin − Δ ln shares. This separates the business from margins and buybacks.
- **Sustainable growth:** g = b × ROE (b = retention). Compare with realized growth; a gap means external financing or a change in returns.
- **Fundamental growth (operating):** g = reinvestment rate × ROIC, where reinvestment rate = (net capex + ΔNWC) / NOPAT. This feeds A.3 directly.
- **Organic vs acquired:** if `net_cash_business_acquisitions` is material, use the filing [S] to separate acquired revenue. Without it, disclose that growth includes acquisitions.
- **Macro sensitivity (optional):** regress revenue growth on nominal GDP growth [D] for cyclicality; report beta-to-GDP and R².

### C.6 Earnings quality

- **Accruals:** balance-sheet and cash-flow accrual ratios. fafnir `accruals` = (NI − CFO)/avg assets. Persistently high accruals are a flag (Sloan 1996).
- **Piotroski F-score** (`piotroski_f` [F]), with its nine signals listed.
- **Beneish M-score:** compute only if every input is available [F/S], and list which were proxied. Otherwise omit and say so.
- **Altman Z** (`altman_z` [F]; the original 1968 model for manufacturers. For non-manufacturers, use Z'' with cited coefficients, or omit).
- **Signals to check and report:** revenue growth vs receivables growth, inventory build vs COGS, capitalized vs expensed costs (from the filing), SBC / revenue, restatement history (Phase 2), auditor changes and qualified opinions [S], non-GAAP vs GAAP gap [S].

### C.7 Output

A driver dashboard (T-5), DuPont and ROIC tables with attribution, the growth decomposition, an earnings-quality scorecard, and a written synthesis covering:

1. what drives returns;
2. what drove the change;
3. how durable it is, judged on evidence such as stability through downturns, peer-relative persistence and reinvestment opportunities;
4. which assumptions this implies for Module A.
