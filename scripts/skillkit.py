#!/usr/bin/env python3
"""skillkit: maintenance tool for the alpha-tango skills repository.

Subcommands:
  validate        check every skill, the plugin marketplace, links and the catalog
  catalog         regenerate the skill catalog tables and sync marketplace.json
  check-versions  require a version bump and changelog entry for each changed skill
  package         build an uploadable .zip for each skill (default: dist/)
  release         publish a GitHub release for each skill version not yet tagged
  notes           print the changelog section for a skill version
  new             scaffold a new skill from templates/
  list            list the skills

Run `python scripts/skillkit.py <subcommand> --help` for options. The only
third-party dependency is PyYAML. Repository conventions are documented in
docs/tooling.md and docs/versioning-and-releases.md.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import functools
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import urllib.parse
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only without dev deps
    sys.exit("skillkit needs PyYAML: pip install -r requirements-dev.txt")

DEFAULT_ROOT = Path(__file__).resolve().parent.parent

# Frontmatter keys accepted by every Agent Skills surface (claude.ai upload, the
# Skills API and Claude Code). Claude Code-only keys are rejected on upload, so
# skills in this repository are limited to the portable set.
PORTABLE_KEYS = frozenset({"name", "description", "license", "compatibility", "metadata", "allowed-tools"})
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESERVED_WORDS = ("anthropic", "claude")
MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_COMPATIBILITY = 500
MAX_BODY_LINES = 500
TOC_MIN_LINES = 100
INITIAL_VERSION = "0.1.0"

# Human-facing files kept beside SKILL.md but left out of release packages.
HUMAN_FILES = frozenset({"README.md", "CHANGELOG.md"})
IGNORED_NAMES = frozenset({"__pycache__", ".DS_Store", "Thumbs.db"})
IGNORED_SUFFIXES = frozenset({".pyc", ".pyo"})

MARKETPLACE = ".claude-plugin/marketplace.json"
CATALOG_FILES = ("README.md", "skills/README.md")
CATALOG_BEGIN = "<!-- skills-catalog:begin -->"
CATALOG_END = "<!-- skills-catalog:end -->"

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
CHANGELOG_HEADING_RE = re.compile(
    r"^## \[(?P<version>[^\]]+)\](?:[ \t]+-[ \t]+(?P<date>\d{4}-\d{2}-\d{2}))?[ \t]*$",
    re.MULTILINE,
)
CONTENTS_HEADING_RE = re.compile(r"^#{2,4} (contents|table of contents)\s*$", re.I | re.M)
LINK_RE = re.compile(r"\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
REF_DEF_RE = re.compile(r"^ {0,3}\[[^\]]+\]:\s*<?([^\s>]+)>?")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


# --------------------------------------------------------------------------- #
# Versions
# --------------------------------------------------------------------------- #


@functools.total_ordering
@dataclass(frozen=True)
class Version:
    """A Semantic Versioning 2.0.0 version (build metadata is ignored)."""

    major: int
    minor: int
    patch: int
    pre: tuple = ()

    @classmethod
    def parse(cls, text: str) -> Version:
        match = SEMVER_RE.match(text or "")
        if not match:
            raise ValueError(f"not a semantic version (MAJOR.MINOR.PATCH): {text!r}")
        pre = ()
        if match.group(4):
            pre = tuple(int(p) if p.isdigit() else p for p in match.group(4).split("."))
        return cls(int(match.group(1)), int(match.group(2)), int(match.group(3)), pre)

    @property
    def is_prerelease(self) -> bool:
        return bool(self.pre)

    def _key(self) -> tuple:
        # A release sorts above its pre-releases; numeric identifiers sort below
        # alphanumeric ones; a longer identifier list wins when the prefix ties.
        pre = tuple((0, p, "") if isinstance(p, int) else (1, 0, p) for p in self.pre)
        return (self.major, self.minor, self.patch, 0 if self.pre else 1, pre)

    def __lt__(self, other: Version) -> bool:
        return self._key() < other._key()

    def __str__(self) -> str:
        text = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre:
            text += "-" + ".".join(str(p) for p in self.pre)
        return text


# --------------------------------------------------------------------------- #
# Findings
# --------------------------------------------------------------------------- #


@dataclass
class Finding:
    level: str  # "error" or "warning"
    path: str
    message: str
    line: int | None = None


@dataclass
class Findings:
    items: list[Finding] = field(default_factory=list)

    def error(self, path: str, message: str, line: int | None = None) -> None:
        self.items.append(Finding("error", path, message, line))

    def warning(self, path: str, message: str, line: int | None = None) -> None:
        self.items.append(Finding("warning", path, message, line))

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.items if f.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.items if f.level == "warning"]

    def emit(self, stream=None) -> None:
        stream = stream or sys.stdout
        github = os.environ.get("GITHUB_ACTIONS") == "true"
        for f in sorted(self.items, key=lambda f: (f.level != "error", f.path, f.line or 0)):
            if github:
                loc = f"file={f.path}" + (f",line={f.line}" if f.line else "")
                print(f"::{f.level} {loc}::{f.message}", file=stream)
            else:
                loc = f.path + (f":{f.line}" if f.line else "")
                print(f"{f.level.upper():<7} {loc}: {f.message}", file=stream)


# --------------------------------------------------------------------------- #
# Skills
# --------------------------------------------------------------------------- #


@dataclass
class Skill:
    root: Path
    path: Path
    frontmatter: dict
    body: str
    body_line: int
    parsed: bool = True

    @property
    def rel(self) -> str:
        return self.path.relative_to(self.root).as_posix()

    @property
    def domain(self) -> str:
        return self.path.parent.name

    @property
    def dir_name(self) -> str:
        return self.path.name

    @property
    def name(self) -> str:
        name = self.frontmatter.get("name")
        return name if isinstance(name, str) and name else self.dir_name

    @property
    def description(self) -> str:
        desc = self.frontmatter.get("description")
        return desc if isinstance(desc, str) else ""

    @property
    def metadata(self) -> dict:
        meta = self.frontmatter.get("metadata")
        return meta if isinstance(meta, dict) else {}

    @property
    def version(self) -> str | None:
        version = self.metadata.get("version")
        return version if isinstance(version, str) else None

    @property
    def summary(self) -> str:
        summary = self.metadata.get("summary")
        if isinstance(summary, str) and summary.strip():
            return summary.strip()
        return first_sentence(self.description.strip())

    @property
    def tag(self) -> str:
        return f"{self.name}-v{self.version}"

    @property
    def skill_md(self) -> Path:
        return self.path / "SKILL.md"


ABBREVIATIONS = frozenset(
    {"e.g", "i.e", "vs", "etc", "inc", "corp", "co", "ltd", "no", "approx", "fig", "al"}
)


def first_sentence(text: str) -> str:
    """The first sentence of a description, not fooled by "U.S." or "e.g."."""
    for match in re.finditer(r"[.!?](?=\s+[A-Z0-9(\"'])", text):
        word = text[: match.start()].split()[-1].lower() if text[: match.start()].split() else ""
        if word in ABBREVIATIONS or re.fullmatch(r"(?:[a-z]\.)*[a-z]", word):
            continue
        return text[: match.end()]
    return text


def split_frontmatter(text: str) -> tuple[dict, str, int]:
    """Return (frontmatter, body, first body line number) for a SKILL.md text."""
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with a YAML frontmatter block opened by '---'")
    end = text.find("\n---\n", 3)
    if end == -1:
        if text.rstrip("\n").endswith("\n---"):
            end = text.rstrip("\n").rfind("\n---")
        else:
            raise ValueError("the frontmatter block is not closed by a '---' line")
    raw = text[4:end]
    body = text[end + 5 :]
    data = yaml.safe_load(raw) if raw.strip() else {}
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("the frontmatter must be a YAML mapping")
    return data, body, raw.count("\n") + 3


def rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def discover(root: Path, findings: Findings | None = None) -> list[Skill]:
    findings = findings if findings is not None else Findings()
    skills_dir = root / "skills"
    skills: list[Skill] = []
    if not skills_dir.is_dir():
        return skills
    for md in sorted(skills_dir.rglob("SKILL.md")):
        parts = md.relative_to(skills_dir).parts
        if len(parts) != 3:
            findings.error(rel(root, md), "SKILL.md must be at skills/<domain>/<skill>/SKILL.md")
            continue
        try:
            fm, body, line = split_frontmatter(md.read_text(encoding="utf-8"))
            skills.append(Skill(root, md.parent, fm, body, line))
        except (ValueError, yaml.YAMLError) as exc:
            findings.error(rel(root, md), f"invalid frontmatter: {exc}", 1)
            skills.append(Skill(root, md.parent, {}, "", 1, parsed=False))
    return skills


def packaged_files(skill: Skill) -> list[Path]:
    """Files shipped in a skill's release package (SKILL.md and its resources)."""
    files = []
    for path in sorted(skill.path.rglob("*")):
        if not path.is_file():
            continue
        parts = path.relative_to(skill.path).parts
        if any(p.startswith(".") or p in IGNORED_NAMES for p in parts):
            continue
        if path.suffix in IGNORED_SUFFIXES:
            continue
        if len(parts) == 1 and parts[0] in HUMAN_FILES:
            continue
        files.append(path)
    return files


