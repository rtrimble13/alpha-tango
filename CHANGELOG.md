# Changelog: repository

Changes to the repository's structure, tooling, CI and documentation, by date. Each skill has its own versioned `CHANGELOG.md` in its folder. Find them through the [skill catalog](skills/README.md).

## 2026-11-24

### Added

- The repository structure: `skills/<domain>/<skill>/`, with one Claude Code plugin per domain, published from `.claude-plugin/marketplace.json`.
- The `equity-research` domain and `equity-valuation` 1.0.0 (see [its changelog](skills/equity-research/equity-valuation/CHANGELOG.md)).
- `scripts/skillkit.py`, with tests, to validate skills, the marketplace, links and the catalog; generate the catalog; enforce version bumps; build deterministic release packages; and publish releases.
- CI (validation, version gate, tests, ruff, markdownlint, `claude plugin validate --strict`, package artifact) and a release workflow that tags and publishes new skill versions from `main`.
- Dependabot, pre-commit and pre-push hooks, a Makefile, EditorConfig and Git attributes.
- Templates for new skills and domains, issue forms, a pull-request template and CODEOWNERS.
- Documentation: README, getting started, architecture, authoring, versioning and releases, tooling, roadmap, contributing and security.
