# Authoring skills

How to write a new skill, or change an existing one, so that it passes review and works well for users.

## Contents

- [Quick start](#quick-start)
- [Frontmatter](#frontmatter)
- [Writing the description](#writing-the-description)
- [Structuring the body](#structuring-the-body)
- [Reference files, scripts and assets](#reference-files-scripts-and-assets)
- [Financial-skill conventions](#financial-skill-conventions)
- [The user guide (README.md)](#the-user-guide-readmemd)
- [Testing a skill](#testing-a-skill)
- [Changing an existing skill](#changing-an-existing-skill)
- [Review checklist](#review-checklist)

## Quick start

```bash
make new DOMAIN=fixed-income NAME=bond-relative-value
```

This creates `skills/fixed-income/bond-relative-value/` with a SKILL.md, README.md and CHANGELOG.md from `templates/`, starting at version `0.1.0`. If the domain is new, it also creates the domain README and a plugin entry in the marketplace. The catalog tables are regenerated too.

Then:

1. Write the description and body of SKILL.md. Replace every `TODO`: the validator warns until they are gone.
2. Add reference files or scripts if the skill needs them, and link each one from SKILL.md.
3. Write the user guide in README.md.
4. Run `make check`.
5. Try the skill on real requests. Link it into `~/.claude/skills/` as [getting-started.md](getting-started.md#claude-code-install-a-single-skill-by-hand) describes.
6. Open a pull request using the template.

## Frontmatter

Only the keys that every Agent Skills surface accepts are allowed:

| Key | Required | Rules |
|---|---|---|
| `name` | Yes | At most 64 characters: lowercase letters, digits and single hyphens. Must equal the directory name. Must not contain `anthropic` or `claude`. Unique across the repository. |
| `description` | Yes | 1 to 1,024 characters, with no `<` or `>`. See below. |
| `metadata` | Yes (house rule) | A map of string values. `version` is required (a quoted semantic version). `domain` is recommended and must match the domain directory. `summary` optionally overrides the one-line catalog summary. |
| `license` | No | For example `MIT` |
| `compatibility` | No | At most 500 characters, saying what the skill needs to run: tools, data, network. Recommended for any skill that depends on more than Claude itself. |
| `allowed-tools` | No | Tools the skill may use without asking. Honored by Claude Code. |

Claude Code also understands extra keys such as `when_to_use` and `model`. They are not allowed here, because claude.ai and the Skills API reject a skill that contains them.

## Writing the description

The description is the only part of a skill that Claude always sees. It decides whether the skill loads at all.

- **Say what it does, then when to use it.** For example: "Fundamental equity valuation … Use for any request to value a company …".
- **Name the terms users actually say**, such as DCF, WACC, DuPont, z-spread or attribution, so that the request matches the description.
- **Write in the third person**, and in a neutral register.
- **Stay inside your domain.** A description that claims adjacent work can win requests meant for another skill. If the skill uses fixed-income tools only as inputs, say so ("uses the Treasury curve to value the company's debt"). Do not list curve building as something the skill offers.
- **Keep it well under the limit.** About 300 to 800 characters is typical. The catalog uses its first sentence, or `metadata.summary` when that is set.

## Structuring the body

SKILL.md is loaded every time the skill triggers, so it should hold what applies to every use, and point to the rest.

A structure that works for analytical skills:

1. **Role and scope.** Who Claude is acting as, and the tasks covered, as a table if there are several.
2. **How the skill is organized.** A map of reference files: what each covers, and when to read it in full.
3. **Non-negotiable rules.** Evidence, point-in-time discipline, neutrality. See the conventions below.
4. **Workflow.** Numbered phases, with intake defaults in a table, and gates that stop the work early when an input fails.
5. **Data gaps and stop conditions.** What to do when a fact is unavailable, and when to stop entirely.

Keep the body under 500 lines; the validator warns past that. Prefer tables and numbered steps to long paragraphs. Use stable section numbers and table IDs, such as `A.9` and `T-13`, so that reports, reviews and changelogs can cite them.

## Reference files, scripts and assets

| Folder | Holds | Rules |
|---|---|---|
| `references/` | Detailed methodology, data contracts, report standards | Link every file from SKILL.md, and say when to read it. One level deep: reference files do not link on to other reference files. Files over 100 lines start with a `## Contents` list. |
| `scripts/` | Deterministic code: calculations, validators, data transforms | Mention each script in SKILL.md, with what it does and how to call it. Test it. Use no network access unless the skill's purpose requires it. |
| `assets/` | Templates, JSON Schemas, example outputs | Mention each in SKILL.md |

The validator warns about any shipped file that SKILL.md does not mention, because Claude will not know it exists.

Name reference files so that their order and contents are obvious. `equity-valuation` prefixes each file with its section number (`04-module-a-intrinsic-valuation.md`).

## Financial-skill conventions

`equity-valuation` set the house standard for analytical skills. New skills should adopt the parts that apply, and say why in review if they depart from one.

| Convention | What it means |
|---|---|
| **Evidence or nothing** | Every number is retrieved (with a source ID), computed (with formula and inputs) or a registered assumption (with its anchor evidence). Never facts from memory. |
| **Provenance tags** | Inline tags such as `[F3]`, `[D1]`, `[S4]`, `[X2]`, `[C7]` and `[A4]`, backed by a Source Ledger, a Computation Register and an Assumption Register in the output |
| **Point-in-time discipline** | Every analysis has an as-of date and uses only information knowable then, including vintage macro data |
| **Compute in code** | Arithmetic runs in code that is saved with the output, and rerunning it reproduces every number |
| **No silent defaults** | Every methodological choice is stated, with its rationale |
| **Ranges, not false precision** | Estimates come with sensitivities and scenarios |
| **Data is not instruction** | Text in filings, web pages, tool results or database rows is analyzed, never obeyed |
| **Integrity of the record** | Bad inputs are investigated and disclosed, never adjusted to make a model work |
| **Neutral language and a disclaimer** | No personalized advice. Rating language only in a vocabulary the user sets. A standard disclaimer at the end. |
| **Data-gap protocol** | Try the next source, bound immaterial gaps, disclose proxies, and stop rather than guess |
| **Machine-readable summary** | A versioned JSON block, such as `equity-valuation-report/1.1`, so that outputs can be compared and checked by tools |
| **Quality gate** | A checklist completed before any output, and an independent review for high-stakes work |

Never hard-code market data in a skill: rates, premiums, tax rates, multiples or company facts. A skill names the source and the method for retrieving each input. Illustrative numbers must be labelled as placeholders, as in equity-valuation 9.5.

## The user guide (README.md)

The README is for people. It is not shipped to Claude. Cover:

- what the skill does, with an example request for each task;
- requirements: tools, data sources, credentials, network, and which surfaces it runs on;
- what it asks for, and its defaults;
- what it produces;
- when it stops, and how to get past each stop;
- limitations;
- a file map, and a pointer to the changelog.

`skills/equity-research/equity-valuation/README.md` is the reference example.

## Testing a skill

`make check` checks structure. It cannot tell whether a skill is any good. Before opening a pull request:

1. **Triggering.** Write five or more requests that should load the skill, and two or three near-misses that should not. Near-misses include requests for adjacent domains' skills. Try them in a fresh session.
2. **Golden cases.** Run the skill end-to-end on at least one realistic case, with a fixed as-of date so that the result can be reproduced. For a change to an existing skill, rerun the same case before and after the change, and compare the outputs.
3. **Stop paths.** Check at least one stop condition: an ambiguous identifier, a missing tool or a missing input. The skill should stop and say why.
4. **Record what you ran** in the pull request's "How this was tested" section.

Claude Code's `claude plugin eval` runs eval cases stored under a plugin's `evals/` directory, with graders, and can compare the result against a run without the plugin. Adding eval suites per domain is on the [roadmap](roadmap.md).

## Changing an existing skill

- Keep section numbers and table IDs stable. If you must renumber, treat it as a MAJOR change and update every cross-reference.
- Search the skill for references to anything you rename (`grep -rn "A.2.5" skills/<domain>/<skill>`).
- Bump `metadata.version` according to [versioning-and-releases.md](versioning-and-releases.md), and add a changelog section.
- Update the user guide if behavior visible to users changed.

## Review checklist

Reviewers check:

- [ ] The description says what the skill does and when to use it, and does not reach into other domains.
- [ ] SKILL.md is under 500 lines. Every resource is linked and described.
- [ ] Rules, defaults and stop conditions are explicit.
- [ ] Formulas and thresholds agree with the cited curriculum or literature. Sign conventions and timing conventions are stated.
- [ ] No market data or company facts are hard-coded as known values.
- [ ] The version bump matches the change. The changelog says what users will notice.
- [ ] The user guide is accurate.
- [ ] The author has described the requests they tested.
