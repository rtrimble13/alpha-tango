# Changelog: equity-valuation

All notable changes to this skill are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow Semantic Versioning, with the meaning of MAJOR, MINOR and PATCH for a skill defined in [docs/versioning-and-releases.md](../../../docs/versioning-and-releases.md).

## [Unreleased]

## [2.1.0] - 2026-11-24

Roadmap items E5 and E7. Valuation outputs are unchanged.

### Added

- **Skill version in every report (E7).** The JSON summary (9.8) gains `"generator": {"skill": "equity-valuation", "version": ...}`, filled from `metadata.version` in SKILL.md, so reports made under different skill versions can be told apart. The schema moves from `equity-valuation-report/1.0` to `1.1`; the change is additive and every 1.0 field is unchanged. Appendix F (9.3) lists the skill name and version, and the Section 8 checklist checks both.

### Changed

- **Description scope (E5).** The description now presents fit as an input to the equity work (the Treasury curve, and the yield, z-spread, fair value and rate risk of the company's own debt). It says the skill is not for standalone bond, yield-curve or credit analysis, so that it no longer claims requests meant for a future `fixed-income` skill.

## [2.0.0] - 2026-11-24

Four methodology corrections (roadmap items E1 to E4). The first three change valuation and credit outputs, so the version is MAJOR. Reports made with 1.0.0 are not directly comparable on the affected figures. The report structure and the `equity-valuation-report/1.0` JSON schema are unchanged.

### Fixed

- **FFO sign (D.2).** FFO was defined as CFO − ΔNWC. With ΔNWC = NWC_t − NWC_t−1 (Phase 4), the correct figure is CFO + ΔNWC, so 1.0.0 misstated FFO by 2 × ΔNWC whenever working capital moved. D.2 now defines FFO as cash flow before working-capital changes. It prefers the filing's cash-flow-statement working-capital lines, because the balance-sheet ΔNWC also moves with acquisitions, disposals and FX. *Moves FFO / debt.*
- **Terminal-value timing under the mid-year convention (A.4).** The perpetuity-growth terminal value was discounted at N. Under the mid-year convention, the flows it capitalizes arrive from N + 0.5 onward, so it is now discounted at N − 0.5. That matches the present value of the mid-year perpetuity exactly. 1.0.0 understated the PV of the terminal value by a factor of (1 + WACC)^0.5, about 3.8% at an 8% WACC. An exit-multiple terminal value is still discounted at N. *Raises FCFF DCF values.*
- **FCFE discounting (A.5).** The FCFE formula used end-of-year exponents, although A.3 makes mid-year discounting the default. A.5 now uses t − 0.5 and N − 0.5, with the same terminal-value rule as A.4, and defines TV_N = FCFE_{N+1} / (r_e − g). *Raises FCFE DCF values.*
- **DuPont change attribution (C.1, Section 8, Section 11).** The log decomposition summed to ln(ROE₁/ROE₀) rather than to ΔROE, and could not run when a factor was zero or negative. Contributions now use logarithmic-mean (LMDI) weights, so they sum exactly to ΔROE in ROE points. When any factor is ≤ 0 (a loss, a tax benefit, EBT < 0 with EBIT > 0, negative equity), the Shapley decomposition is used instead. The method used is stated. *Changes the attribution table, not ROE itself.*

### Changed

- The A.8 exit-multiple cross-check now compares TV_N × (1 + WACC)^0.5 with year-end multiples under the mid-year convention, so that both sit at the same date.
- The formula appendix (Section 11) adds the terminal-value discounting rule and FFO, and replaces the log-attribution row with LMDI.
- The QA checklist (Section 8) now requires the attribution to sum to ΔROE in ROE points, with the method stated.

## [1.0.0] - 2026-11-24

### Added

- First release of the equity-valuation standard. It has four tasks:
  - fair value (Module A);
  - relative value (Module B);
  - decomposition of profitability and growth (Module C);
  - capital structure (Module D).
- Prime directives, the evidence hierarchy and data-gap protocol, an eight-phase engagement workflow, a quality-assurance checklist and the report standard, with tables T-1 to T-14 and the `equity-valuation-report/1.0` JSON summary.
- Data and computation contracts for fafnir (prices, point-in-time fundamentals, factors), dismal (FRED/BLS/BEA) and fit (Treasury curve and company-debt analytics).

### Changed

- The text is now split for progressive disclosure. SKILL.md holds the intro, Sections 1, 3 and 10, and a section map. Sections 2, 4 to 9 and 11 are in `references/`, with their original numbering. Each reference file has a contents list.
- The frontmatter now has `license`, `compatibility` and `metadata` (`version`, `domain`).

### Fixed

- In Section 2.1, the Tier 2 row pointed to 2.4 (dismal) for the items fafnir lacks. It now points to 2.6, which holds that list.
- The A.9 equity bridge is now in a text block. Without one, GitHub rendered its `+` lines as bullets and merged the `−` lines into them. The text is unchanged.
- Blank lines were added around headings, lists and code fences so that the Markdown lints cleanly. Rendering is unchanged.
