# Equity valuation: Section 4 (Module A)

Part of the `equity-valuation` skill ([SKILL.md](../SKILL.md)). Section numbers and cross-references (for example 2.6, A.9, T-13) are those of the full standard; the section map in SKILL.md says which file holds each section.

## Contents

- [A.1 Model selection](#a1-model-selection)
- [A.2 Cost of capital](#a2-cost-of-capital)
  - [A.2.1 Risk-free rate](#a21-risk-free-rate)
  - [A.2.2 Equity risk premium](#a22-equity-risk-premium)
  - [A.2.3 Beta (estimate it; don't download it)](#a23-beta-estimate-it-dont-download-it)
  - [A.2.4 Cost of equity](#a24-cost-of-equity)
  - [A.2.5 Cost of debt](#a25-cost-of-debt)
  - [A.2.6 Weights and WACC](#a26-weights-and-wacc)
- [A.3 Forecasting](#a3-forecasting)
- [A.4 FCFF DCF (enterprise)](#a4-fcff-dcf-enterprise)
- [A.5 FCFE DCF (equity)](#a5-fcfe-dcf-equity)
- [A.6 Dividend discount models](#a6-dividend-discount-models)
- [A.7 Residual income](#a7-residual-income)
- [A.8 Terminal value constraints](#a8-terminal-value-constraints)
- [A.9 Enterprise value to equity value per share](#a9-enterprise-value-to-equity-value-per-share)
- [A.10 Sensitivity, scenarios and the market-implied view](#a10-sensitivity-scenarios-and-the-market-implied-view)
- [A.11 Special situations](#a11-special-situations)

## 4. Module A: Intrinsic valuation

### A.1 Model selection

Choose a **primary** model and at least one **cross-check** model, and justify both.

| Company profile | Primary | Cross-check | Avoid |
|---|---|---|---|
| Mature, stable, dividend payout tracks FCFE | DDM (Gordon or 2-stage) | FCFE, residual income | — |
| Operating company, leverage stable or targeted | FCFF DCF (WACC) | Residual income, exit multiple | — |
| Leverage changing materially (LBO, recap) | APV or FCFE with explicit debt schedule | FCFF with year-varying WACC | Constant-WACC FCFF |
| Banks, insurers, other financials (NULL current assets, deposit liabilities) | Residual income (P/B–ROE) or DDM/FCFE | Justified P/B | FCFF/WACC (debt is operating) |
| Negative or volatile FCF but positive book value | Residual income | Normalized FCFF | Gordon DDM |
| High growth, currently loss-making | Multi-stage FCFF with explicit margin path to a cited steady-state peer level | Reverse DCF; EV/Sales vs peers | Single-stage models |
| Cyclical | FCFF on normalized mid-cycle margins | EV/EBITDA on mid-cycle EBITDA | Peak/trough earnings capitalized |
| Asset-heavy holding, REIT, resources | NAV / sum-of-the-parts (cited asset values) | P/FFO or P/NAV vs peers (FFO from filings) | Earnings multiples alone |

### A.2 Cost of capital

#### A.2.1 Risk-free rate
- Default: `DGS10` on the as-of date [D], in the currency of the cash flows. For non-USD flows, use that sovereign's local-currency yield from a Tier 1/3 source, adjusted for default spread if the sovereign is not AAA (cite Damodaran's country default spreads).
- Use the same rate in CAPM, the cost of debt and the terminal-growth ceiling.
- **Curve checks with fit (2.5).** Build the Treasury curve on the as-of date and report the 10-year par and zero rates beside `DGS10`. They should agree to within about 1 bp on par. Also report:
  - the 10y-forward-in-10y rate, as context for whether a flat r_f in the terminal period is consistent with the curve;
  - for a non-standard horizon (for example, a 7-year explicit period, or a duration-matched rate at the equity's cash-flow duration), the par rate at that tenor, read off the curve instead of interpolated by hand.

  The CAPM r_f stays `DGS10` unless the report states and justifies another tenor, because the ERP source (A.2.2) is quoted over a specific tenor.

#### A.2.2 Equity risk premium
- No default number. Choose one source per 2.6 and record the value, edition/month and method (implied vs historical; arithmetic vs geometric; window). The ERP must match the risk-free rate's basis (an ERP over T-bonds with the 10-year).
- Country risk premium only for material non-domestic operations, from Damodaran's CRP table [X], weighted by a cited revenue/operations split [S].
- **Size, company-specific or "alpha" premia are not added by default.** If the user asks for one, it needs a cited source and is shown as a separate line with sensitivity.

#### A.2.3 Beta (estimate it; don't download it)
1. **Regression beta [C]:** OLS of the stock's adjusted returns on SPY adjusted returns [F]. Default: 5 years of monthly returns (60 observations). Alternative: 2 years of weekly returns. Use the same dates for both series. Report β, standard error, R², observation count and window.
2. **Adjusted beta [C]:** Blume, β_adj = 0.67 β_raw + 0.33. Disclose it.
3. **Bottom-up beta [C] (preferred when the regression SE > 0.25, R² < 0.2, the company has fewer than 2 years of history, or its business mix has changed):**
   - regression beta for each peer (Module B peer set), same method;
   - unlever each one: β_U = β_L / [1 + (1 − t)(D/E)], with market D/E from fafnir (`total_debt` / `market_cap`);
   - take the median β_U;
   - relever it at the target's D/E (current market D/E, or a target structure from D.6, stated).
4. The `security_profile`/screen beta (1-year daily vs SPY) is a sanity check only.
5. State the chosen beta and why. Show cost of equity at ±0.2 beta in the sensitivity.

#### A.2.4 Cost of equity
- CAPM: r_e = r_f + β × ERP (+ CRP × exposure, if applied).
- Cross-checks, where data exists: implied cost of equity from the Gordon model at the current price (r = D1/P0 + g), and a bond-yield-plus-premium approach (company's cost of debt + a cited premium). Report any divergence greater than 150 bp and explain it.

#### A.2.5 Cost of debt
In order of preference:
1. **Market yield** on the company's long-dated bonds, when a cited price exists [S/X] (for example, FINRA TRACE last sale, with date and size). Compute the YTM and z-spread with `fit bond yield … --price P --curve treasury.csv` [C], using the bond's terms from its indenture or the 10-K debt note [S]. When there are several bonds, use a face-weighted or longest-maturity spread, and state which. r_d = the curve's par rate at the WACC tenor + that spread.
2. **Agency rating** [S] → current spread for that rating (FRED ICE BofA OAS by rating, or Damodaran's table) + r_f.
3. **Synthetic rating** [C]: interest coverage (EBIT / interest expense, TTM [F]) → rating → spread, using the current Damodaran table (large-firm or small/risky-firm version, stated) [X].
4. Historical cost (interest expense / average total debt [C]) is a check only, not a cost of capital.

After-tax cost of debt = r_d × (1 − marginal t). Leases are included in debt only if included in the debt weight, and vice versa (consistency rule).

#### A.2.6 Weights and WACC
- **Market-value weights.** Equity = market cap on the price date [F]. Debt at fair value, in order of preference:
  1. a fit valuation on the as-of date [C]: `fit portfolio value` of the fixed-rate notes listed in the 10-K debt note [S], each marked at a cited price or at the A.2.5 spread, plus out-of-scope instruments at carrying value [S], disclosed;
  2. the 10-K fair-value disclosure [S], which is as of the fiscal year end and must be dated in the report;
  3. book `total_debt` [F], disclosed.

  The debt figure must be the same in the weights and in the A.9 bridge. Add preferred and leases per A.9 consistency.
- Use the current structure unless there is evidence (cited management targets, a stated policy, or a D.6 analysis) for a target structure. State which.
- WACC = w_e r_e + w_d r_d (1 − t) + w_p r_p.
- Sanity checks: WACC > terminal g + 100 bp; r_e > r_d (pre-tax); WACC within the peer-implied range (flag when it falls outside the interquartile range of peers' WACCs computed the same way).

### A.3 Forecasting

- **Drivers, not line items.** Forecast revenue growth, operating margin, tax rate, reinvestment (net capex + ΔNWC as % of revenue, or the sales-to-capital ratio) and capital structure. Derive the statements from the drivers.
- **Anchors.** Each driver path is anchored to evidence: the company's own history (Module C), peer distributions (Module B, `v_industry_fundamentals` quartiles where available), cited management guidance [S] and macro anchors [D]. Record each driver in the Assumption Register with its anchor.
- **Fade rules.** High growth and excess returns fade toward steady state over the explicit horizon. The fade path is stated: linear by default, with a rationale.
- **Consistency checks (must pass):**
  - Implied reinvestment rate × ROIC ≈ growth, both in the explicit period and in terminal: g = RR × ROIC_new.
  - Terminal ROIC_new is justified: equal to WACC (no competitive advantage) by default; higher only with a cited moat rationale from Module C evidence (sustained ROIC > WACC over ≥ 10 years, through a downturn).
  - Margins in the terminal year are within the peer range, or justified.
  - Share count path reflects cited buyback/issuance evidence; flat by default.
- **Base year:** TTM by default (as of the knowledge date), or the last fiscal year when TTM is unavailable. Use mid-year discounting by default. Handle the stub period from the as-of date to the first fiscal year end explicitly.

### A.4 FCFF DCF (enterprise)
Value_firm = Σ_{t=1..N} FCFF_t / (1+WACC)^(t−0.5) + TV_N / (1+WACC)^N (mid-year convention; state it). TV_N = FCFF_{N+1} / (WACC − g), with FCFF_{N+1} = NOPAT_{N+1} × (1 − g / ROIC_new). Then the bridge to equity (A.9).

### A.5 FCFE DCF (equity)
Value_equity = Σ FCFE_t / (1+r_e)^t + TV_N / (1+r_e)^N. Requires an explicit debt path. Net borrowing is consistent with the stated leverage target.

### A.6 Dividend discount models
- **Gordon:** V0 = D1 / (r_e − g), with D1 = D0 (1+g). D0 = TTM DPS from `corporate_actions` [F]. Requires g < r_e and a sustainable g, checked against b × ROE.
- **Two-stage:** explicit high-growth dividends, then Gordon.
- **H-model:** V0 = [D0 (1+g_L) + D0 H (g_S − g_L)] / (r − g_L), with H = half-life of the linear fade, in years.
- **Three-stage:** growth, transition and maturity stages, each with the payout ratio consistent with growth (payout = 1 − g/ROE).

### A.7 Residual income
V0 = B0 + Σ (E_t − r_e B_{t−1}) / (1+r_e)^t + TV, where B is book equity (`total_equity_parent` [F]) and E is NI to common. Requires clean-surplus checks: B_t = B_{t−1} + E_t − D_t ± net issuance. Flag dirty-surplus items (AOCI moves) from `accumulated_other_comprehensive_income`. Terminal options are stated: residual income persists, fades (persistence factor ω, cited or justified), or ends at N. The justified P/B for the cross-check is (ROE − g)/(r_e − g).

### A.8 Terminal value constraints
- **Nominal g ≤ the risk-free rate**, and ≤ the long-run nominal GDP growth anchor [D] (for example, CBO potential real growth from `GDPPOT` plus expected inflation from `T10YIE`). Both anchors are shown.
- Report TV as % of total value. More than 75% is flagged and requires a reverse-DCF discussion.
- **Exit-multiple cross-check:** terminal value ÷ terminal-year EBITDA (and the implied P/E) against peer and own-history ranges from Module B. A gap of more than ±30% from the peer median must be explained.

### A.9 Enterprise value to equity value per share
Equity value = Enterprise value
 + cash and equivalents [F] (+ non-operating investments, if justified, cited)
 − total debt: fair value per A.2.6 (fit [C], or 10-K [S]), else book [F]; the same figure as in the WACC weights
 − lease liabilities (if not in debt and leases are treated as debt; consistency with WACC weights is mandatory)
 − preferred stock [S]
 − noncontrolling interest [S] (or derived [C], flagged)
 − unfunded pension/OPEB, net of tax [S]
 − other debt-like items (litigation reserves, contingent consideration) [S]
 + equity-method investments and other non-consolidated assets at a cited value [S]

Per share = equity value ÷ diluted shares. Diluted shares = basic shares outstanding on the as-of date (`shares_outstanding_as_of` [F] or the latest 10-Q cover [S]) + in-the-money options and RSUs (treasury-stock method, at the estimated value: iterate) + convertibles if in the money (if-converted). Each item is listed with its source.

### A.10 Sensitivity, scenarios and the market-implied view
- **Sensitivity grids (required):** WACC (±100 bp in 50 bp steps) × terminal g (±100 bp in 50 bp steps). Also terminal operating margin × revenue CAGR.
- **Scenarios:** bear, base and bull, each a coherent set of drivers with a narrative. Probability weights only if the user requests them or evidence supports them; otherwise present the scenarios unweighted.
- **Reverse DCF:** solve for the revenue CAGR (or terminal margin) that the current price implies, holding the other assumptions at base. Compare with history and peers.
- **Fair value conclusion:** a point estimate (the primary model's base case) and a range (bounded by the sensitivity and scenario results, stated). If the cross-check models differ from the primary by more than 15%, explain why. Weight methods only with a stated rationale.

### A.11 Special situations
- **Negative earnings or EBIT:** do not capitalize losses. Model the path to a cited steady-state margin, and survival risk (Module D distress metrics). Value per share must account for dilution from likely financing.
- **Financials:** debt is raw material, so use equity-side models only. Regulatory capital ratios come from filings [S].
- **Multi-class issuers:** value the issuer once; per-share values for each class follow the cited conversion terms.
- **ADRs:** value in the reporting currency, convert at the cited spot FX rate, and apply the ADR ratio (fafnir `share_factor`).
- **M&A pending:** if a definitive agreement exists [S], report deal terms and the spread; standalone intrinsic value is secondary.