# --------------------------------------------------------------------------- #
# Changelogs
# --------------------------------------------------------------------------- #


def changelog_headings(text: str) -> list[tuple[str, str | None, int]]:
    return [
        (m.group("version"), m.group("date"), text.count("\n", 0, m.start()) + 1)
        for m in CHANGELOG_HEADING_RE.finditer(text)
    ]


def changelog_section(text: str, version: str) -> str | None:
    """The body of the `## [version]` section, without trailing link definitions."""
    headings = list(CHANGELOG_HEADING_RE.finditer(text))
    for i, match in enumerate(headings):
        if match.group("version") != version:
            continue
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        lines = text[match.end() : end].strip("\n").split("\n")
        while lines and (not lines[-1].strip() or REF_DEF_RE.match(lines[-1])):
            lines.pop()
        return "\n".join(lines).strip()
    return None


def check_changelog(skill: Skill, findings: Findings) -> None:
    path = skill.path / "CHANGELOG.md"
    where = rel(skill.root, path)
    if not path.is_file():
        findings.error(rel(skill.root, skill.path), "missing CHANGELOG.md")
        return
    text = path.read_text(encoding="utf-8")
    seen_release = False
    released: list[tuple[Version, int]] = []
    for version, date, line in changelog_headings(text):
        if version.lower() == "unreleased":
            if seen_release:
                findings.error(where, "[Unreleased] must come before every version section", line)
            continue
        seen_release = True
        try:
            parsed = Version.parse(version)
        except ValueError as exc:
            findings.error(where, str(exc), line)
            continue
        if not date:
            findings.error(where, f"section [{version}] needs a date: '## [{version}] - YYYY-MM-DD'", line)
        released.append((parsed, line))
    for (newer, _), (older, line) in zip(released, released[1:], strict=False):
        if not older < newer:
            findings.error(where, f"versions must be listed newest first ({older} after {newer})", line)
    if not released:
        findings.error(where, "no version sections; add '## [x.y.z] - YYYY-MM-DD'")
        return
    if skill.version and SEMVER_RE.match(skill.version):
        latest = released[0][0]
        if latest != Version.parse(skill.version):
            findings.error(
                where,
                f"latest section is [{latest}] but SKILL.md metadata.version is {skill.version}; "
                f"add '## [{skill.version}] - YYYY-MM-DD' describing the change",
                released[0][1],
            )


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #


