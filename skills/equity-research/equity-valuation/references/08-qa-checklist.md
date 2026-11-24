# Equity valuation: Section 8

Part of the `equity-valuation` skill ([SKILL.md](../SKILL.md)). Section numbers and cross-references (for example 2.6, A.9, T-13) are those of the full standard; the section map in SKILL.md says which file holds each section.

## 8. Quality-assurance checklist (complete before reporting)

**Data**

- [ ] Every input value has a Source Ledger ID; every Tier 2–4 value has a URL or accession number, location and retrieval date.
- [ ] As-of discipline: no statement with `known_from` > as-of; no price after the price date; macro values from the correct vintage; external sources published on or before the as-of date.
- [ ] Phase 2 reconciliations pass (≤ 0.5%) or are explained.
- [ ] Share terms are consistent (splits) and the share factor is applied; currency is consistent.
- [ ] SF1 sign conventions are handled (capex, dividends, buybacks negative).
- [ ] NULLs are reported as n.m., not zeros.

**Model integrity**

- [ ] The balance sheet balances in forecasts: assets = liabilities + parent equity + NCI.
- [ ] FCFF from the CFO route and the NOPAT route reconcile, or the difference is explained.
- [ ] g < WACC (and < r_e); terminal g ≤ r_f and ≤ the cited nominal GDP anchor.
- [ ] Reinvestment × ROIC ≈ growth in the terminal period; terminal ROIC is justified.
- [ ] WACC weights are at market value; debt definition is the same in the weights, the bridge and the multiples (leases included or excluded throughout).
- [ ] fit curve: `max_repricing_error_bp` ≤ 0.01; quote conventions (bill basis, par frequency) and the interpolation scheme are recorded; the 10Y par rate agrees with `DGS10` within 1 bp; no example data was used.
- [ ] Every fit-valued instrument is fixed-rate bullet or zero-coupon. Others are at carrying or fair value [S] and disclosed.
- [ ] The EV → equity bridge includes every claim in A.9 or discloses its omission.
- [ ] Diluted shares are documented.
- [ ] DuPont components multiply to ROE; attribution sums to ΔROE in ROE points, by LMDI or (when a factor is ≤ 0) Shapley, as stated (C.1).
- [ ] The implied exit multiple and the reverse-DCF result are reasonable against Module B, or explained.
- [ ] TV share of value is reported.

**Reproducibility**

- [ ] The calculation script runs from the saved data files and reproduces every number in the report.
- [ ] Rounding is applied only at presentation.

**Report**

- [ ] Every required section and table in Section 9 is present, or marked "not applicable" with the reason.
- [ ] Data gaps and limitations are listed.
- [ ] Neutral language and the disclaimer are included.

For high-stakes work (the user says the report will be published or used for a decision), a separate reviewer agent that did not build the model reruns this checklist and recomputes the summary figures from the saved script and data.
