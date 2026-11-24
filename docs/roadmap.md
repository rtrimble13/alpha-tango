# Roadmap

Planned domains and skills, and proposed enhancements to the repository and to `equity-valuation`. Everything here is a proposal unless it is marked as applied. Each item becomes an issue, then a pull request, when work starts.

## Contents

- [Domains](#domains)
- [Repository enhancements](#repository-enhancements)
- [Proposed changes to equity-valuation](#proposed-changes-to-equity-valuation)

## Domains

The taxonomy is meant to grow one domain at a time. A domain is created by the first skill in it (`make new DOMAIN=… NAME=…`).

| Domain (plugin) | Status | Candidate skills |
|---|---|---|
| `equity-research` | Active | `equity-valuation` (released). Candidates: `earnings-review` (a quarter's results against history, guidance and the prior model); `equity-screening` (factor screens and cross-sections on the fafnir panel); `sum-of-the-parts` for conglomerates |
| `fixed-income` | Planned | `treasury-curve` (curve construction and forward analysis with fit and dismal); `corporate-bond-relative-value` (z-spread against rating and sector curves); `credit-analysis` (issuer credit profile, covenants, recovery) |
| `macro-research` | Planned | `economic-dashboard` (current conditions from FRED/BLS/BEA with vintages); `recession-indicators` |
| `market-analysis` | Planned | `technical-analysis`: trend, momentum, volatility and volume indicators, support and resistance, and relative strength against a benchmark or sector ETF. Runs on fafnir daily prices; signals are stated as conditions, not forecasts. See the [proposal](#proposal-technical-analysis). |
| `portfolio-management` | Planned | `portfolio-analytics` (exposures, risk contribution); `performance-attribution` (Brinson and factor attribution); `rebalancing` |
| `risk-management` | Candidate | `market-risk` (VaR, expected shortfall, stress tests); `liquidity-risk` |
| `wealth-planning` | Candidate | `retirement-projection`; `tax-aware-withdrawals` |

When a new domain arrives, check that its skills' descriptions and the existing ones don't overlap. For example, `equity-valuation` 2.1.0 stopped listing curve work ahead of a `fixed-income` skill (item E5 below).

### Proposal: technical-analysis

**Domain.** Keep it out of `equity-research`, because technical analysis applies to anything with a price history, not just single companies. Separate plugins also stop chart requests from picking up fundamental skills, and the reverse. If it will only ever cover equities and ETFs, putting it in `equity-research` is an acceptable, simpler choice.

**Data and tools.** Checked against fafnir at `ebe7386`.

- fafnir `price_history`: adjusted prices for indicators; raw prices for price levels such as support, resistance and gaps.
- `duk ti` computes four indicators: SMA, EMA, RSI and MACD. `duk rc` computes simple, log, cumulative, dividend-adjusted, excess and annualized returns. Any other indicator, such as ATR, Bollinger bands, stochastics, ADX or on-balance volume, needs tested code in the skill's `scripts/` or a new `duk ti` subcommand.
- Volume is stored. `core.daily_price.volume` is raw (shares, in that day's share terms). `mart.v_daily_price_adjusted` back-adjusts it to post-split terms, which volume indicators need across a split. NAV-priced funds carry volume 0, so volume indicators are n.m. for them.
- Charts are built in Python and saved with the report.

**Gaps.** The data is daily only, so there is no intraday analysis. There is no options, positioning or sentiment data.

**Conventions.** The house standard in [authoring-skills.md](authoring-skills.md#financial-skill-conventions) applies:

- state each indicator's definition and parameters;
- keep point-in-time discipline, and compute in code;
- use neutral language, and end with the disclaimer;
- for any backtest, disclose look-ahead and survivorship bias, and that delisting returns aren't in the warehouse.

**Overlap with `equity-screening`.** Momentum as a cross-sectional ranking factor belongs to screening. Chart-based signals on one instrument belong to technical analysis. Each skill's description should exclude the other's requests.

## Repository enhancements

| ID | Enhancement | Why | Notes |
|---|---|---|---|
| R1 | **Evaluation suites** per domain under `evals/`, run with `claude plugin eval` | Today CI checks structure only. Evals check whether a skill triggers on the right requests, and whether its outputs meet the standard. Comparing a run with and without the plugin shows what the skill adds. | Start with trigger and no-trigger cases. Then add golden cases with a fixed as-of date and graders for the QA checklist. Runs cost tokens, so run on demand or nightly, not on every PR. |
| R2 | **Reviewer subagent** shipped in the `equity-research` plugin | equity-valuation already calls for "a separate reviewer agent" for high-stakes work. Shipping one makes that review repeatable. | A Claude Code agent definition listed in the plugin entry. It reruns Section 8 and recomputes the summary from the saved script and data. |
| R3 | **Shared, tested calculation library** | Prime directive 5 sends all arithmetic to code, but every engagement writes that code from scratch. A tested library removes a large source of variance and error, and saves tokens. | Per-skill `scripts/` first, for example WACC, DCF with stub and mid-year handling, LMDI DuPont attribution, TTM contiguity, harmonic means, beta regression, treasury-stock iteration. Promote to a shared package once two skills need the same code. |
| R4 | **JSON Schemas for machine-readable outputs** | Turns `equity-valuation-report/1.1` into something a tool can check, in the QA phase and in downstream systems. | `assets/report.schema.json`, plus a validation script that the skill runs before reporting |
| R5 | **Release provenance** | Lets users verify that a release zip was built by this repository's workflow | Add `actions/attest-build-provenance` to the release job |
| R6 | **Documentation site** | Search and navigation once there are several domains | MkDocs or GitHub Pages built from `docs/` and each skill's README |
| R7 | **Per-domain code owners** | Methodology review by someone who knows the domain | Extend `.github/CODEOWNERS` as domains gain maintainers |
| R8 | **House configuration** | Several skills will need firm-level settings: rating vocabulary, house ERP, approved vendors, output folder | A documented config file (for example `.alpha-tango/config.yaml` in the user's project) that skills read during intake. See E8. |

## Proposed changes to equity-valuation

A review of the 1.0.0 text found the items below. Each changes methodology or behavior and needed the author's decision, and each lists the version bump it needs. The 1.0.0 release itself only fixed a broken cross-reference and Markdown rendering. See the [changelog](../skills/equity-research/equity-valuation/CHANGELOG.md) for what each release changed.

| Status | Items |
|---|---|
| **Applied in 2.0.0** | E1 to E4 (methodology) |
| **Applied in 2.1.0** | E5 (description scope), E7 (skill version in reports) |
| Open | E6, E8 to E14 |

### Methodology (applied in 2.0.0)

| ID | Where | Observation | Proposal | Bump |
|---|---|---|---|---|
| E1 | D.2 | `FFO = CFO − ΔNWC`, but Phase 4 defines ΔNWC as NWC_t − NWC_t−1. An increase in working capital lowers CFO, so FFO (cash flow before working-capital changes) is CFO **+** ΔNWC under that definition. | Use CFO + ΔNWC. Better still, use CFO less the cash-flow statement's working-capital lines from the filing: the balance-sheet ΔNWC includes acquisition and FX effects that CFO does not. | MAJOR (moves FFO/debt) |
| E2 | A.4 | Under the mid-year convention, the explicit flows are discounted at t − 0.5, but the perpetuity-growth terminal value is discounted at N. A Gordon TV built from FCFF_{N+1} assumes year-end flows, so this understates TV by a factor of about (1 + WACC)^0.5, roughly 4% at an 8% WACC, on the largest part of the value. | State the TV timing explicitly. Discount the perpetuity-growth TV at N − 0.5 under the mid-year convention, and an exit-multiple TV at N. | MAJOR (moves values) |
| E3 | A.5 vs A.3 | A.3 makes mid-year discounting the default, but the FCFE formula in A.5 uses end-of-year exponents. | Align A.5 with A.3, or state why FCFE differs | MAJOR |
| E4 | C.1, Section 8, Section 11 | Log attribution `ln ROE = Σ ln factor_i` fails when any factor is zero or negative: a loss year, a tax benefit, EBT < 0 with EBIT > 0. Its terms also sum to ln(ROE₁/ROE₀), not to ΔROE, which the QA checklist requires. | Scale the log contributions by the logarithmic mean L = ΔROE / ln(ROE₁/ROE₀) (LMDI), so that they sum to ΔROE in points. When a factor is ≤ 0, fall back to Shapley (average sequential substitution) and disclose it. | MINOR |

### Behavior and triggering (E5 and E7 applied in 2.1.0)

| ID | Where | Observation | Proposal | Bump |
|---|---|---|---|---|
| E5 | Frontmatter `description` | "Fixed-income work (Treasury curve construction …) runs in fit" can make the skill load for standalone bond or curve requests. Those will belong to a future `fixed-income` skill. | Reword it as inputs to the equity work: "uses fit to build the Treasury curve and value the company's own debt." Optionally add "Not for standalone bond or curve analysis." | MINOR |
| E6 | Phase 0 | "If any of the first three are missing or ambiguous, ask", but the third row (as-of date) has a default of "Today". | Ask only for company and task. Default the as-of date to today, and ask only when the request implies a historical date ambiguously. | PATCH |
| E7 | Section 9.8, Appendix F | The report records tool versions but not the skill version, so reports made under different skill versions can't be told apart. | Add `"generator": {"skill": "equity-valuation", "version": "<metadata.version>"}` to the JSON (schema 1.1) and list it in Appendix F | MINOR |
| E8 | Prime directive 9, Phase 0 | "The vocabulary the user has configured" has no defined configuration mechanism. The same is true of a house ERP and approved Tier 4 vendors. | Define where house settings come from (R8). Until then, say "the vocabulary the user specifies in the request or project instructions". | MINOR |
| E9 | Phase 3, Phase 7 | Outputs go to "the working directory", with no layout, so repeated runs can overwrite each other. | Standard layout `reports/<TICKER>/<as-of>/` with `report.md`, `model.py`, `data/` and `summary.json` | MINOR |
| E10 | Phase 0 | Tool availability is discovered mid-workflow (`dismal doctor` in 2.4, `fit --version` in 2.5), so a long engagement can fail late. On claude.ai none of the tools exist. | Add a preflight step to Phase 0: check fafnir (MCP or `duk`), `dismal doctor`, `fit --version` and web access, then report which routes are available before starting. A small script in `scripts/` could do this. | MINOR |

### Clarity

| ID | Where | Observation | Proposal | Bump |
|---|---|---|---|---|
| E11 | 9.7 | The confidence rubric defines only High and Low columns. | Add a Medium column, or define Medium as "neither High nor Low" | PATCH |
| E12 | B.1 | `feedFrozenOn` is used as a peer screen but not defined, and its source tool is not named | Name the fafnir field and the tool that returns it | PATCH |
| E13 | 2.5 and 9.8 | fit reports rates in percent, while the JSON summary uses decimals | Add a Section 8 checklist item: fit percent outputs are converted to decimals in the JSON summary | PATCH |
| E14 | A.2.3 | Bottom-up beta unlevers with D/E but doesn't adjust for peers' cash holdings | Optionally use Damodaran's cash-adjusted unlevered beta, β_U / (1 − cash/firm value), for cash-rich peers, stated as a choice | MINOR |