def check_frontmatter(skill: Skill, findings: Findings) -> None:
    fm = skill.frontmatter
    where = rel(skill.root, skill.skill_md)

    unknown = sorted(set(fm) - PORTABLE_KEYS)
    if unknown:
        findings.error(
            where,
            f"frontmatter key(s) {', '.join(unknown)} are not portable; allowed: "
            f"{', '.join(sorted(PORTABLE_KEYS))} (claude.ai and the Skills API reject others)",
            1,
        )

    name = fm.get("name")
    if not isinstance(name, str) or not name:
        findings.error(where, "frontmatter needs a 'name' string", 1)
    else:
        if len(name) > MAX_NAME:
            findings.error(where, f"name is {len(name)} characters; the limit is {MAX_NAME}", 1)
        if not NAME_RE.match(name):
            findings.error(where, f"name {name!r} must be lowercase letters, digits and single hyphens", 1)
        for word in RESERVED_WORDS:
            if word in name:
                findings.error(where, f"name {name!r} contains the reserved word {word!r}", 1)
        if name != skill.dir_name:
            findings.error(where, f"name {name!r} must match its directory name {skill.dir_name!r}", 1)

    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        findings.error(where, "frontmatter needs a non-empty 'description' string", 1)
    else:
        if len(desc) > MAX_DESCRIPTION:
            findings.error(where, f"description is {len(desc)} characters; the limit is {MAX_DESCRIPTION}", 1)
        if "<" in desc or ">" in desc:
            findings.error(where, "description must not contain angle brackets (< or >)", 1)
        if not re.search(r"\b(use|when)\b", desc, re.I):
            findings.warning(where, "description should say when to use the skill ('Use for/when ...')", 1)

    if "license" in fm and not isinstance(fm["license"], str):
        findings.error(where, "license must be a string", 1)

    compat = fm.get("compatibility")
    if compat is not None:
        if not isinstance(compat, str):
            findings.error(where, "compatibility must be a string", 1)
        elif len(compat) > MAX_COMPATIBILITY:
            findings.error(
                where, f"compatibility is {len(compat)} characters; the limit is {MAX_COMPATIBILITY}", 1
            )

    tools = fm.get("allowed-tools")
    if tools is not None and not (
        isinstance(tools, str) or (isinstance(tools, list) and all(isinstance(t, str) for t in tools))
    ):
        findings.error(where, "allowed-tools must be a string or a list of strings", 1)

    meta = fm.get("metadata")
    if not isinstance(meta, dict):
        findings.error(where, "frontmatter needs a 'metadata' mapping with at least 'version'", 1)
        return
    for key, value in meta.items():
        if not isinstance(key, str) or not isinstance(value, str):
            findings.error(
                where,
                f'metadata.{key} must be a string (quote it, for example version: "1.0.0")',
                1,
            )
    version = meta.get("version")
    if isinstance(version, str):
        try:
            Version.parse(version)
        except ValueError as exc:
            findings.error(where, f"metadata.version: {exc}", 1)
    elif version is None:
        findings.error(where, "metadata.version is required (semantic version string)", 1)
    domain = meta.get("domain")
    if isinstance(domain, str) and domain != skill.domain:
        findings.error(
            where, f"metadata.domain {domain!r} must match its domain directory {skill.domain!r}", 1
        )


