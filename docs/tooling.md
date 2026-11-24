# Tooling

The commands, hooks and CI checks that keep the repository consistent. Everything runs on Python 3.10 or later, with the pinned packages in `requirements-dev.txt`. Markdown linting also needs Node.js, for `npx`.

## Contents

- [Setup](#setup)
- [make targets](#make-targets)
- [skillkit](#skillkit)
- [What validate checks](#what-validate-checks)
- [Pre-commit hooks](#pre-commit-hooks)
- [CI jobs](#ci-jobs)
- [Markdown lint notes](#markdown-lint-notes)

## Setup

```bash
make install
```

This installs the Python tools and the git hooks, both pre-commit and pre-push. Without `make`, run:

```bash
python3 -m pip install -r requirements-dev.txt
```

```bash
python3 -m pre_commit install --install-hooks -t pre-commit -t pre-push
```

## make targets

| Target | Does |
|---|---|
| `make check` | Everything CI runs on a pull request: validate, versions, test, lint |
| `make validate` | `skillkit validate` |
| `make catalog` | Regenerates the catalog tables and syncs `marketplace.json` |
| `make versions` | Version gate against `BASE` (default `origin/main`) |
| `make test` | pytest |
| `make lint` | markdownlint, `ruff check`, `ruff format --check` |
| `make format` | `ruff format` and `ruff check --fix` |
| `make package` | Builds release zips into `dist/` |
| `make release-plan` | Shows what the next merge to `main` would release |
| `make plugin-validate` | `claude plugin validate . --strict` (needs Claude Code installed) |
| `make new DOMAIN=… NAME=…` | Scaffolds a skill |
| `make clean` | Removes `dist/` and caches |

## skillkit

`scripts/skillkit.py` is a single-file command-line tool. Its only dependency is PyYAML. `--root` points it at another checkout; by default it works on the repository it lives in.

| Command | Purpose | Notable options |
|---|---|---|
| `validate` | Run every check below. Exit 1 on any error. | `--strict` also fails on warnings |
| `catalog` | Rewrite the tables between `<!-- skills-catalog:begin -->` and `<!-- skills-catalog:end -->` in `README.md` and `skills/README.md`, and sync each domain plugin's `skills` list in `marketplace.json` | `--check` reports drift without writing |
| `check-versions` | Require a version bump and changelog section for every skill whose shipped files changed since the merge base. Also sees uncommitted and untracked files. | `--base origin/main` |
| `package [skill …]` | Build deterministic `<name>-<version>.zip` and `.sha256` files | `--out DIR` (default `dist/`) |
| `release` | For every skill version without a `<name>-v<version>` tag, package it and create the GitHub release with `gh`. Needs `GH_TOKEN`. | `--dry-run` |
| `notes <skill>` | Print a changelog section | `--version X.Y.Z` |
| `new <domain> <name>` | Scaffold from `templates/` and update the catalog | `--description "…"` |
| `list` | List skills | `--json` |

Examples:

```bash
python3 scripts/skillkit.py validate
```

```bash
python3 scripts/skillkit.py check-versions --base origin/main
```

```bash
python3 scripts/skillkit.py notes equity-valuation --version 1.0.0
```

Inside GitHub Actions, findings print as `::error` and `::warning` annotations on the affected file and line.

## What validate checks

**Errors** fail the build:

| Area | Check |
|---|---|
| Layout | `SKILL.md` is at `skills/<domain>/<skill>/SKILL.md`. Domain names are kebab-case. Each domain has a README.md. |
| Frontmatter | Valid YAML mapping. Only portable keys. `name` rules (length, charset, reserved words, equals the directory, unique). `description` is 1 to 1,024 characters, with no angle brackets. `compatibility` is at most 500 characters. `metadata` values are strings. `metadata.version` is semver. `metadata.domain` matches the directory. |
| Body | SKILL.md has instructions after the frontmatter |
| Files | Each skill has README.md and CHANGELOG.md |
| Changelog | Version sections are dated and listed newest first. `[Unreleased]` comes first. The newest section equals `metadata.version`. |
| Marketplace | Valid JSON with `name`, `owner` and `plugins`. Unique plugin names. Relative sources. Every listed skill path exists. Every skill is in exactly one plugin, the one named after its domain. |
| Links | Every relative link and image in every Markdown file resolves. Code blocks and inline code are skipped, and so are URLs. No backslashes in links. |
| Catalog | Generated tables and plugin skill lists are up to date |

**Warnings** are reported but don't fail the build unless you pass `--strict`:

| Check | Why |
|---|---|
| SKILL.md body over 500 lines | Recommended limit for the always-loaded instructions |
| A shipped file not mentioned in SKILL.md | Claude will never find it |
| A reference file over 100 lines without a `## Contents` list | Claude may read only part of a long file |
| A reference file linking to another file in the skill | References should be one level deep |
| `TODO` left in SKILL.md | Unfinished scaffold |
| Description with no "use"/"when" | It may not say when to use the skill |
| A plugin entry with `version` | Pins users to a cached copy (see [versioning](versioning-and-releases.md#plugin-versions)) |

## Pre-commit hooks

`.pre-commit-config.yaml` runs these hooks:

| Stage | Hooks |
|---|---|
| pre-commit | Trailing whitespace (Markdown line breaks kept), end-of-file, LF line endings, YAML/JSON syntax, merge conflicts, files over 1 MB; ruff lint and format; markdownlint; `skillkit catalog` (rewrites generated files: re-stage them); `skillkit validate` |
| pre-push | `skillkit check-versions --base origin/main` |

Run every hook on demand with `python3 -m pre_commit run --all-files`.

## CI jobs

`.github/workflows/ci.yml` runs on every pull request and every push to `main`:

| Job | Steps |
|---|---|
| **Skills and tooling** | `skillkit validate`; `skillkit check-versions` (pull requests only); pytest; ruff; `skillkit package`, with the zips uploaded as the `skill-packages` artifact for 14 days |
| **Markdown lint** | `markdownlint-cli2` |
| **Claude Code marketplace** | `claude plugin validate . --strict`, run from a pinned `@anthropic-ai/claude-code` version |

`.github/workflows/release.yml` runs on pushes to `main` that touch `skills/`, or by hand. It reruns the tests, prints the release plan, and publishes new versions. See [versioning-and-releases.md](versioning-and-releases.md#how-a-release-happens).

Third-party actions are pinned to full commit SHAs, with the version in a comment. Dependabot (`.github/dependabot.yml`) proposes weekly updates for actions and Python tools. The pinned `markdownlint-cli2` and `claude-code` versions in the workflow, Makefile and pre-commit config are updated by hand.

## Markdown lint notes

The configuration is in `.markdownlint-cli2.yaml`. These rules are relaxed:

- line length (MD013): prose is not wrapped;
- duplicate headings, except among siblings (MD024): changelogs repeat "Added" and "Fixed";
- table column style (MD060);
- bold lead-in labels (MD036);
- unlabelled code fences (MD040).

Do not run `markdownlint-cli2 --fix` on skill files. Its list fixer rewrites an indented line that starts with a plus sign as a hyphen bullet. In a formula such as the equity bridge, that silently turns a plus into a minus. Fix skill Markdown by hand, and check the result with `git diff --ignore-blank-lines`.
