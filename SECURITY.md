# Security

Skills are instructions that an AI agent follows, often with a shell, files, network access and data credentials. A flaw in a skill can therefore have real effects, even though the skill contains little or no code.

## Reporting a vulnerability

Report security problems privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability**. Do not open a public issue.

Include the affected skill and version (or file), what an attacker could cause, and the steps to reproduce. You should receive an acknowledgement within a few days.

## What counts as a security problem

- **Instruction injection.** A skill that would follow instructions found in data, such as filings, web pages, tool output or database rows. Skills here treat such text as content, never as commands (equity-valuation prime directive 8). A way around that rule is a vulnerability.
- **Unsafe actions.** A skill that tells the agent to run destructive commands, send data to unexpected destinations, or ask for secrets in chat.
- **Credential exposure.** Secrets, tokens or private data committed to the repository or included in release packages.
- **Supply chain.** A compromised or unpinned dependency in CI or the release workflow, or a release asset that does not match what the workflow built.

A skill producing a wrong financial number is a quality problem, not a security one. Report it with the *Skill problem* issue form.

## How the repository protects itself

- GitHub Actions are pinned to full commit SHAs, and Dependabot proposes updates. Workflows default to read-only permissions; only the release job can write.
- Release zips are built deterministically, and each one is published with a SHA-256 checksum.
- Skills are plain text. Review a skill, and any script it ships, before installing it. This applies to any third-party skill, not only these.
