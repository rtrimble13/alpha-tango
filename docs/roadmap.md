# Roadmap

Planned domains and skills, the tooling strategy they depend on, and proposed enhancements to the repository and to `equity-valuation`. Everything here is a proposal unless it is marked as applied. Each item becomes an issue, then a pull request, when work starts.

## Contents

- [Domains](#domains)
- [Tooling strategy](#tooling-strategy)
- [Repository enhancements](#repository-enhancements)
- [Proposed changes to equity-valuation](#proposed-changes-to-equity-valuation)

## Domains

The taxonomy is meant to grow one domain at a time. A domain is created by the first skill in it (`make new DOMAIN=… NAME=…`).

| Domain (plugin) | Status | Candidate skills |
|---|---|---|
| `equity-research` | Active | `equity-valuation` (released). Candidates: `equity-screening` (top-down and bottom-up screening of the U.S.-listed universe; see the [proposal](#proposal-equity-screening)); `earnings-review` (a quarter's results against history, guidance and the prior model); `sum-of-the-parts` for conglomerates |
| `fixed-income` | Planned | `treasury-curve` (curve construction and forward analysis with fit and dismal); `corporate-bond-relative-value` (z-spread against rating and sector curves); `credit-analysis` (issuer credit profile, covenants, recovery) |
| `macro-research` | Planned | `economic-dashboard` (current conditions from FRED/BLS/BEA with vintages); `recession-indicators` |
| `market-analysis` | Planned | `technical-analysis`: trend, momentum, volatility and volume indicators, support and resistance, and relative strength against a benchmark or sector ETF. Runs on fafnir daily prices; signals are stated as conditions, not forecasts. See the [proposal](#proposal-technical-analysis). |
| `portfolio-management` | Planned | `portfolio-analytics` (exposures, risk contribution); `performance-attribution` (Brinson and factor attribution); `rebalancing` |
| `risk-management` | Candidate | `market-risk` (VaR, expected shortfall, stress tests); `liquidity-risk` |
| `wealth-planning` | Candidate | `retirement-projection`; `tax-aware-withdrawals` |

When a new domain arrives, check that its skills' descriptions and the existing ones don't overlap. For example, `equity-valuation` 2.1.0 stopped listing curve work ahead of a `fixed-income` skill (item E5 below).

### Proposal: equity-screening

**Recommendation.** Build a separate skill in `equity-research`, in the same plugin, rather than extending `equity-valuation`:

- The unit of work and the output differ: a universe and a ranked shortlist, against one company and a fair-value report.
- `equity-valuation`'s per-company gates, such as reconciling three figures to the 10-K, don't scale to thousands of names. A screen needs universe-level gates instead: data-quality flags, stale statements and coverage counts.
- `equity-valuation`'s description is already 866 of 1,024 characters. Adding screening would blur its triggering, and every valuation would load screening instructions it doesn't use.
- Screening changes would force version bumps on a skill whose versions signal whether valuation reports are comparable.

Names on the shortlist are handed to `equity-valuation` for full or quick-look valuations.

**Modes.**

- **Bottom-up:** screen the universe on fundamentals and, from 0.2, on price-based factors; rank within sectors; report the shortlist.
- **Top-down:** go from macro conditions (dismal) to sector and industry tilts, then to names within the favored groups. Every tilt is either computed from data, for example sector sensitivity to rates or growth estimated from sector ETF prices and dismal series, or registered as an assumption. A tilt is never asserted from memory. A full economic-regime analysis belongs to a future `macro-research` skill that screening can draw on.

**What fafnir provides today.** Checked at `632e8a6`.

- `mart.fundamental_panel`: monthly from 1998, about 45 factors per security, survivorship-free.
- `mart.fn_fundamental_snapshot(D, lag)` for any date, and `mart.security_fundamentals_latest` for current screens.
- `mart.v_industry_fundamentals`: quartiles of 16 factors by sector and industry at each month-end.
- dismal macro series with vintages, sector ETF prices, and `market_cap_history` for up to 1,000 securities a call.

**What it needs.**

| Need | Where | Why |
|---|---|---|
| A cross-sectional screen: `duk sc`, and an MCP `factor_screen` tool | One served read in `duk.datasource.db`, the duk CLI, and the fafnir MCP server | The read profile has only per-security factor rows. `screen_securities` filters metadata and market cap, with no as-of date. `sql_read` is ops-only and capped at 500 rows. A served read reaches the CLI, the HTTP API and MCP with one implementation. It filters on an allowlist of columns (no free SQL), sorts, limits, aggregates by group, and counts what each filter removes. The MCP tool returns capped shortlists (a default of about 50 rows, and at most 5,000 with the `truncated` flag); `duk sc -o` exports the full cross-section. `screen_securities` stays unchanged, because `equity-valuation` B.1 uses it. |
| The universe on a date | fafnir `mart` | Listing status, market cap and panel factors as known on the date. `is_actively_trading` is today's flag, so it gives look-ahead in a historical screen. |
| A price-factor table | fafnir `mart` | Monthly 12-month-minus-1 momentum, volatility, beta against SPY, and average daily dollar volume. The panel is fundamentals-only. |
| Sector aggregates | fafnir `mart` | Cap-weighted sector valuations and returns for top-down. Quartiles describe the typical member, not the sector. |
| A calculation library | The skill's `scripts/` | Outlier trimming, z-scores within sector, composite scores, neutralization, deciles, and turnover against the previous screen. fafnir leaves outlier handling to the user on purpose. |

**Each screen reports:**

- the resolved as-of date, and whether it is a panel month-end or an exact-date snapshot;
- the snapshot's refresh time and the universe definition;
- the count each filter removed, with NULLs counted as n.m. and currency-mismatch exclusions shown;
- for each row: `security_id`, fiscal date, knowledge source, days since filing, the currency-mismatch flag, open data-quality flags, and `feedFrozenOn`.

**Scope and limits.**

- The universe is U.S.-listed securities with Sharadar SF1 statements.
- ADRs that report in another currency have NULL price-based ratios. Either convert them at a cited FX rate, as `equity-valuation` 2.3.1 does, or exclude them and say so.
- Sector labels are today's, not historical.
- There are no consensus estimates, so there are no revision or surprise screens.
- Backtests come later, opt in, and disclose their biases, including the missing delisting returns.

**Boundaries.**

- When this skill ships, `equity-valuation`'s description gains "Not for screening a universe" (T3).
- `equity-screening`'s description excludes single-company valuation and chart signals.
- `technical-analysis` excludes cross-sectional ranking.

**Phases.**

| Step | fafnir work | Skill release |
|---|---|---|
| 1 | `duk sc` and `factor_screen` over the existing panel; deprecate `ls -S fmp` | `equity-screening` 0.1: bottom-up on fundamentals |
| 2 | The price-factor table | 0.2: momentum, volatility and liquidity screens |
| 3 | Sector aggregates and returns | 0.3: top-down mode |

**Shared material.** The skill shares fafnir's data rules (2.3), its factor definitions (2.3.3) and the peer statistics (B.1, B.3) with `equity-valuation`. See R9.

### Proposal: technical-analysis

**Domain.** Keep it out of `equity-research`, because technical analysis applies to anything with a price history, not just single companies. Separate plugins also stop chart requests from picking up fundamental skills, and the reverse. If it will only ever cover equities and ETFs, putting it in `equity-research` is an acceptable, simpler choice.

**Data and tools.** Checked against fafnir at `632e8a6`.

- fafnir `price_history`: adjusted prices for indicators; raw prices for price levels such as support, resistance and gaps.
- A standalone technical-analysis tool replaces `duk ti`; see [Tooling strategy](#tooling-strategy). `duk ti` offers four indicators today: SMA, EMA, RSI and MACD. The new tool also needs the others skills use, such as ATR, Bollinger bands, stochastics, ADX and on-balance volume.
- `duk rc` stays in duk for returns: simple, log, price difference, cumulative and annualized. The tool's own return functions must pass the shared conformance fixture, so the two can't disagree.
- Volume is stored. `core.daily_price.volume` is raw (shares, in that day's share terms). `mart.v_daily_price_adjusted` back-adjusts it to post-split terms, which volume indicators need across a split. NAV-priced funds carry volume 0, so volume indicators are n.m. for them.
- Charts are built in Python and saved with the report.

**Gaps.** The data is daily only, so there is no intraday analysis. There is no options, positioning or sentiment data.

**Conventions.** The house standard in [authoring-skills.md](authoring-skills.md#financial-skill-conventions) applies:

- state each indicator's definition and parameters;
- keep point-in-time discipline, and compute in code;
- use neutral language, and end with the disclaimer;
- for any backtest, disclose look-ahead and survivorship bias, and that delisting returns aren't in the warehouse.

**Overlap with `equity-screening`.** Momentum as a cross-sectional ranking factor belongs to screening. Chart-based signals on one instrument belong to technical analysis. Each skill's description should exclude the other's requests.

## Tooling strategy

The skills rely on four tools. This is the agreed division of labor, as of 2026-11-25. fafnir facts were checked at `632e8a6`.

| Tool | Role | Changes |
|---|---|---|
| **duk** (fafnir's CLI) | Reads the warehouse, locally or over fafnir's HTTP API. The same functions back the fafnir MCP read tools. | Gains `duk sc`. Loses `ti`, `yc` and FMP in `ls`. Keeps vendor reconciliation reads and `rc`. |
| **fit** | Fixed-income computation | Takes over Treasury-curve work from `duk yc` |
| **technical-analysis tool** (new, standalone) | Indicators computed on price series | Replaces `duk ti` |
| **dismal** | Macro and rates data | Unchanged |

### duk after the change

| | |
|---|---|
| **Warehouse reads** | Every command, with `-S db` as the default |
| **Vendor reads** | `ph` and `mc` only, through an explicit `-S fmp` or `-S sharadar`, in the CLI only |
| **Computation** | `rc`, frozen at return transforms |
| **Added** | `duk sc`, and a matching MCP `factor_screen` tool ([equity-screening](#proposal-equity-screening)) |
| **Removed** | `ti` (to the technical-analysis tool); `yc` and its FMP fallback (to fit); `ls -S fmp`, FMP's lists and the FMP-only dividend filter, which the panel's derived `dividend_yield_ttm` replaces; FMP identifier search |

Rules that go with this:

- **Vendor reads exist for reconciliation.** `scripts/reconcile.sh` uses them, and so does `equity-valuation` Phase 2's `duk -S sharadar ph` check. duk shapes every source into the same frame, so a check is a diff of two duk outputs.
  - A vendor is read only when `-S` names it. No command falls back to a vendor.
  - Vendor reads are never served over the HTTP API or MCP. API keys stay on the client, and agents read only the warehouse.
  - Identity is resolved with `-S db`, and the ticker is then passed to the vendor.
  - Both vendors stay while both subscriptions run, because they catch different errors. A Sharadar read checks the warehouse against its own feed; FMP is an independent second source.
- **`rc` is frozen at return transforms.** Volatility, Sharpe ratio, drawdown and indicators belong to the technical-analysis tool. Total returns come from adjusted closes, which already include dividends, so dividends are never added again.
- **A conformance fixture keeps the two return implementations in step.** It is a CSV of prices with the expected output of every return type, including annualization over 252 and 12 periods, and both duk's and the technical-analysis tool's test suites run it. duk annualizes over 252 periods by default, compounding simple returns and scaling log returns; a tool that chose differently would fail the fixture.
- **Deprecate before removing.** `ls -S fmp` warns for one release before it goes.
- **Coverage is U.S.-listed for now.** New warehouse objects keep currency explicit: thresholds in the trading currency, labelled, and filtered to USD-traded securities for now. If non-U.S. coverage is needed later, it comes from a vendor loaded into the warehouse with tracked provenance (ADR 0015), not from a vendor screener in duk.

### Follow-ups in alpha-tango, timed with the duk release

| ID | Change | Bump |
|---|---|---|
| T1 | `equity-valuation` 2.2 tool map: drop the `duk yc` row, since curve work is already fit's. Drop `duk ti` from the "Returns and indicators" row, since no module uses indicators. Keep `duk rc` and Phase 2's `duk -S sharadar ph`. | MINOR: the tool map changes, outputs don't |
| T2 | `equity-valuation` B.1: once `factor_screen` ships, peer screens may use it beside `screen_securities` | MINOR |
| T3 | `equity-valuation` description: add "Not for screening a universe" when `equity-screening` ships | MINOR |

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
| R9 | **Shared reference files** | `equity-screening` and `equity-valuation` will share fafnir's data rules, factor definitions and peer statistics. Copies kept by hand drift apart. | Maintain each shared file once per domain. `skillkit` copies it into every skill that uses it, and fails the build when a copy drifts. Each skill stays self-contained for upload. |

## Proposed changes to equity-valuation

A review of the 1.0.0 text found the items below. Each changes methodology or behavior and needed the author's decision, and each lists the version bump it needs. The 1.0.0 release itself only fixed a broken cross-reference and Markdown rendering. See the [changelog](../skills/equity-research/equity-valuation/CHANGELOG.md) for what each release changed. Tool-related follow-ups are T1 to T3 under [Tooling strategy](#tooling-strategy).

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
| E12 | B.1 | `feedFrozenOn` is used as a peer screen but is not defined, and the tool that returns it is not named. | Define it in B.1: it is fafnir's own column (ADR 0020), the last session the warehouse holds for a security no vendor feeds. `screen_securities` returns it, from `mart.security_latest` joined to `mart.v_security_profile`; this was checked against fafnir at `632e8a6`. | PATCH |
| E13 | 2.5 and 9.8 | fit reports rates in percent, while the JSON summary uses decimals | Add a Section 8 checklist item: fit percent outputs are converted to decimals in the JSON summary | PATCH |
| E14 | A.2.3 | Bottom-up beta unlevers with D/E but doesn't adjust for peers' cash holdings | Optionally use Damodaran's cash-adjusted unlevered beta, β_U / (1 − cash/firm value), for cash-rich peers, stated as a choice | MINOR |
