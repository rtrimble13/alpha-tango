# equity-valuation

Fundamental equity valuation and analysis to a CFA-charterholder standard, with every number sourced, computed in code or registered as an assumption.

| | |
|---|---|
| **Domain / plugin** | `equity-research` |
| **Current version** | see `metadata.version` in [SKILL.md](SKILL.md) and the [changelog](CHANGELOG.md) |
| **Report schema** | `equity-valuation-report/1.0` (Section 9.8) |
| **Runs best in** | Claude Code, or another agent runtime with a shell, Python 3 and the data tools below |
| **License** | MIT |

This page is the user guide. The instructions Claude follows are in [SKILL.md](SKILL.md) and its [`references/`](references/) files.

## Contents

- [What it does](#what-it-does)
- [Requirements](#requirements)
- [Using the skill](#using-the-skill)
- [What you get](#what-you-get)
- [How an engagement runs](#how-an-engagement-runs)
- [Checking a report](#checking-a-report)
- [When the skill stops](#when-the-skill-stops)
- [Limitations](#limitations)
- [Files in this skill](#files-in-this-skill)
- [Versions](#versions)

## What it does

The skill acts as a senior fundamental equity analyst. It works from the CFA Program curriculum (Equity Valuation, Financial Statement Analysis, Corporate Issuers) and the practitioner texts behind it (Damodaran; Koller, Goedhart and Wessels; Penman). It does four kinds of work:

| Task | Question it answers | Module | Example request |
|---|---|---|---|
| 1. Fair value | What is the equity worth per share, and why? | A: Intrinsic valuation (DCF, DDM, residual income) | "Value Microsoft." |
| 2. Relative value | Is it cheap or expensive against peers, its sector and its own history? | B: Relative valuation | "Is Coca-Cola cheap against its peers and its own 10-year history?" |
| 3. Decomposition | What drives profitability and growth, and how durable is it? | C: DuPont, ROIC tree, margins, working capital, earnings quality | "What drove the change in Costco's ROE over the last five years?" |
| 4. Capital structure | How is it financed, what does that cost, and is it sound? | D: Leverage, coverage, credit view, WACC curve | "Analyze Ford's capital structure and its optimal debt ratio." |

A full valuation (Task 1) runs all four modules. Modules C and D supply the inputs, A produces the value, and B is the cross-check. Any module can also be run on its own.

## Requirements

The skill never states a fact from memory (prime directive 1). It needs live access to its data sources. Without them it can only report what is missing.

| Component | Role | Notes |
|---|---|---|
| **fafnir** warehouse (`rtrimble13/fafnir`) | Tier 1: prices, corporate actions, point-in-time statements (Sharadar SF1), market cap, factor panel | Reached through the MCP read profile (`fafnir-mcp --profile read`), or the `duk` CLI as a fallback. With the **ops** profile (`sql_read`), the skill can also use industry quartiles, TTM and cross-section views. |
| **dismal** CLI (`rtrimble13/dismal`) | Tier 1: FRED, BLS and BEA series (Treasury yields, breakevens, credit spreads, GDP, inflation), including ALFRED vintages | Needs its API key(s) configured. The skill runs `dismal doctor` first, and exit code 7 means a key is missing. |
| **fit** CLI (`rtrimble13/fit`, v0.1) | Computation: Treasury curve bootstrap and interpolation, bond yield and z-spread, fair value and rate risk of the company's debt | The skill checks `fit --version`, and builds fit from source with CMake if it is missing. |
| **Python 3** | All arithmetic | The skill writes a calculation script for each report and saves it with the report. |
| **Web access** | Tier 2 and 3 sources: SEC EDGAR filings, company IR, Damodaran Online (implied ERP, rating spreads, country risk), Kenneth French Data Library, U.S. Treasury | Every external value is cited with its URL or accession number. |

**Where it runs.** Claude Code is the intended host: it has the shell, file system and MCP access the workflow needs. The skill also uploads to claude.ai and the Claude API, because its frontmatter is portable. Their code-execution sandboxes do not have fafnir, dismal or fit, so there the skill will stop at its data gates. See [docs/getting-started.md](../../../docs/getting-started.md) for installation on each surface.

## Using the skill

Ask in plain language. Claude loads the skill when a request matches its description. In Claude Code you can also call it by name: `/equity-research:equity-valuation` when installed as a plugin, or `/equity-valuation` when installed as a personal or project skill.

### Example requests

```text
Value AAPL as of today.
Quick look at NVDA's valuation as of 2024-06-30.
Is KO cheap relative to its beverage peers and its own history since 2010?
Decompose Costco's ROE change from FY2020 to FY2025 and tell me how durable it is.
What is Ford's optimal capital structure, and what WACC does it imply?
Value JPM. Use our house ERP of 5.0% and the rating scale Overweight / Neutral / Underweight.
```

### What it asks you, and what it assumes (Phase 0)

The skill asks before starting if it cannot tell which security you mean or which task you want. Everything else has a default, and the report states each default it applied.

| Parameter | Default if you don't say |
|---|---|
| Company or security (ticker, CIK, ISIN, CUSIP, or `TICKER@YYYY-MM-DD`) | Asks |
| Task(s) | Asks if unclear; "value X" means Task 1 with all modules |
| As-of (knowledge) date | Today, using current knowledge including restatements |
| Valuation currency | The trading currency |
| Share class | The one named; for an issuer, its primary class |
| Standard of value | Intrinsic value per share for a minority, marketable interest |
| Forecast horizon | 5 years explicit, extended to 10 when growth is far from steady state |
| Rating vocabulary | None: the report says "estimated value is X% above/below the current price" |
| Depth | Full report. Ask for a **quick look** to get only the summary, key tables and data gaps. |

You can also supply house parameters: an equity risk premium, a rating vocabulary, consensus estimates, or approval of a Tier 4 vendor. The skill tags them "user-supplied" in the Assumption Register.

**Historical analysis.** Give an as-of date and the skill uses only what was knowable then: point-in-time statements, prices on or before the date, ALFRED vintages for revised macro series, and sources published by that date.

## What you get

A full engagement produces a report package in the working directory:

| Output | What it contains |
|---|---|
| **Report** (Markdown) | Twelve sections in a fixed order: summary, company and security, historical performance, capital structure and cost of capital, forecast and assumptions, intrinsic valuation, relative valuation, valuation synthesis, risks, data gaps, appendices and disclaimer. Single-module tasks mark the other sections "out of scope". |
| **Standard tables** | T-1 summary box to T-14 debt valuation, including peer comparison (T-4), DCF build (T-8), EV-to-equity bridge (T-9), sensitivity grids (T-10), football field (T-11), cost-of-capital build (T-12) and risk-free curve (T-13). |
| **Registers** | Source Ledger (every retrieved value), Assumption Register (every judgment, with anchor evidence and sensitivity), Computation Register (every fit command). |
| **JSON summary** | A fenced `equity-valuation-report/1.0` block at the end of the report, for comparing reports across companies or feeding other tools. |
| **Calculation script and data files** | The Python script and the CSV/JSON pulls it reads. Rerunning the script reproduces every number in the report. |

### Provenance tags

Every number in a report carries a tag that links it to its evidence:

| Tag | Meaning | Example |
|---|---|---|
| `[F#]` | Retrieved from fafnir | `$394.3bn [F3]` |
| `[D#]` | Retrieved from dismal (FRED/BLS/BEA) | `4.21% [D1]` |
| `[S#]` | Primary filing (EDGAR, company IR) | `[S4]` |
| `[X#]` | Third-party reference data (Damodaran, French, Treasury, statute) | `21.0% [X2]` |
| `[C#]` | Computed in code (including fit output) | `8.4% [C7]` |
| `[A#]` | Assumption in the register | `3.0% [A4]` |

### Fair value and confidence

A fair value is a point estimate with a range. Language is neutral: "the estimate is 18% above the current price". Confidence is High, Medium or Low. It is set by the weakest of six factors: data completeness, agreement between models, width of the sensitivity range, the terminal value's share of total value, how predictable the business is, and peer quality (Section 9.7).

## How an engagement runs

| Phase | What happens |
|---|---|
| 0. Intake | Confirms the security, task, as-of date and defaults |
| 1. Identify | Resolves the security without guessing between matches, records its identity, checks it is an operating company |
| 2. Data-integrity gate | Data-quality flags, statement coverage, restatements, and reconciliation of three headline figures to the 10-K within 0.5% |
| 3. Data pack | Statements, prices, market cap, corporate actions, factors, benchmark, peers, macro and rates, the fitted Treasury curve and the company's debt notes |
| 4. Standardize | Builds the standardized model (EBITDA, NOPAT, FCFF/FCFE, NWC, invested capital, and so on) in code |
| 5. Modules | Runs C, then D, then A, then B for a full valuation |
| 6. QA | Works through the full checklist in Section 8 |
| 7. Report | Writes the report package to the Section 9 standard |

Expect a full valuation to be a long, multi-step session with many tool calls. Ask for a quick look, or a single task, when you need something faster.

## Checking a report

1. Read the summary (T-1) and the data-gaps section first. Together they tell you how much weight the conclusion can bear.
2. Pick any number and follow its tag to the Source Ledger, Computation Register or Assumption Register.
3. Rerun the saved script against the saved data files. The numbers must reproduce.
4. Look at the sensitivity grids and the reverse DCF. They show which assumptions the conclusion depends on.
5. For a report that will be published or used for a decision, say so. The skill then has an independent reviewer agent, which did not build the model, rerun the QA checklist and recompute the summary figures.

## When the skill stops

The skill would rather stop than guess (Section 10). The common stop points, and how to get past them:

| Stop | Why | What you can do |
|---|---|---|
| Ambiguous security | Several securities match the identifier | Give the exchange, CIK, ISIN, or `TICKER@YYYY-MM-DD` |
| Reconciliation fails by more than 0.5% | fafnir and the 10-K disagree with no explanation | Point to the filing or restatement that explains it, or accept that the item is excluded and disclosed |
| ETF or fund | The models are for operating companies | Out of scope |
| Statements more than 2 years old | No current basis for valuation | Choose an earlier as-of date or another company |
| Method doesn't fit | For example, FCFF/WACC for a bank | Accept the alternative the skill proposes (A.1) |
| No equity risk premium | Cost of equity cannot be set | Supply a house ERP, or approve Damodaran's implied ERP as the source |
| Material preferred stock with no data | The EV bridge and cost of capital are incomplete | Provide the filing data |
| fit curve repricing error above 0.01 bp | Bad or inconsistent curve quotes | The skill investigates the quotes; check dismal's data for the date |

For an immaterial gap (under 2% of value), the skill proceeds and discloses the gap. For a material gap with a defensible proxy, it uses the proxy, shows the sensitivity and lowers confidence.

## Limitations

- **Coverage** is fafnir's: U.S.-listed securities with Sharadar SF1 statements, back to the early 1990s. The factor panel and survivorship-free cross-sections start in 1998.
- **Sector and industry labels are current**, not historical. For historical peer sets, the skill checks each peer's business from its filings.
- **No consensus estimates** in the warehouse. Forward multiples need cited or user-supplied estimates. Otherwise forecasts are assumptions anchored to history.
- **fit v0.1 prices only fixed-rate bullet and zero-coupon bonds.** Floaters, callables, convertibles and term loans are carried at book or disclosed fair value, and listed as gaps.
- **Not investment advice.** Reports give no personalized advice, use rating language only in a vocabulary you set, and end with the standard disclaimer.

## Files in this skill

```text
equity-valuation/
├── SKILL.md                              Hub: role, section map, Sections 1 (prime directives), 3 (workflow), 10 (data gaps)
├── references/
│   ├── 02-data-sources.md                Evidence tiers; fafnir, dismal and fit usage; known gaps
│   ├── 04-module-a-intrinsic-valuation.md
│   ├── 05-module-b-relative-valuation.md
│   ├── 06-module-c-decomposition.md
│   ├── 07-module-d-capital-structure.md
│   ├── 08-qa-checklist.md
│   ├── 09-reporting-standard.md          Report template, tables T-1 to T-14, registers, JSON summary
│   └── 11-formula-appendix.md
├── README.md                             This guide (not shipped in release packages)
└── CHANGELOG.md                          Version history (not shipped in release packages)
```

Section numbers are the same as in the original single-file standard, so a cross-reference such as "A.9" or "T-13" means the same thing in every file. SKILL.md's section map says which file holds each section. Claude reads a reference file when the work reaches it, which keeps the instructions it loads up front short.

## Versions

The skill version is in `metadata.version` in SKILL.md. Every change is recorded in [CHANGELOG.md](CHANGELOG.md). The skill version and the report schema (`equity-valuation-report/1.0`) are versioned separately. A change to the JSON summary's structure bumps the schema and is a MAJOR change to the skill. See [docs/versioning-and-releases.md](../../../docs/versioning-and-releases.md).

---

*This skill produces analysis for informational purposes. It is not investment advice or a recommendation to buy or sell any security.*