def check_body(skill: Skill, findings: Findings) -> None:
    where = rel(skill.root, skill.skill_md)
    if not skill.body.strip():
        findings.error(where, "SKILL.md has no instructions after the frontmatter")
        return
    lines = skill.body.strip("\n").count("\n") + 1
    if lines > MAX_BODY_LINES:
        findings.warning(
            where,
            f"SKILL.md body is {lines} lines; keep it under {MAX_BODY_LINES} and move detail to references/",
            skill.body_line,
        )
    text = skill.skill_md.read_text(encoding="utf-8")
    for i, line in enumerate(text.split("\n"), 1):
        if re.search(r"\bTODO\b", line):
            findings.warning(where, "unfinished TODO left in SKILL.md", i)


def check_resources(skill: Skill, findings: Findings) -> None:
    skill_text = skill.skill_md.read_text(encoding="utf-8")
    if not (skill.path / "README.md").is_file():
        findings.error(rel(skill.root, skill.path), "missing README.md (the user guide for people)")
    for path in packaged_files(skill):
        if path == skill.skill_md:
            continue
        relpath = path.relative_to(skill.path).as_posix()
        where = rel(skill.root, path)
        if relpath not in skill_text:
            findings.warning(where, "not referenced from SKILL.md, so Claude will not know it exists")
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        if text.count("\n") > TOC_MIN_LINES and not CONTENTS_HEADING_RE.search(text):
            findings.warning(where, f"over {TOC_MIN_LINES} lines; add a '## Contents' list at the top")
        for target, line in iter_links(text):
            resolved = resolve_link(path, target, skill.root)
            if resolved is None or resolved == skill.skill_md:
                continue
            try:
                resolved.relative_to(skill.path)
            except ValueError:
                continue
            findings.warning(
                where,
                f"links to {target}; keep references one level deep (link files from SKILL.md only)",
                line,
            )


def strip_code(text: str) -> list[str]:
    """Lines of a markdown text with fenced blocks and inline code blanked out."""
    out, fence = [], None
    for line in text.split("\n"):
        stripped = line.lstrip()
        marker = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence:
            if marker and stripped.startswith(fence):
                fence = None
            out.append("")
            continue
        if marker:
            fence = marker.group(1)
            out.append("")
            continue
        out.append(re.sub(r"`+[^`]*`+", "", line))
    return out


def iter_links(text: str):
    for number, line in enumerate(strip_code(text), 1):
        for match in LINK_RE.finditer(line):
            yield match.group(1), number
        ref = REF_DEF_RE.match(line)
        if ref:
            yield ref.group(1), number


def resolve_link(source: Path, target: str, root: Path) -> Path | None:
    """The local file a relative link points at, or None for URLs and anchors."""
    if SCHEME_RE.match(target) or target.startswith("#"):
        return None
    target = urllib.parse.unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not target:
        return None
    if target.startswith("/"):
        return (root / target.lstrip("/")).resolve()
    return (source.parent / target).resolve()


def markdown_files(root: Path) -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.md"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split("\n")
        files = [root / f for f in out if f]
    except (OSError, subprocess.CalledProcessError):
        files = [
            p
            for p in root.rglob("*.md")
            if not any(part in {".git", "node_modules", "dist"} for part in p.relative_to(root).parts)
        ]
    return sorted(p for p in files if p.is_file())


def check_links(root: Path, findings: Findings) -> None:
    for md in markdown_files(root):
        text = md.read_text(encoding="utf-8")
        for target, line in iter_links(text):
            if "\\" in target:
                findings.error(rel(root, md), f"link {target!r} uses backslashes; use forward slashes", line)
                continue
            resolved = resolve_link(md, target, root)
            if resolved is not None and not resolved.exists():
                findings.error(rel(root, md), f"broken link: {target}", line)


def check_domains(root: Path, skills: list[Skill], findings: Findings) -> None:
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        findings.error("skills", "the skills/ directory is missing")
        return
    for domain in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        where = rel(root, domain)
        if not NAME_RE.match(domain.name):
            findings.error(
                where, "domain directory names must be lowercase letters, digits and single hyphens"
            )
        if not (domain / "README.md").is_file():
            findings.error(where, "each domain needs a README.md describing its scope")
    seen: dict[str, Skill] = {}
    for skill in skills:
        other = seen.get(skill.name)
        if other:
            findings.error(
                rel(root, skill.skill_md), f"skill name {skill.name!r} is also used by {other.rel}"
            )
        seen[skill.name] = skill


