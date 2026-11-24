# Equity valuation: Section 7 (Module D)

Part of the `equity-valuation` skill ([SKILL.md](../SKILL.md)). Section numbers and cross-references (for example 2.6, A.9, T-13) are those of the full standard; the section map in SKILL.md says which file holds each section.

## Contents

- [D.1 Structure and leverage](#d1-structure-and-leverage)
- [D.2 Coverage and debt capacity](#d2-coverage-and-debt-capacity)
- [D.3 Liquidity and maturity](#d3-liquidity-and-maturity)
- [D.4 Credit view](#d4-credit-view)
- [D.5 Payout and dilution](#d5-payout-and-dilution)
- [D.6 Cost of capital and optimal structure](#d6-cost-of-capital-and-optimal-structure)
- [D.7 Output](#d7-output)

## 7. Module D: Capital structure

### D.1 Structure and leverage

- **Composition:** current and non-current debt (`debt_current`, `debt_noncurrent`), leases [S], preferred [S], NCI, equity at book and market value.
- **Leverage:** D/E (book and market), D/Capital, net debt / EBITDA, debt / assets, FLEV (C.1), financial leverage ratio (assets / equity). Show a 10-year history and the peer median.

### D.2 Coverage and debt capacity

EBIT / interest, EBITDA / interest, (EBITDA − capex) / interest, FFO / debt, and debt / EBITDA headroom against covenants where covenants are disclosed [S].

FFO is cash flow from operations before working-capital changes. With ΔNWC as defined in Phase 4 (NWC_t − NWC_t−1: an increase in working capital is positive and has reduced CFO), FFO = CFO + ΔNWC. Prefer the working-capital lines of the filing's cash-flow statement [S]: FFO = CFO − (those lines as reported, where a build-up is negative). The balance-sheet ΔNWC also moves with acquisitions, disposals and FX, and CFO does not. State which was used.

### D.3 Liquidity and maturity

Current, quick and cash ratios; cash and undrawn revolver [S] vs debt due within 12 months (`debt_current`).

The maturity ladder: from the 10-K debt note [S], built as a fit portfolio (2.5). `fit portfolio cashflows` gives principal and coupon by year.

Interest-rate exposure: the fixed vs floating mix [S]. Two separate effects:

- floating debt's **interest cost** under a ±100 bp shock [C];
- the fixed-rate debt's **fair-value** sensitivity, from `fit portfolio scenario --shifts=-100,0,100` and the key-rate DV01 ladder from `fit portfolio risk` [C].

Also report the debt's weighted duration (`fit portfolio value` totals) and the refinancing need over the next 3 years at today's curve plus the A.2.5 spread.

### D.4 Credit view

- Agency ratings and outlook [S] if any.
- Synthetic rating from coverage (A.2.5) and its implied spread; a comparison with the market spread (FRED OAS for that bucket [D]).
- Distress metrics: Altman Z, interest coverage below 1.5×, negative equity, going-concern language [S].

### D.5 Payout and dilution

Dividends, buybacks (−`net_equity_issuance`), total shareholder yield, payout vs FCF (are distributions funded by debt?), net share issuance (`net_share_issuance_1y`), and SBC dilution.

### D.6 Cost of capital and optimal structure

- **Unlever/relever (Hamada):** β_L = β_U [1 + (1 − t) D/E]. State the assumption that debt beta is 0, or use a cited debt beta for high leverage.
- **WACC curve:** at D/(D+E) from 0% to 70% in 10-point steps:
  - relever β and recompute r_e;
  - re-estimate interest coverage at each level (interest = r_d × D, with EBIT held at normalized TTM);
  - map coverage to a synthetic rating and spread (cited table), with r_d = the fit curve's par rate at the assumed new-issue tenor (state it; default 10Y) + spread;
  - compute r_d and WACC.

  Find the minimum-WACC range and the value effect versus the current structure, which is the change in firm value from the change in WACC holding FCFF constant (state this simplification).
- **Qualitative factors:** business risk (C.3 operating leverage), asset tangibility, growth options, tax shield usability (positive taxable income), and the pecking-order and agency considerations that the company's disclosures support.
- **MM framing:** state where the analysis relies on Modigliani-Miller propositions with taxes, and which frictions (distress costs) are modelled through the rating-spread mechanism.

### D.7 Output

A capital-structure table (T-6), coverage and liquidity history, the credit view, the WACC-curve table and chart, and conclusions: is the structure appropriate, what are the risks, and what does it imply for the WACC used in Module A.
