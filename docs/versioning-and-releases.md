# Versioning and releases

Every skill is versioned on its own with [Semantic Versioning](https://semver.org/), and released automatically when a new version reaches `main`.

## Contents

- [What is versioned](#what-is-versioned)
- [What MAJOR, MINOR and PATCH mean for a skill](#what-major-minor-and-patch-mean-for-a-skill)
- [Changelogs](#changelogs)
- [The version gate in CI](#the-version-gate-in-ci)
- [How a release happens](#how-a-release-happens)
- [Pre-releases](#pre-releases)
- [Plugin versions](#plugin-versions)
- [Fixing a bad release](#fixing-a-bad-release)
- [Recommended repository settings](#recommended-repository-settings)

## What is versioned

| Thing | Version lives in | Example | Bumped when |
|---|---|---|---|
| A skill | `metadata.version` in its SKILL.md frontmatter | `"1.0.0"` | Any change to a file the skill ships (SKILL.md, `references/`, `scripts/`, `assets/`) |
| A skill's output schema | Inside the skill's instructions | `equity-valuation-report/1.1` | The structure of a machine-readable output changes |
| The repository (tooling, CI, docs) | Dated sections in the root [CHANGELOG.md](../CHANGELOG.md) | `## 2026-11-24` | Not versioned; changes are logged by date |

A skill's user guide (`README.md`) and `CHANGELOG.md` are not shipped. Editing only those files needs no version bump.

The version is a quoted string (`version: "1.0.0"`), because the Agent Skills spec requires `metadata` values to be strings. An unquoted `1.0` would be read as a number.

## What MAJOR, MINOR and PATCH mean for a skill

A skill is a contract between its author, the people who rely on its output and any tools that read that output. Bump the number for the strongest effect the change has on that contract.

| Bump | Meaning | Examples |
|---|---|---|
| **MAJOR** (`2.0.0`) | Output or behavior changes incompatibly. Reports made before and after are not comparable, or something downstream breaks. | Changing the default valuation method or a methodological default that moves values materially (such as the beta method or the SBC treatment). Removing or renumbering report sections or table IDs. A breaking change to the JSON summary schema. Dropping a supported task. Requiring a new tool or data source. Renaming the skill. Changing or removing a prime directive. |
| **MINOR** (`1.1.0`) | New capability that leaves existing behavior unchanged | A new module, model or optional table. A new optional data source or fallback. An additive JSON field (schema `1.0` → `1.1`). Support for a new security type. Broader triggering. |
| **PATCH** (`1.0.1`) | Corrections and clarifications with no intended change to outputs | Typos and wording. A broken cross-reference fixed. Formatting. A clearer explanation of an existing rule. A corrected example that the rules already implied. |

When a change fixes a methodological error that moves outputs, for example a wrong sign in a formula, treat it as MAJOR. It is a fix, but users comparing old and new reports need to know that the numbers changed. Say so plainly in the changelog.

Before `1.0.0`, a skill is in development: `0.y.z` versions may change in any way, and MINOR bumps are used for breaking changes.

## Changelogs

Each skill keeps a `CHANGELOG.md` in [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format:

```markdown
## [Unreleased]

## [1.1.0] - 2026-12-15

### Added

- Sum-of-the-parts valuation for conglomerates (A.12).

### Changed

- Bottom-up beta is now the default when the regression R² is below 0.3 (A.2.3).
```

The validator enforces these rules:

- An optional `## [Unreleased]` section comes first. Use it to collect notes while a change is in progress.
- Every version has a section `## [x.y.z] - YYYY-MM-DD`. Sections are listed newest first.
- The newest version section matches `metadata.version` in SKILL.md.

Use the standard categories: **Added**, **Changed**, **Deprecated**, **Removed**, **Fixed**, **Security**. Write for the skill's users: say what the skill now does differently, and cite the section it affects. A version's section becomes the text of its GitHub release.

## The version gate in CI

On every pull request, `skillkit check-versions` compares the branch with its base:

1. It lists the files the pull request changes.
2. For each skill whose shipped files changed, it requires two things:
   - `metadata.version` is greater than the version on the base branch;
   - `CHANGELOG.md` has a section for the new version.
3. A new skill passes with any valid starting version (normally `0.1.0` or `1.0.0`). A removed skill is reported as a warning. Its tags and downloads stay available.

Run it locally before pushing. The pre-push hook also runs it:

```bash
make versions
```

## How a release happens

```text
PR with version bump ──► CI passes ──► merge to main ──► release workflow
                                                          1. runs the tests and validator
                                                          2. finds every skill whose <name>-v<version> tag is missing
                                                          3. builds <name>-<version>.zip and .sha256
                                                          4. creates the tag and GitHub release, with the
                                                             changelog section as release notes
```

- **Tag:** `<skill-name>-v<version>`, for example `equity-valuation-v1.0.0`, at the merge commit.
- **Assets:** `equity-valuation-1.0.0.zip`, the uploadable skill folder, and `equity-valuation-1.0.0.zip.sha256`.
- **Idempotent:** a version that already has a tag is skipped. Re-running the workflow, or merging an unrelated change, releases nothing new.
- **Several skills in one merge:** each gets its own tag and release.

To preview what the next merge would release:

```bash
make release-plan
```

The workflow can also be started by hand from the Actions tab (`workflow_dispatch`), for example after a transient failure.

## Pre-releases

A version with a pre-release suffix, such as `1.1.0-rc.1`, is published as a GitHub **pre-release**. Under Semantic Versioning, `1.1.0-rc.1` sorts before `1.1.0`, and the version gate respects that ordering. Use a pre-release to share a candidate for review on claude.ai or the API before calling it final.

The plugin marketplace serves whatever is on `main`. If Claude Code users should not receive a pre-release yet, keep the change on a branch until it is final.

## Plugin versions

The marketplace's plugin entries deliberately carry no `version` field. Claude Code resolves a plugin's version from the plugin manifest first, then from the marketplace entry. When neither is set, it uses the git commit. A fixed `version` string would hold every user on their cached copy until someone edited that string, however many skills changed. Leaving it out means `claude plugin update` always delivers what is on `main`.

`skillkit validate` warns if a plugin entry gains a `version` field.

The skill versions inside a plugin remain the record of what changed. Each skill's `metadata.version` and changelog say exactly which version a user has.

## Fixing a bad release

Releases are immutable: do not delete or move tags, because users and automation may have pinned them.

1. Fix forward. Open a pull request with the fix and a new PATCH version (or MAJOR, if outputs change), and merge it. The release workflow publishes it.
2. Mark the bad release on GitHub. Edit its notes to point to the fixed version, and, if it is harmful, tick "Set as a pre-release" so that it no longer shows as the latest.
3. Explain what was wrong in the new version's changelog section, under **Fixed**.

## Recommended repository settings

These are set in GitHub, not in files:

- **Branch protection on `main`:** require a pull request, at least one approving review (CODEOWNERS), and the status checks *Skills and tooling*, *Markdown lint* and *Claude Code marketplace* to pass. Disallow force pushes.
- **Actions → Workflow permissions:** "Read repository contents" is enough. The release job asks for `contents: write` itself.
- **Private vulnerability reporting:** enable it so that [SECURITY.md](../SECURITY.md) reports can be filed privately.
