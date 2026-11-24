# Equity valuation: Section 2

Part of the `equity-valuation` skill ([SKILL.md](../SKILL.md)). Section numbers and cross-references (for example 2.6, A.9, T-13) are those of the full standard; the section map in SKILL.md says which file holds each section.

## Contents

- [2.1 Tiers](#21-tiers)
- [2.2 fafnir: access and the tool map](#22-fafnir-access-and-the-tool-map)
- [2.3 fafnir data semantics you must respect](#23-fafnir-data-semantics-you-must-respect)
  - [2.3.1 General](#231-general)
  - [2.3.2 Point-in-time reading and TTM](#232-point-in-time-reading-and-ttm)
  - [2.3.3 The factor panel: definitions to use, not re-invent](#233-the-factor-panel-definitions-to-use-not-re-invent)
- [2.4 dismal: the macro and rates inputs](#24-dismal-the-macro-and-rates-inputs)
- [2.5 fit: fixed-income analytics](#25-fit-fixed-income-analytics)
- [2.6 Known gaps: what fafnir does not hold, and where to get it](#26-known-gaps-what-fafnir-does-not-hold-and-where-to-get-it)

## 2. Data sources and the evidence hierarchy

### 2.1 Tiers

| Tier | Source | Use for | Tag |
|---|---|---|---|
| **1** | **fafnir** warehouse (`rtrimble13/fafnir`): MCP read tools or `duk -S db` | Prices (raw and adjusted), corporate actions, security identity and history, point-in-time financial statements (Sharadar SF1), daily market cap, the factor panel, sector/industry cross-sections | `[F#]` |
| **1** | **dismal** (`rtrimble13/dismal`): `dismal fred \| bls \| bea` | Risk-free rates, real yields, breakeven inflation, credit spreads, corporate bond yields, GDP and potential GDP, inflation, macro context, historical vintages | `[D#]` |
| **calc** | **fit** (`rtrimble13/fit`): `fit curve \| bond \| portfolio` | **A computation engine, not a data source.** Bootstraps and interpolates the Treasury zero curve from dismal's yields. Gives zero, par and forward rates at any tenor; bond yield, z-spread, duration and DV01; fair value, cashflow ladder and rate-shock P&L of a company's debt. Inputs must themselves be sourced. | `[C#]`, with the fit command in the Computation Register |
| **2** | **Primary filings**: SEC EDGAR (10-K, 10-Q, 8-K, DEF 14A, 20-F/40-F), company investor-relations releases and transcripts | Items fafnir lacks (2.6); verifying fafnir figures; business description; guidance | `[S#]` |
| **3** | **Recognized third-party reference data**: Damodaran Online (implied ERP, country risk premia, rating-to-spread tables, industry betas); Kenneth French Data Library; U.S. Treasury; IRS/statute for tax rates | Market-wide parameters that no Tier 1 source produces | `[X#]` |
| **4** | **Other secondary sources** (financial press, vendor sites) | Context and reconciliation only; **never** a valuation input unless the user approves it | `[X#]` + "secondary" |
| — | **Computed** | Anything derived from the above | `[C#]` |
| — | **Assumption** | Forward-looking or judgmental input | `[A#]` |

**Precedence.** Tier 1 beats Tier 2 for data the warehouse holds, except where the filing is the original record and fafnir's version is in doubt (for example, an open DQ flag). In that case use the filing and record the discrepancy. Tier 2 beats Tier 3 for company facts. Never use a lower tier when a higher one has the fact.

**Citing external sources.** Every Tier 2–4 value records its URL or EDGAR accession number, document and page/section/table, the exact value as published, its units, its publication date and the retrieval date. If a page cannot be reached, the value is not used (Section 10).

### 2.2 fafnir: access and the tool map

Prefer the **MCP read profile** (`fafnir-mcp --profile read`). Fall back to `duk -S db` (one plain command per call, with `-o file.csv` to save), which returns the same rows. Free-form SQL (`sql_read`, capped at 500 rows) exists only on the **ops** profile. If it is not available, build cross-sections from per-security calls.

| Need | MCP tool (read profile) | duk equivalent | Notes |
|---|---|---|---|
| Resolve a company | `resolve_symbol(symbol, as_of?)` | `duk th`, `duk ls QUERY` | Accepts `cik:`, `isin:`, `cusip:` and `TICKER@YYYY-MM-DD`. If several securities match, the tool stops; never pick one. |
| Company overview | `security_profile(symbol)` | `duk ls SYMBOL` | Meta, price statistics, actions, DQ. Its beta is 1-year daily vs SPY: context only (A.2.3). |
| Data quality | `dq_summary(symbol)` | (inside `duk ls`) | Must be checked before analysis (Phase 2). |
| Prices | `price_history(symbol, start_date, end_date, adjusted, limit)` | `duk ph SYMBOL [--adj]` | `adjusted=false` is raw, as traded; `true` is split and dividend adjusted (total-return basis). Use adjusted for returns and beta, raw for market cap and per-share price. |
| Market cap, daily | `market_cap_history(symbols[], start_date, end_date)` | `duk mc SYMBOL... --exact` | Raw close × count in force × SF1 share factor. No cap for ETFs, funds or secondary share classes. No float adjustment. |
| Financial statements | `statements_as_of(symbol, statement=income\|balance\|cash, period=annual\|quarter, as_of, limit)` | `duk fs SYMBOL --statement … --period … --as-of D` | Each period at its version in force on `as_of`. Exact decimal strings. `known_from` and `knowledge_source` on every row. |
| Factor row | `factor_row(symbol, as_of?)` | `duk fa SYMBOL [--as-of D]` | Without `as_of`, the latest snapshot; with it, the panel's month-end on or before the date. About 45 derived factors (2.3.3). |
| Corporate actions | `corporate_actions(symbol)` | `duk ca SYMBOL --exact` | Splits and cash dividends by ex-date, as declared. |
| Ticker history | `ticker_history(symbol)` | `duk th SYMBOL` | Renames, reused tickers. |
| Peer universe | `screen_securities(sector[], industry[], exchange, country, market_cap_more_than, market_cap_less_than, is_etf, is_fund, is_actively_trading, include_delisted, limit)`; `list_sectors()`, `list_industries()` | `duk ls --sector … --industry …` | Actively trading only unless `include_delisted=true`. |
| Sector/industry quartiles | `sql_read` on `mart.v_industry_fundamentals` (**ops only**) | — | 16 factors with n, p25, median and p75 per month-end. Groups with fewer than 3 members are suppressed. |
| TTM statements | `sql_read` on `mart.fn_fundamentals_ttm(D)` (**ops only**) | — | On the read profile, build TTM from 4 quarters yourself (2.3.2). |
| Cross-section on any date | `sql_read` on `mart.fn_fundamental_snapshot(D, lag)` (**ops only**) | — | Optional reporting lag in days. |
| Returns and indicators | — | `duk rc -i file --simple\|--log\|--annual-simple …`, `duk ti` | Source-agnostic computation on saved files. |
| Treasury curve | — | `duk yc` (reads **FMP**) | **Do not use for valuation inputs.** Use dismal/FRED yields (Tier 1, official), built into a curve with fit (2.5). `duk yc` is a cross-check only. |

### 2.3 fafnir data semantics you must respect

#### 2.3.1 General
- **Coverage.** Statements are Sharadar SF1 for linked U.S.-listed securities, back to the early 1990s. The factor panel and survivorship-free cross-sections start on **1998-01-01**. Dead issuers are kept: never filter them out of historical cross-sections.
- **The primary share class only.** SF1 files an issuer under one class (GOOGL, BRK.B). A secondary class has no statements or market cap; tools answer with the primary class and say so in `statements_of`. Value the issuer once, then convert to the requested class with the share factor or the filing's conversion terms, cited.
- **Currency.** Statement amounts are in `reported_currency`. If it differs from the trading currency, fafnir's price-based ratios are NULL (`currency_mismatch`). Convert with a cited FX rate (FRED `DEX…` series via dismal) at the right dates: period-average for flows, period-end for stocks.
- **Absent vs. zero.** SF1 writes **0** for an item the filing does not carry and **NULL** for one that does not apply (for example, a bank's current assets). NULL is never 0. Before treating a 0 as real (for example, R&D = 0), check neighbouring periods and the filing.
- **Signs are SF1's.** `capital_expenditure`, `dividends_paid` and buybacks (`net_equity_issuance` < 0) are **negative** cash flows. Negate them where a formula expects a positive outlay.
- **Share terms.** Statement share counts are stored in the share terms of each version's `known_from`. Before comparing counts across a split, put them in the as-of date's terms: multiply by the product of split ratios with ex-date in `(known_from, as_of]`, from `corporate_actions`. The panel's `shares_outstanding_as_of` has already done this. Never divide a raw price by a per-share figure in different share terms.
- **Classification is today's.** `sector_name` and `industry_name` are current, not historical. For historical peer sets, say so and check each peer's business at the time from its filings.
- **Not in SF1 (balance sheet):** minority (noncontrolling) interest and preferred stock balances. fafnir's `enterprise_value` therefore **omits both**. See A.9.
- **EBIT in SF1** is net income + tax + interest expense, so it includes non-operating items. `operating_income` is the operating line. Use `operating_income` for NOPAT, and reconcile the difference (non-operating income) to the filing when it is material.
- **No interest income line.** Net interest = `interest_expense` only. Interest income, if needed, comes from the filing.

#### 2.3.2 Point-in-time reading and TTM
- A statement version is **in force** at D when `superseded_at IS NULL AND known_from <= D AND (known_to IS NULL OR D < known_to)`. The tools apply this rule when given `as_of`.
- `knowledge_source`: `filed` (first report, known from the SEC filing date), `observed` (a restatement, known from the day fafnir loaded it), `estimated` (inferred from the next filing). For strict historical work, flag or exclude `estimated` rows.
- **Join statements on `fiscal_date`**, never on knowledge dates.
- **TTM (read profile):** sum 4 quarterly flows only when the quarters are **contiguous**: consecutive fiscal labels, each period end 8–18 weeks after the previous one, every flow non-NULL. Otherwise TTM is NULL; never use a partial sum. Stocks (balance-sheet items) take the latest quarter and are never summed.
- **Average balances** = mean of the current and year-ago period-end balances. NULL without the year-ago balance.

#### 2.3.3 The factor panel: definitions to use, not re-invent
When a metric exists in `factor_row`, use fafnir's definition for consistency, and cite the column. Key definitions (fafnir `doc/fundamentals.md`):

| Column | Definition |
|---|---|
| `market_cap` | raw close × `shares_outstanding_as_of` × `share_factor` |
| `enterprise_value` | market cap + total debt − cash (no NCI, no preferred) |
| `earnings_yield` | net income to common / mcap (P/E = 1/EY, only when EY > 0) |
| `book_to_price` | parent equity / mcap; NULL when equity ≤ 0 |
| `sales_to_price`, `cash_flow_to_price`, `fcf_yield` | revenue, CFO, (CFO + capex) over mcap |
| `ev_to_ebitda`, `ev_to_sales`, `ev_to_ebit`, `ev_to_fcf` | EV over EBIT + D&A, revenue, EBIT, FCF |
| `roe` | NI to common / avg parent equity |
| `roa` | NI / avg total assets |
| `roic` | (EBIT − income tax) / (total debt + parent equity − cash) |
| `gross_profitability` | gross profit / total assets |
| margins, `asset_turnover` | on revenue; turnover on avg total assets |
| `accruals` | (NI − CFO) / avg total assets |
| `debt_to_equity`, `net_debt_to_ebitda`, `interest_coverage` (EBIT / interest), `current_ratio`, `quick_ratio` | |
| `altman_z` (1968 original), `piotroski_f` (0–9) | |
| growth: `revenue_growth_yoy`, `eps_growth_yoy`, `net_income_growth_yoy`, `revenue_cagr_3y`, `asset_growth_1y` | |
| payout: `dividend_yield_ttm`, `buyback_yield_ttm`, `shareholder_yield` | |
| context: `basis` (ttm/annual), `fiscal_date`, `known_from`, `knowledge_source`, `days_since_filing`, `price_date`, `close_raw`, `close_adjusted`, `currency_mismatch` | |

**Denominator rule.** fafnir returns NULL for a ratio whose denominator is NULL, zero or negative, and nothing is winsorized. Report NULLs as "n.m." (not meaningful) with the reason. Never fill them.

### 2.4 dismal: the macro and rates inputs

Run `dismal doctor` (or `dismal fred doctor`) first. Pass `--format json` or `csv` explicitly. Check exit codes (0 ok; 3 bad id; 4 rate limit; 6 no data under `--strict`; 7 missing key). Confirm each series with `dismal fred series info ID --notes` and record its title, units and frequency.

| Input | Primary FRED series | Notes |
|---|---|---|
| Nominal risk-free (long) | `DGS10` (10-yr CMT, daily); `DGS20`, `DGS30` | Match the duration of the cash flows; the 10-year is the conventional default. Use the value on the as-of date, or the last observation before it. |
| Short rate | `DGS3MO`, `DTB3` | For short-horizon or CAPM-period checks |
| Real risk-free | `DFII10` (10-yr TIPS) | For real-terms models |
| Inflation expectations | `T10YIE` (10-yr breakeven), `T5YIFR` (5y5y forward) | Anchor for nominal terminal growth |
| Realized inflation | `CPIAUCSL`, `PCEPILFE` (`--units pc1` for YoY) | Context, pass-through |
| Real GDP, potential | `GDPC1`, `GDPPOT` (CBO) | Anchor for long-run real growth |
| Nominal GDP | `GDP` | Long-run nominal growth anchor |
| Corporate yields | `BAA`, `AAA` (Moody's seasoned) | Cost-of-debt cross-check |
| Credit spreads | `BAMLC0A0CM` (IG OAS), `BAMLC0A4CBBB` (BBB OAS), `BAMLH0A0HYM2` (HY OAS); other rating buckets via `dismal fred series search "ICE BofA <rating> OAS"` | Spread for the rating or synthetic rating (D.4) |
| FX | `DEXUSEU`, `DEXJPUS`, … | Currency conversion |
| Equity market level | `SP500` | Context only. Total-return market proxy comes from fafnir SPY adjusted prices. |

**Historical work:** use `--as-of D` (ALFRED) for revised series (GDP, CPI and similar) so that only the vintage known on D is used. Market series (yields, spreads) are not revised; read the observation on or before D.

**Verify ids.** The ids above are starting points. Resolve and confirm each with `dismal fred search` / `series info` before use, and cite the confirmed title.

**The full Treasury curve.** For curve work (2.5), pull every constant-maturity tenor FRED publishes for the date in one call, for example `dismal fred data DGS1MO DGS3MO DGS6MO DGS1 DGS2 DGS3 DGS5 DGS7 DGS10 DGS20 DGS30 --start D --end D -f json`. Confirm the tenor list with `dismal fred series search "market yield treasury constant maturity"`. Add any other tenors found, such as 2-, 4- and 6-week bills. Use the last observation on or before D for each series. If any tenor is missing on D, record it and do not fill it in.

### 2.5 fit: fixed-income analytics

`fit` (`rtrimble13/fit`, C++20 CLI, v0.1) turns market yields into a curve and prices fixed-rate debt off it. Everything it computes is `[C]`. Its inputs are dismal yields `[D]`, filing terms `[S]` and cited prices or spreads `[S]`/`[X]`. Record the exact command line, input CSV file and output in the Computation Register.

**Contract**
- Check availability with `fit --version`. If it is missing, build it per its README (`cmake --preset release && cmake --build --preset release`), or do the step by a disclosed alternative method.
- Always run with `--format json` (full precision, 12 significant digits). Exit code 0 means success, 1 a data or runtime error, 2 a usage error. Errors are on stderr, and a failed run writes nothing to stdout.
- Units: rates, coupons and yields in **percent**; spreads and shifts in **bp**; prices per 100 face, clean unless stated. Zero rates are continuously compounded on ACT/365F (`zero_cc_pct`). `zero_sa_pct` and `par_sa_pct` are semi-annual. State which one each valuation input uses.
- **Never use `examples/data/*.csv`.** It is illustrative, not market data.

**Building the risk-free curve from dismal (`fit curve build`)**
1. Write a quotes CSV (`type,tenor,rate[,daycount,frequency]`) from the dismal pull in 2.4, with a comment line citing the dismal command and date.
2. Map conventions:
   - 1-year to 30-year constant-maturity yields are semi-annual par yields: `par` (fit's default, semi-annual ACT/ACT).
   - Bill tenors (under 1 year) are published as bond-equivalent yields: `deposit` with `daycount` set to `act/365`. fit's own example enters bills as ACT/360 money-market yields; do not copy that for FRED data.
   - Cite Treasury's published yield-curve methodology for these conventions, and note any you could not confirm.
3. Run `fit curve build --curve quotes.csv --asof D --interp monotone-convex --calendar us --format json`. This is the default: Hagan-West monotone convex gives continuous, positive forwards.
   - Check Treasury's published methodology for the method it uses to build its own curve, cite it, and match it where you can.
   - Show the default `flat-forward` interpolation as a robustness check if results differ materially.
4. **QA:** `max_repricing_error_bp` must be at most 0.01. Otherwise stop and investigate the quotes. Report the node table (T-13).
5. **Read rates:** `fit curve query … --tenors 5Y,10Y,20Y,30Y` (zero, par, instantaneous forward, discount factor). `fit curve forwards` gives a forward strip. `fit curve query --horizon NY` gives the forward-implied curve N years out.

**Where the skill uses fit**

| Use | Command | Feeds |
|---|---|---|
| Risk-free rate at any maturity (not just published tenors) | `fit curve query` | A.2.1, A.8 |
| Forward-implied rates (is a flat r_f over the forecast period consistent with the curve?) | `fit curve forwards`; `fit curve query --horizon` | A.2.1, A.8, A.10 sensitivity |
| Yield to maturity and z-spread of a company bond from a cited price | `fit bond yield --maturity … --coupon … --frequency … --daycount … --price P --curve treasury.csv --asof D` | A.2.5 cost of debt (market route) |
| Fair value of the company's fixed-rate debt | `fit portfolio value --portfolio debt.csv --curve treasury.csv --asof D` (one row per note from the 10-K debt footnote; `price` where cited, else `zspread` from the rating's spread) | A.2.6 weights, A.9 bridge |
| Debt maturity and cashflow ladder | `fit portfolio cashflows` | D.3 |
| Rate sensitivity of the debt | `fit portfolio risk --key-tenors 2Y,5Y,10Y,30Y`; `fit portfolio scenario --shifts=-100,0,100` | D.3 |
| Marginal cost of new debt at tenor T | Par rate at T from the curve + the rating's spread | D.6 WACC curve |
| PV of disclosed debt-like cashflows (lease or pension schedules) | `fit bond cashflows` / zero-coupon positions at the cited discount spread; or discount factors from `fit curve query --dates …` | A.9 |

**Limits (v0.1):** fit handles fixed-rate bullet and zero-coupon bonds in one currency only. It does not price floaters, callables, convertibles, amortizing term loans or inflation-linked bonds. Its only spread measure is z-spread (continuously compounded: no OAS, G-spread or asset-swap spread), and its risk measures come from zero-rate bumps. For instruments outside that scope:
- use the carrying value or the 10-K fair-value disclosure `[S]`;
- approximate a floater at par plus or minus its spread (disclosed);
- for a callable, use the yield-to-worst price from a cited source;
- list each such case in the data-gaps section.

Treating an FRED ICE BofA OAS as a z-spread for a bullet bond is an approximation. Disclose it and show ±25 bp of sensitivity.

### 2.6 Known gaps: what fafnir does not hold, and where to get it

| Item | Why it matters | Source (in order) | If unavailable |
|---|---|---|---|
| Consensus estimates, guidance | Forward multiples, near-term forecasts | User-supplied or approved vendor; company guidance in 8-K/earnings release [S] | Trailing multiples only; forecasts are analyst assumptions anchored to history, labelled as such |
| Equity risk premium | Cost of equity | Damodaran current implied ERP [X] (with month); or a historical ERP from Damodaran/French data, stating the window and arithmetic vs geometric; or a user/house ERP | **Stop**: cost of equity cannot be set (Section 10) |
| Rating-to-spread table, synthetic rating table | Cost of debt | Damodaran `ratings` table, current edition [X]; agency rating from the company's filings/IR [S] | Use the BBB/IG OAS from FRED with a disclosed rating judgment |
| Marginal tax rate | WACC, NOPAT | Statute (U.S. federal 21%, IRC §11(b)) [X] plus a state estimate from the 10-K tax footnote's rate reconciliation [S] | Effective rate from fafnir (tax / EBT), disclosed as such |
| Noncontrolling interest | EV bridge | 10-K balance sheet [S]; cross-check with the identity NCI ≈ total assets − total liabilities − parent equity [C] | Use the derived identity, flagged |
| Preferred stock | EV bridge, cost of capital | 10-K [S]. A non-zero `preferred_dividends` signals it exists. | **Stop** if preferred dividends are material |
| Lease liabilities | Debt, EV, WACC weights | 10-K lease footnote [S]. Check whether SF1's `total_debt` includes operating leases for this company; never assume. | Disclose and run sensitivity both ways |
| Options, RSUs, convertibles | Diluted shares | 10-K equity-compensation and debt footnotes [S] (treasury-stock and if-converted methods) | `weighted_average_shares_diluted` [F], disclosed as an approximation |
| Debt maturities, coupons, fair value | Market value of debt, refinancing risk | 10-K debt footnote [S] | Book value of debt as proxy, disclosed |
| Pensions/OPEB deficit | Debt-like claims | 10-K footnote [S] | Disclose omission |
| Segment data, unit economics | Driver-based forecasts | 10-K segment note, MD&A [S] | Forecast at consolidated level |
| Non-recurring items | Normalized earnings | 10-K/10-Q MD&A and notes [S] | Unadjusted, flagged |
| Float, insider holdings | Liquidity context | DEF 14A, 13F/13D/G [S] | Omit |
| Delisting returns | Historical studies | Not in the warehouse; returns run to the last trade | Disclose |
