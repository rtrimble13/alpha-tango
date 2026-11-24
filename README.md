# alpha-tango

[![CI](https://github.com/rtrimble13/alpha-tango/actions/workflows/ci.yml/badge.svg)](https://github.com/rtrimble13/alpha-tango/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Agent skills for financial analysis.** Each skill packages a professional workflow for Claude: the methods, evidence standards, data-source contracts and report format for one kind of financial work. Claude can then do that work to a consistent, auditable standard.

Skills are organized by financial domain. Each skill is versioned on its own and released as a package you can upload. Each domain is published as a Claude Code plugin from this repository's marketplace.

## Skills

<!-- skills-catalog:begin -->
| Skill | Domain | Version | What it does |
|---|---|---|---|
| [`equity-valuation`](skills/equity-research/equity-valuation/README.md) | equity-research | 2.1.0 | Fundamental equity valuation and analysis to a CFA-charterholder standard. |
<!-- skills-catalog:end -->

The table is generated from each skill's frontmatter by `make catalog`. Planned domains and skills are in the [roadmap](docs/roadmap.md).

## Quick start

### Claude Code (recommended)

Add this repository as a plugin marketplace, then install the domain you need:

```bash
claude plugin marketplace add rtrimble13/alpha-tango
```

```bash
claude plugin install equity-research@alpha-tango
```

You can do the same from inside a session with the `/plugin` command. Then ask for the work in plain language ("Value MSFT as of today"), or call a skill by name: `/equity-research:equity-valuation`.

### claude.ai or the Claude API

Download `<skill>-<version>.zip` from the [Releases](https://github.com/rtrimble13/alpha-tango/releases) page and upload it as a custom skill. Some skills depend on local tools and data. Check the requirements in each skill's guide first: `equity-valuation`, for example, needs the fafnir, dismal and fit tools, which claude.ai's sandbox does not have.

The [getting-started guide](docs/getting-started.md) covers every installation route, including copying a skill into `~/.claude/skills/` and checking that it loaded.

## Repository layout

```text
alpha-tango/
├── .claude-plugin/marketplace.json   Claude Code marketplace: one plugin per domain
├── skills/
│   ├── README.md                     Skill catalog
│   └── <domain>/                     A financial domain, e.g. equity-research
│       ├── README.md                 Domain scope
│       └── <skill>/                  One skill
│           ├── SKILL.md              Instructions for Claude (frontmatter + body)
│           ├── references/           Detail Claude loads when needed
│           ├── scripts/, assets/     Optional code and files the skill uses
│           ├── README.md             User guide (not shipped in packages)
│           └── CHANGELOG.md          Version history (not shipped in packages)
├── templates/                        Scaffolds used by `make new`
├── scripts/skillkit.py               Validation, catalog, versioning, packaging, releases
├── tests/                            Tests for skillkit
├── docs/                             User and contributor documentation
└── .github/                          CI, release workflow, issue and PR templates
```

See [docs/architecture.md](docs/architecture.md) for the design and the reasons behind it.

## Versioning and releases

- Every skill has its own [semantic version](docs/versioning-and-releases.md), set in `metadata.version` in its SKILL.md. Each version has an entry in the skill's CHANGELOG.md.
- CI rejects a pull request that changes a skill's shipped files without a version bump and a changelog entry.
- When a new version reaches `main`, the release workflow tags it `<skill>-v<version>` and publishes a GitHub release with the zip and its SHA-256 checksum.

## Documentation

| Guide | For |
|---|---|
| [Getting started](docs/getting-started.md) | Installing and using skills in Claude Code, claude.ai and the API |
| [Architecture](docs/architecture.md) | How the repository, domains, skills and plugins fit together |
| [Authoring skills](docs/authoring-skills.md) | Writing a new skill or changing an existing one |
| [Versioning and releases](docs/versioning-and-releases.md) | What MAJOR, MINOR and PATCH mean for a skill; how releases happen |
| [Tooling](docs/tooling.md) | `skillkit`, `make` targets, pre-commit hooks and CI checks |
| [Roadmap](docs/roadmap.md) | Planned domains, skills and enhancements |
| [Contributing](CONTRIBUTING.md) | Workflow for proposing and reviewing changes |

## Disclaimer

The skills here produce analysis for informational and educational purposes. Their output is not investment, legal, tax or accounting advice, nor a recommendation to buy or sell any security. Output quality depends on the data sources and models each skill uses. Review it before relying on it.

## License

[MIT](LICENSE)