def validate(root: Path, check_catalog: bool = True) -> tuple[list[Skill], Findings]:
    findings = Findings()
    skills = discover(root, findings)
    check_domains(root, skills, findings)
    for skill in skills:
        if skill.parsed:
            check_frontmatter(skill, findings)
            check_body(skill, findings)
        check_resources(skill, findings)
        check_changelog(skill, findings)
    check_marketplace(root, skills, findings)
    check_links(root, findings)
    if check_catalog:
        for problem in catalog_drift(root, skills):
            findings.error(problem, "out of date; run `make catalog` (python scripts/skillkit.py catalog)")
    return skills, findings


# --------------------------------------------------------------------------- #
# Marketplace and catalog
# --------------------------------------------------------------------------- #


def skill_source_path(skill: Skill) -> str:
    return f"./skills/{skill.domain}/{skill.dir_name}"


def load_marketplace(root: Path) -> dict:
    return json.loads((root / MARKETPLACE).read_text(encoding="utf-8"))


def check_marketplace(root: Path, skills: list[Skill], findings: Findings) -> None:
    path = root / MARKETPLACE
    if not path.is_file():
        findings.error(MARKETPLACE, "missing plugin marketplace manifest")
        return
    try:
        data = load_marketplace(root)
    except json.JSONDecodeError as exc:
        findings.error(MARKETPLACE, f"invalid JSON: {exc}", exc.lineno)
        return
    for key in ("name", "owner", "plugins"):
        if key not in data:
            findings.error(MARKETPLACE, f"missing required key {key!r}")
    plugins = data.get("plugins") or []
    if not isinstance(plugins, list):
        findings.error(MARKETPLACE, "'plugins' must be a list")
        return
    owners: dict[str, list[str]] = {}
    names = set()
    for plugin in plugins:
        pname = plugin.get("name", "?")
        if pname in names:
            findings.error(MARKETPLACE, f"plugin name {pname!r} is used twice")
        names.add(pname)
        if "version" in plugin:
            findings.warning(
                MARKETPLACE,
                f"plugin {pname!r} sets 'version', which pins users until it changes; "
                "skill versions live in SKILL.md (see docs/versioning-and-releases.md)",
            )
        source = plugin.get("source")
        if not isinstance(source, str) or not source.startswith("./"):
            findings.error(MARKETPLACE, f"plugin {pname!r} needs a relative 'source' starting with './'")
            continue
        base = (root / source).resolve()
        for entry in plugin.get("skills") or []:
            if not isinstance(entry, str) or not entry.startswith("./"):
                findings.error(MARKETPLACE, f"plugin {pname!r}: skill path {entry!r} must start with './'")
                continue
            if not (base / entry / "SKILL.md").is_file():
                findings.error(MARKETPLACE, f"plugin {pname!r}: {entry} has no SKILL.md")
                continue
            owners.setdefault((base / entry).resolve().as_posix(), []).append(pname)
    for skill in skills:
        listed = owners.get(skill.path.resolve().as_posix(), [])
        if not listed:
            findings.error(MARKETPLACE, f"skill {skill.rel} is not in any plugin; run `make catalog`")
        elif len(listed) > 1:
            findings.error(MARKETPLACE, f"skill {skill.rel} is in several plugins: {', '.join(listed)}")
        elif listed[0] != skill.domain:
            findings.error(
                MARKETPLACE,
                f"skill {skill.rel} belongs in plugin {skill.domain!r}, not {listed[0]!r}",
            )


def domain_summary(root: Path, domain: str) -> str:
    readme = root / "skills" / domain / "README.md"
    if readme.is_file():
        for block in readme.read_text(encoding="utf-8").split("\n\n"):
            block = block.strip()
            if block and not block.startswith(("#", "<!--", "|", "-", ">")):
                return " ".join(block.split())
    return f"Skills for {domain.replace('-', ' ')}."


def synced_marketplace(root: Path, skills: list[Skill], current: dict) -> dict:
    data = copy.deepcopy(current)
    plugins = data.setdefault("plugins", [])
    by_name = {p.get("name"): p for p in plugins}
    for domain in sorted({s.domain for s in skills}):
        paths = sorted(skill_source_path(s) for s in skills if s.domain == domain)
        plugin = by_name.get(domain)
        if plugin is None:
            plugin = {
                "name": domain,
                "description": domain_summary(root, domain),
                "source": "./",
                "strict": False,
                "skills": paths,
            }
            plugins.append(plugin)
            by_name[domain] = plugin
        elif plugin.get("source") == "./":
            plugin["skills"] = paths
    return data


