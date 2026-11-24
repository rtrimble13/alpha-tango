# Equity valuation: Section 5 (Module B)

Part of the `equity-valuation` skill ([SKILL.md](../SKILL.md)). Section numbers and cross-references (for example 2.6, A.9, T-13) are those of the full standard; the section map in SKILL.md says which file holds each section.

## Contents

- [B.1 Peer selection protocol](#b1-peer-selection-protocol)
- [B.2 Metrics](#b2-metrics)
- [B.3 Statistics](#b3-statistics)
- [B.4 From multiples to value](#b4-from-multiples-to-value)
- [B.5 Output](#b5-output)

## 5. Module B: Relative valuation

### B.1 Peer selection protocol

1. **Universe:** `screen_securities(industry=[target industry])` (actively trading). If fewer than 8 names, widen to the sector, then narrow by business model.
2. **Screens**, each stated: same reporting currency or convertible; not a secondary share class; positive revenue; market cap within a stated band of the target (default 0.2× to 5×); not ETF/fund; no `feedFrozenOn`; no material open DQ flags.
3. **Business-model check:** read each candidate's 10-K Item 1 (or the `security_profile` description) and keep companies whose primary revenue source, customers and economics resemble the target's. Record the reason for each inclusion and exclusion.
4. **Minimum:** 5 peers. With fewer, relative valuation is reported as low-confidence.
5. **Historical as-of dates:** classification is today's (2.3.1). Verify that each peer existed and was comparable on the date; include peers that have since died (`include_delisted=true`), since excluding them creates survivorship bias.

### B.2 Metrics

Use fafnir's factor definitions (2.3.3) for every peer at the same as-of date (`factor_row(peer, as_of)`). Present multiples as both yields and multiples:

- **Equity:** P/E (1/`earnings_yield`), P/B (1/`book_to_price`), P/S, P/CF, dividend yield, shareholder yield.
- **Enterprise:** EV/EBITDA, EV/EBIT, EV/Sales, EV/FCF. Adjust EV for NCI, preferred and leases (A.9) consistently for **all** companies, or for none, and state which.
- **Growth-adjusted:** PEG = P/E ÷ (expected EPS growth × 100), only with a cited or explicitly assumed growth figure; label which.
- **Forward multiples** only with cited estimates (2.6).

### B.3 Statistics

- Report n, median, harmonic mean, p25 and p75 for each multiple. The harmonic mean of a multiple equals 1 / mean of its yield, so compute it from yields.
- Do not average multiples with negative or n.m. values. Use yields, or report the count excluded.
- Where the ops profile is available, also show the sector and industry quartiles from `mart.v_industry_fundamentals` at the same month-end [F].
- **Own history:** the target's multiples at each month-end over ≥ 10 years (or since 1998, or since listing) from the panel. Report the current value's percentile and z-score versus that history.

### B.4 From multiples to value

- Implied value = peer median multiple × the target's metric, for each multiple. Use EV multiples → bridge (A.9) → per share.
- **Justified multiples (fundamentals-based):**
  - P/E (leading) = payout ratio / (r_e − g); P/E (trailing) = payout (1+g)/(r_e − g);
  - P/B = (ROE − g)/(r_e − g);
  - EV/Sales = after-tax operating margin × (1 − g/ROIC) × (1+g)/(WACC − g) (stable-growth form).

  Compare justified with actual to explain premiums and discounts.
- **Cross-sectional regression (when n ≥ 10):** for example, P/B on ROE or EV/Sales on operating margin across peers. Report the coefficients, R² and the target's residual. Use it to explain the premium or discount, not as a price target on its own.
- **Explain differences** with Module C (growth, ROIC, margins) and Module D (leverage, risk). A cheap multiple with lower ROIC is not necessarily mispriced.

### B.5 Output

A peer table (9.4, T-4) with every peer's metrics and source IDs, the statistics, the target's percentile rank per multiple, the implied value range, and a written view of relative value supported by fundamentals.
