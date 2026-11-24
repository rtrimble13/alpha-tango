# Skills

Every skill in the repository, grouped by financial domain. Each domain directory is published as one Claude Code plugin of the same name.

<!-- skills-catalog:begin -->
| Skill | Domain | Version | What it does |
|---|---|---|---|
| [`equity-valuation`](equity-research/equity-valuation/README.md) | equity-research | 1.0.0 | Fundamental equity valuation and analysis to a CFA-charterholder standard. |
<!-- skills-catalog:end -->

## Domains

| Domain | Plugin | Scope |
|---|---|---|
| [equity-research](equity-research/README.md) | `equity-research` | Single-company equity analysis: valuation, financial-statement analysis, earnings quality, capital structure |

Planned domains are listed in the [roadmap](../docs/roadmap.md).

## Anatomy of a skill

```text
<skill-name>/
├── SKILL.md        Required. YAML frontmatter (name, description, metadata.version, ...) and the instructions
├── references/     Optional. Detailed material that SKILL.md links to and Claude reads on demand
├── scripts/        Optional. Code the skill runs (deterministic calculations, validators)
├── assets/         Optional. Templates, schemas and other files used in output
├── README.md       Required. The user guide; not shipped in release packages
└── CHANGELOG.md    Required. Version history; not shipped in release packages
```

To add a skill, run `make new DOMAIN=<domain> NAME=<skill-name>` and follow [docs/authoring-skills.md](../docs/authoring-skills.md).