def render_catalog(skills: list[Skill], catalog: Path) -> str:
    rows = ["| Skill | Domain | Version | What it does |", "|---|---|---|---|"]
    for skill in sorted(skills, key=lambda s: (s.domain, s.name)):
        guide = Path(os.path.relpath(skill.path / "README.md", catalog.parent)).as_posix()
        summary = skill.summary.replace("|", "\\|")
        rows.append(f"| [`{skill.name}`]({guide}) | {skill.domain} | {skill.version or 'n.a.'} | {summary} |")
    if not skills:
        rows.append("| _No skills yet_ | | | |")
    return "\n".join(rows)


def replace_catalog(text: str, table: str) -> str | None:
    start, end = text.find(CATALOG_BEGIN), text.find(CATALOG_END)
    if start == -1 or end == -1 or end < start:
        return None
    return text[: start + len(CATALOG_BEGIN)] + "\n" + table + "\n" + text[end:]


def catalog_updates(root: Path, skills: list[Skill]) -> dict[str, str]:
    """Map of repo-relative path -> desired content, for every generated file."""
    wanted: dict[str, str] = {}
    for name in CATALOG_FILES:
        path = root / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        updated = replace_catalog(text, render_catalog(skills, path))
        if updated is not None:
            wanted[name] = updated
    if (root / MARKETPLACE).is_file():
        try:
            current = load_marketplace(root)
        except json.JSONDecodeError:
            current = None
        if current is not None:
            wanted[MARKETPLACE] = json.dumps(synced_marketplace(root, skills, current), indent=2) + "\n"
    return wanted


def catalog_drift(root: Path, skills: list[Skill]) -> list[str]:
    drift = []
    for name in CATALOG_FILES:
        path = root / name
        if path.is_file() and replace_catalog(path.read_text(encoding="utf-8"), "") is None:
            drift.append(name + f" (missing {CATALOG_BEGIN} / {CATALOG_END} markers)")
    for name, content in catalog_updates(root, skills).items():
        if (root / name).read_text(encoding="utf-8") != content:
            drift.append(name)
    return drift


# --------------------------------------------------------------------------- #
# Git helpers
# --------------------------------------------------------------------------- #


class GitError(RuntimeError):
    pass


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {result.stderr.strip() or 'failed'}")
    return result.stdout


def changed_files(root: Path, base: str) -> tuple[str, list[str]]:
    merge_base = git(root, "merge-base", base, "HEAD").strip()
    tracked = git(root, "diff", "--name-only", merge_base).split("\n")
    untracked = git(root, "ls-files", "--others", "--exclude-standard").split("\n")
    return merge_base, sorted({f for f in tracked + untracked if f})


def check_versions(root: Path, base: str) -> tuple[list[str], Findings]:
    findings = Findings()
    skills = discover(root, findings)
    merge_base, changed = changed_files(root, base)
    report: list[str] = []
    for skill in skills:
        prefix = skill.rel + "/"
        shipped = [f for f in changed if f.startswith(prefix) and f[len(prefix) :] not in HUMAN_FILES]
        if not shipped:
            continue
        where = rel(root, skill.skill_md)
        try:
            head = Version.parse(skill.version or "")
        except ValueError as exc:
            findings.error(where, f"metadata.version: {exc}")
            continue
        try:
            base_fm, _, _ = split_frontmatter(git(root, "show", f"{merge_base}:{skill.rel}/SKILL.md"))
        except GitError:
            report.append(f"{skill.name}: new skill at {head}")
        except (ValueError, yaml.YAMLError):
            findings.warning(where, "could not read the base version; skipping the bump check")
        else:
            base_version = (base_fm.get("metadata") or {}).get("version")
            try:
                previous = Version.parse(str(base_version))
            except ValueError:
                findings.warning(
                    where, f"base version {base_version!r} is not semver; skipping the bump check"
                )
            else:
                if head > previous:
                    report.append(f"{skill.name}: {previous} -> {head}")
                else:
                    findings.error(
                        where,
                        f"{len(shipped)} shipped file(s) changed but metadata.version is still {head} "
                        f"(base {previous}); bump it per docs/versioning-and-releases.md",
                        1,
                    )
                    report.append(f"{skill.name}: {previous} -> {head} (needs a bump)")
        log = skill.path / "CHANGELOG.md"
        if not log.is_file() or changelog_section(log.read_text(encoding="utf-8"), str(head)) is None:
            findings.error(rel(root, log), f"add a '## [{head}] - YYYY-MM-DD' section for this change")
    current = {s.rel for s in skills}
    listing = git(root, "ls-tree", "-r", "--name-only", merge_base, "--", "skills").split("\n")
    for path in listing:
        parts = path.split("/")
        if len(parts) == 4 and parts[-1] == "SKILL.md" and "/".join(parts[:3]) not in current:
            findings.warning(path, "skill removed; its released tags and downloads remain available")
            report.append(f"{parts[2]}: removed")
    return report, findings


# --------------------------------------------------------------------------- #
# Packaging and releases
# --------------------------------------------------------------------------- #


