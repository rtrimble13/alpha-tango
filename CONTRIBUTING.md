# Contributing

Thank you for helping improve alpha-tango. This page covers the workflow. The details are in [docs/](docs/README.md).

## Ways to contribute

- **Report a problem with a skill.** Use the *Skill problem* issue form. Give the skill version, your request, and the part of the output that is wrong. Where you can, cite the section of the skill that was not followed (for example "A.2.5").
- **Propose a skill or a domain.** Use the *Skill proposal* issue form, so that scope and data sources are agreed before anyone writes the skill.
- **Change a skill or the tooling.** Open a pull request, as described below.

Never include credentials, API keys, licensed data you are not allowed to share, or confidential client information in issues, pull requests or skill files.

## Setup

```bash
git clone https://github.com/rtrimble13/alpha-tango.git
```

```bash
cd alpha-tango && make install
```

You need Python 3.10 or later, and Node.js for the Markdown linter. `make install` adds pre-commit and pre-push hooks that run the same checks as CI.

## Workflow

1. Create a branch from `main`.
2. Make the change:
   - new skill: `make new DOMAIN=<domain> NAME=<skill-name>`, then follow [docs/authoring-skills.md](docs/authoring-skills.md);
   - change to a skill: edit it, bump `metadata.version` in its SKILL.md according to [docs/versioning-and-releases.md](docs/versioning-and-releases.md), and add a section to its `CHANGELOG.md`;
   - tooling or docs: add a line to the root [CHANGELOG.md](CHANGELOG.md).
3. Run `make check`. Run `make catalog` if it reports catalog drift.
4. Try the skill on real requests, and note what you ran.
5. Open a pull request and fill in the template. CI must pass, and a code owner must approve.
6. After the merge, the release workflow publishes any new skill version. You don't need to tag anything.

## Standards for financial content

Skills here produce analysis that people may rely on, so changes to methodology get the same scrutiny as code:

- Ground every formula, threshold and default in a citable reference, such as the CFA curriculum, a standard text or a regulator's methodology, and name that reference in the pull request.
- State sign conventions, timing conventions (for example mid-year or end-of-year) and units explicitly.
- Never hard-code market data or company facts as known values. A skill names the source and the method for each input.
- Keep section numbers and table IDs stable, and update every cross-reference you touch.
- A change that moves outputs is MAJOR, even when it is a bug fix. Say in the changelog what users will see change.

## Commits

Write commit messages in the imperative ("Add sum-of-the-parts module"), and explain why in the body. Keep unrelated changes in separate commits, for example a formatting-only change apart from a methodology change, so that reviewers can tell them apart.

## AI-assisted contributions

Contributions written with AI assistance are welcome, and are held to the same standards. You are responsible for every line: read the diff, check formulas against the cited references, and run the tests.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
