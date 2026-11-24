# Getting started

This guide covers how to install alpha-tango skills, check that they loaded, use them and keep them up to date.

## Contents

- [Choose where to run a skill](#choose-where-to-run-a-skill)
- [Claude Code: install from the marketplace](#claude-code-install-from-the-marketplace)
- [Claude Code: install a single skill by hand](#claude-code-install-a-single-skill-by-hand)
- [claude.ai and the Claude API: upload a package](#claudeai-and-the-claude-api-upload-a-package)
- [Check that a skill loaded](#check-that-a-skill-loaded)
- [Use a skill](#use-a-skill)
- [Keep skills up to date](#keep-skills-up-to-date)
- [Troubleshooting](#troubleshooting)

## Choose where to run a skill

A skill is a folder holding a `SKILL.md` file and the reference material it points to. Several Claude surfaces can load one. Which surface suits a skill depends on what the skill needs at run time:

| Surface | How you install | Good for |
|---|---|---|
| **Claude Code** (CLI, desktop, IDE, web) | Plugin marketplace, or copy the folder into a skills directory | Skills that need local tools, MCP servers, files or a shell. That is most skills here, including `equity-valuation`. |
| **claude.ai** | Upload the release `.zip` | Skills that need only Claude and its built-in code execution |
| **Claude API** | Upload the release `.zip` through the Skills API | The same, inside your own application |

Each skill's guide (its `README.md`) lists its requirements under **Requirements**. Check that section first. For example, `equity-valuation` needs the fafnir warehouse and the dismal and fit command-line tools. Those exist only where you have installed them, which in practice means Claude Code on your machine or server.

## Claude Code: install from the marketplace

This repository is a Claude Code **plugin marketplace**. Each domain (for example `equity-research`) is one plugin. Installing a plugin installs every skill in that domain.

1. Add the marketplace (once per machine):

   ```bash
   claude plugin marketplace add rtrimble13/alpha-tango
   ```

2. Install the domain plugin you want:

   ```bash
   claude plugin install equity-research@alpha-tango
   ```

   This installs for your user account by default. To install for one project, and share the setting with everyone who works on it, add `--scope project`.

3. Start a new session, or run `/reload-plugins` in an open one.

You can do the same interactively with the `/plugin` command inside a session.

To list or inspect what is installed:

```bash
claude plugin list
```

```bash
claude plugin details equity-research@alpha-tango
```

## Claude Code: install a single skill by hand

To use one skill without the plugin, or to try a local change before you open a pull request, copy or link the skill folder into a skills directory:

| Scope | Location |
|---|---|
| Personal (all your projects) | `~/.claude/skills/<skill-name>/SKILL.md` |
| One project (commit it to share) | `.claude/skills/<skill-name>/SKILL.md` in that project |

For example, from a clone of this repository:

```bash
mkdir -p ~/.claude/skills && ln -s "$PWD/skills/equity-research/equity-valuation" ~/.claude/skills/equity-valuation
```

A symbolic link means edits in your clone take effect straight away. Run `/reload-skills` in an open session to pick them up. A skill installed this way is called by its plain name (`/equity-valuation`). A plugin skill is called with the plugin name in front (`/equity-research:equity-valuation`).

## claude.ai and the Claude API: upload a package

Every release on the [Releases page](https://github.com/rtrimble13/alpha-tango/releases) carries a `<skill>-<version>.zip` file and its `.sha256` checksum. The zip holds one folder, named after the skill, with `SKILL.md` and its resources. The user guide and changelog are left out.

1. Download the zip and its checksum, then verify the zip:

   ```bash
   sha256sum -c equity-valuation-1.0.0.zip.sha256
   ```

2. **claude.ai:** open Settings and find the Skills section (under Capabilities at the time of writing), then upload the zip. Code execution must be enabled. On Team and Enterprise plans an administrator may need to allow skills first.
3. **Claude API:** upload the zip with the Skills API, then attach the skill to requests that use the code-execution tool. Anthropic's [Skills guide](https://docs.claude.com/en/api/skills-guide) documents the current endpoints and headers.

You can also build the same zip yourself from a clone: `make package` writes it to `dist/`.

## Check that a skill loaded

- In Claude Code, type `/` and look for the skill's name in the menu. Or ask "What skills do you have available?"
- Then try a request from the skill's guide. A skill loads when the request matches its description, so phrase the request the way the guide's examples do.

## Use a skill

Ask for the work in plain language. Claude reads the skill's short description up front, and loads the full instructions only when a request needs them. You can also call a skill by name to force it.

For example, with `equity-valuation`:

```text
Value MSFT as of today.
Quick look at KO against its peers.
/equity-research:equity-valuation Decompose Costco's ROE over the last five years.
```

The skill's guide explains what it asks for, the defaults it applies, what it produces and when it stops: [equity-valuation guide](../skills/equity-research/equity-valuation/README.md).

## Keep skills up to date

- **Plugin installs:** the marketplace entries carry no `version` field, so Claude Code tracks the repository's commits. Update with:

  ```bash
  claude plugin marketplace update alpha-tango
  ```

  ```bash
  claude plugin update equity-research@alpha-tango
  ```

  Automatic updates for third-party marketplaces are off by default. You can turn them on from the `/plugin` panel.
- **Manual installs:** pull your clone. A symbolic link picks up the change at once; a copy has to be copied again.
- **Uploaded packages:** download the new release and upload it again.

Each skill's `CHANGELOG.md` says what changed in each version. [Versioning and releases](versioning-and-releases.md) explains what a MAJOR, MINOR or PATCH change means for a skill.

## Troubleshooting

| Symptom | Likely cause | What to do |
|---|---|---|
| The skill doesn't appear | Plugin not installed or not reloaded | `claude plugin list`; `/reload-plugins` or a new session |
| The skill appears but doesn't trigger | The request doesn't match its description | Call it by name, or rephrase the request like the guide's examples |
| Upload to claude.ai is rejected | The zip was re-packed with the folder nested one level too deep, or the frontmatter was edited | Upload the release zip unchanged, or rebuild it with `make package` |
| The skill stops early, saying data is missing | A required tool or source is not available in this environment | Check the skill's **Requirements**, and its **When the skill stops** table |
| A new marketplace version doesn't arrive | Automatic updates are off | Run the two update commands above |