def package_skill(skill: Skill, out_dir: Path) -> Path:
    """Write a deterministic <name>-<version>.zip (plus .sha256) for upload."""
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"{skill.name}-{skill.version}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in packaged_files(skill):
            arcname = f"{skill.name}/{path.relative_to(skill.path).as_posix()}"
            info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if os.access(path, os.X_OK) else 0o644
            info.external_attr = (0o100000 | mode) << 16
            zf.writestr(info, path.read_bytes())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (out_dir / f"{archive.name}.sha256").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return archive


def pending_releases(root: Path, skills: list[Skill]) -> list[Skill]:
    tags = set(git(root, "tag", "--list").split())
    return [s for s in skills if s.version and s.tag not in tags]


# --------------------------------------------------------------------------- #
# Scaffolding
# --------------------------------------------------------------------------- #


def render_template(path: Path, values: dict[str, str]) -> str:
    text = path.read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    leftover = re.findall(r"\{\{[a-z_]+\}\}", text)
    if leftover:
        raise ValueError(f"{path}: unknown placeholder(s) {', '.join(sorted(set(leftover)))}")
    return text


def scaffold(root: Path, domain: str, name: str, description: str | None) -> list[Path]:
    for label, value in (("domain", domain), ("skill name", name)):
        if not NAME_RE.match(value) or len(value) > MAX_NAME:
            raise ValueError(f"{label} {value!r} must be lowercase letters, digits and single hyphens")
    for word in RESERVED_WORDS:
        if word in name:
            raise ValueError(f"skill name {name!r} contains the reserved word {word!r}")
    if any(s.name == name for s in discover(root)):
        raise ValueError(f"a skill named {name!r} already exists")
    if description and ("<" in description or ">" in description or len(description) > MAX_DESCRIPTION):
        raise ValueError("description must be at most 1024 characters with no angle brackets")
    templates = root / "templates"
    skill_dir = root / "skills" / domain / name
    values = {
        "name": name,
        "domain": domain,
        "title": name.replace("-", " ").title(),
        "domain_title": domain.replace("-", " ").capitalize(),
        "domain_words": domain.replace("-", " "),
        "description": json.dumps(
            description or "TODO: say what the skill does, then 'Use when ...' with the requests it covers."
        ),
        "version": INITIAL_VERSION,
        "date": dt.date.today().isoformat(),
    }
    created = []
    domain_readme = root / "skills" / domain / "README.md"
    if not domain_readme.exists():
        domain_readme.parent.mkdir(parents=True, exist_ok=True)
        domain_readme.write_text(
            render_template(templates / "domain" / "README.md.tmpl", values), encoding="utf-8"
        )
        created.append(domain_readme)
    skill_dir.mkdir(parents=True)
    for template in sorted((templates / "skill").glob("*.tmpl")):
        target = skill_dir / template.name[: -len(".tmpl")]
        target.write_text(render_template(template, values), encoding="utf-8")
        created.append(target)
    return created


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #


def cmd_validate(args) -> int:
    skills, findings = validate(args.root)
    findings.emit()
    print(
        f"{len(skills)} skill(s) checked: {len(findings.errors)} error(s), "
        f"{len(findings.warnings)} warning(s)"
    )
    if findings.errors or (args.strict and findings.warnings):
        return 1
    return 0


def cmd_catalog(args) -> int:
    findings = Findings()
    skills = discover(args.root, findings)
    if args.check:
        drift = catalog_drift(args.root, skills)
        for name in drift:
            findings.error(name, "out of date; run `make catalog`")
        findings.emit()
        if not drift:
            print("catalog and marketplace are up to date")
        return 1 if findings.errors else 0
    for name, content in catalog_updates(args.root, skills).items():
        path = args.root / name
        if path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
            print(f"updated {name}")
    findings.emit()
    return 1 if findings.errors else 0


def cmd_check_versions(args) -> int:
    try:
        report, findings = check_versions(args.root, args.base)
    except GitError as exc:
        print(f"error: {exc}\nFetch the base branch with full history (actions/checkout fetch-depth: 0).")
        return 1
    for line in report or ["no shipped skill files changed"]:
        print(line)
    findings.emit()
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary and report:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("### Skill versions\n\n" + "\n".join(f"- {line}" for line in report) + "\n")
    return 1 if findings.errors else 0


def select_skills(skills: list[Skill], names: list[str]) -> list[Skill]:
    if not names:
        return skills
    by_name = {s.name: s for s in skills}
    missing = [n for n in names if n not in by_name]
    if missing:
        raise SystemExit(f"unknown skill(s): {', '.join(missing)}")
    return [by_name[n] for n in names]


def cmd_package(args) -> int:
    skills, findings = validate(args.root, check_catalog=False)
    if findings.errors:
        findings.emit()
        print("fix the errors above before packaging")
        return 1
    for skill in select_skills(skills, args.skills):
        archive = package_skill(skill, args.out)
        print(f"{rel(args.root, archive)} ({len(packaged_files(skill))} files)")
    return 0


