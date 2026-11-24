# Changelog: equity-valuation

All notable changes to this skill are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow Semantic Versioning, with the meaning of MAJOR, MINOR and PATCH for a skill defined in [docs/versioning-and-releases.md](../../../docs/versioning-and-releases.md).

## [Unreleased]

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