def cmd_release(args) -> int:
    skills, findings = validate(args.root)
    if findings.errors:
        findings.emit()
        print("refusing to release with validation errors")
        return 1
    pending = pending_releases(args.root, skills)
    if not pending:
        print("every skill version is already released")
        return 0
    target = os.environ.get("GITHUB_SHA") or git(args.root, "rev-parse", "HEAD").strip()
    repository = os.environ.get("GITHUB_REPOSITORY")
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    guide = (
        f"{server}/{repository}/blob/{target}/docs/getting-started.md"
        if repository
        else "docs/getting-started.md"
    )
    for skill in pending:
        notes = changelog_section((skill.path / "CHANGELOG.md").read_text(encoding="utf-8"), skill.version)
        notes = (notes or "See CHANGELOG.md.") + (
            f"\n\n---\n\nUpload `{skill.name}-{skill.version}.zip` to claude.ai or the Claude API, or "
            f"install the `{skill.domain}` plugin from this repository's marketplace in Claude Code. "
            f"See the [installation guide]({guide})."
        )
        archive = package_skill(skill, args.out)
        command = [
            "gh",
            "release",
            "create",
            skill.tag,
            str(archive),
            str(archive) + ".sha256",
            "--title",
            f"{skill.name} v{skill.version}",
            "--target",
            target,
        ]
        if Version.parse(skill.version).is_prerelease:
            command.append("--prerelease")
        if args.dry_run:
            print(f"would release {skill.tag} from {target[:12]}:\n  {shlex.join(command)}")
            print("  notes:\n    " + notes.replace("\n", "\n    "))
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
            fh.write(notes)
        try:
            subprocess.run([*command, "--notes-file", fh.name], check=True)
        finally:
            os.unlink(fh.name)
        print(f"released {skill.tag}")
    return 0


def cmd_notes(args) -> int:
    skill = select_skills(discover(args.root), [args.skill])[0]
    version = args.version or skill.version
    section = changelog_section((skill.path / "CHANGELOG.md").read_text(encoding="utf-8"), version)
    if section is None:
        print(f"no changelog section for {skill.name} {version}", file=sys.stderr)
        return 1
    print(section)
    return 0


def cmd_new(args) -> int:
    try:
        created = scaffold(args.root, args.domain, args.name, args.description)
    except (ValueError, FileExistsError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for path in created:
        print(f"created {rel(args.root, path)}")
    skills = discover(args.root)
    for name, content in catalog_updates(args.root, skills).items():
        path = args.root / name
        if path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
            print(f"updated {name}")
    print("next: write SKILL.md and README.md, then run `make check` (see docs/authoring-skills.md)")
    return 0


def cmd_list(args) -> int:
    skills = discover(args.root)
    if args.json:
        print(
            json.dumps(
                [
                    {"name": s.name, "domain": s.domain, "version": s.version, "path": s.rel, "tag": s.tag}
                    for s in skills
                ],
                indent=2,
            )
        )
        return 0
    for s in skills:
        print(f"{s.name:<32} {s.version or '?':<12} {s.rel}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skillkit", description=__doc__.split("\n")[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="repository root")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="check skills, marketplace, links and catalog")
    p.add_argument("--strict", action="store_true", help="treat warnings as errors")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("catalog", help="regenerate catalog tables and sync marketplace.json")
    p.add_argument("--check", action="store_true", help="report drift without writing")
    p.set_defaults(func=cmd_catalog)

    p = sub.add_parser("check-versions", help="require version bumps for changed skills")
    p.add_argument("--base", default="origin/main", help="git ref to compare with (default origin/main)")
    p.set_defaults(func=cmd_check_versions)

    p = sub.add_parser("package", help="build release zips")
    p.add_argument("skills", nargs="*", help="skill names (default: all)")
    p.add_argument("--out", type=Path, help="output directory (default: <root>/dist)")
    p.set_defaults(func=cmd_package)

    p = sub.add_parser("release", help="publish GitHub releases for untagged skill versions")
    p.add_argument("--dry-run", action="store_true", help="print the plan without publishing")
    p.add_argument("--out", type=Path, help="output directory (default: <root>/dist)")
    p.set_defaults(func=cmd_release)

    p = sub.add_parser("notes", help="print a skill's changelog section")
    p.add_argument("skill")
    p.add_argument("--version", help="defaults to the skill's current version")
    p.set_defaults(func=cmd_notes)

    p = sub.add_parser("new", help="scaffold a new skill")
    p.add_argument("domain", help="domain directory, e.g. fixed-income")
    p.add_argument("name", help="skill name, e.g. bond-relative-value")
    p.add_argument("--description", help="frontmatter description")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("list", help="list skills")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.root = args.root.resolve()
    if hasattr(args, "out"):
        args.out = args.out.resolve() if args.out else args.root / "dist"
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
