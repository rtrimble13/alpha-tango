"""Tests for scripts/skillkit.py.

Most tests build a throwaway repository in tmp_path, so they do not depend on
the real skills. test_repository_is_valid checks the real repository.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import skillkit  # noqa: E402
from skillkit import Version  # noqa: E402

SKILL_MD = """---
name: {name}
description: Does a thing for tests. Use when a test needs a skill.
metadata:
  version: "{version}"
  domain: {domain}
---

# Test skill

Read [the reference](references/guide.md) when needed.
"""

CHANGELOG = """# Changelog: {name}

## [Unreleased]

## [{version}] - 2026-01-01

### Added

- Something.
"""


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def add_skill(root: Path, name: str = "demo-skill", domain: str = "demo", version: str = "1.0.0") -> Path:
    skill = root / "skills" / domain / name
    write(skill / "SKILL.md", SKILL_MD.format(name=name, version=version, domain=domain))
    write(skill / "references" / "guide.md", "# Guide\n\nBack to [SKILL.md](../SKILL.md).\n")
    write(skill / "README.md", f"# {name}\n")
    write(skill / "CHANGELOG.md", CHANGELOG.format(name=name, version=version))
    if not (root / "skills" / domain / "README.md").exists():
        write(root / "skills" / domain / "README.md", f"# {domain}\n\nSkills for {domain}.\n")
    return skill


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    add_skill(root)
    write(
        root / ".claude-plugin" / "marketplace.json",
        json.dumps({"name": "test", "owner": {"name": "t"}, "plugins": []}),
    )
    write(
        root / "README.md",
        f"# Test\n\n{skillkit.CATALOG_BEGIN}\n{skillkit.CATALOG_END}\n",
    )
    sync(root)
    return root


def sync(root: Path) -> None:
    for name, content in skillkit.catalog_updates(root, skillkit.discover(root)).items():
        (root / name).write_text(content, encoding="utf-8")


def messages(root: Path, level: str = "error") -> list[str]:
    _, findings = skillkit.validate(root)
    return [f.message for f in findings.items if f.level == level]


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        env={
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": str(root),
        },
    ).stdout


def init_git(root: Path) -> None:
    git(root, "init", "-q", "-b", "main")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")


# --------------------------------------------------------------------------- #
# Real repository
# --------------------------------------------------------------------------- #


def test_repository_is_valid():
    skills, findings = skillkit.validate(REPO)
    assert skills, "no skills found"
    assert not findings.errors, [f"{f.path}: {f.message}" for f in findings.errors]


# --------------------------------------------------------------------------- #
# Versions
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "lower, higher",
    [
        ("1.0.0", "1.0.1"),
        ("1.0.9", "1.1.0"),
        ("1.9.9", "2.0.0"),
        ("1.0.0-alpha", "1.0.0"),
        ("1.0.0-alpha", "1.0.0-alpha.1"),
        ("1.0.0-alpha.1", "1.0.0-alpha.beta"),
        ("1.0.0-beta.2", "1.0.0-beta.11"),
        ("1.0.0-rc.1", "1.0.0"),
    ],
)
def test_semver_precedence(lower, higher):
    assert Version.parse(lower) < Version.parse(higher)


def test_build_metadata_is_ignored():
    assert Version.parse("1.2.3+build.5") == Version.parse("1.2.3")


@pytest.mark.parametrize("bad", ["1.0", "v1.0.0", "01.0.0", "1.0.0-", ""])
def test_invalid_versions(bad):
    with pytest.raises(ValueError):
        Version.parse(bad)


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #


def test_valid_fixture_passes(repo):
    assert messages(repo) == []
    assert messages(repo, "warning") == []


def edit_frontmatter(repo: Path, old: str, new: str) -> None:
    path = repo / "skills/demo/demo-skill/SKILL.md"
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new))


@pytest.mark.parametrize(
    "old, new, expected",
    [
        ("name: demo-skill", "name: other-skill", "must match its directory name"),
        ("name: demo-skill", "name: Demo_Skill", "lowercase letters"),
        ('version: "1.0.0"', "version: 1.0", "must be a string"),
        ('version: "1.0.0"', 'version: "1.0"', "not a semantic version"),
        ("domain: demo", "domain: other", "must match its domain directory"),
        ("metadata:", "when_to_use: x\nmetadata:", "not portable"),
        ("Does a thing", "Does a <thing>", "angle brackets"),
    ],
)
def test_frontmatter_errors(repo, old, new, expected):
    edit_frontmatter(repo, old, new)
    assert any(expected in m for m in messages(repo)), messages(repo)


def test_reserved_word_in_name(tmp_path):
    root = tmp_path / "r"
    add_skill(root, name="claude-helper")
    assert any("reserved word" in m for m in messages(root))


def test_description_too_long(repo):
    edit_frontmatter(repo, "Does a thing for tests.", "x" * 1100 + ".")
    assert any("the limit is 1024" in m for m in messages(repo))


def test_missing_frontmatter(repo):
    write(repo / "skills/demo/demo-skill/SKILL.md", "# No frontmatter\n")
    assert any("invalid frontmatter" in m for m in messages(repo))


def test_changelog_must_match_version(repo):
    edit_frontmatter(repo, 'version: "1.0.0"', 'version: "1.1.0"')
    assert any("latest section is [1.0.0]" in m for m in messages(repo))


def test_changelog_order_and_dates(repo):
    write(
        repo / "skills/demo/demo-skill/CHANGELOG.md",
        "# c\n\n## [0.9.0] - 2025-01-01\n\n## [1.0.0]\n",
    )
    found = messages(repo)
    assert any("newest first" in m for m in found)
    assert any("needs a date" in m for m in found)


def test_unreleased_must_come_first(repo):
    path = repo / "skills/demo/demo-skill/CHANGELOG.md"
    path.write_text(path.read_text() + "\n## [Unreleased]\n")
    assert any("[Unreleased] must come before" in m for m in messages(repo))


def test_broken_link_is_reported(repo):
    write(repo / "docs/guide.md", "See [missing](nowhere.md) and [ok](../README.md).\n")
    found = messages(repo)
    assert any("broken link: nowhere.md" in m for m in found)
    assert not any("../README.md" in m for m in found)


def test_links_in_code_are_ignored(repo):
    write(repo / "docs/code.md", "```\n[x](nowhere.md)\n```\n\nInline `[y](gone.md)` too.\n")
    assert messages(repo) == []


def test_missing_domain_readme(repo):
    (repo / "skills/demo/README.md").unlink()
    assert any("domain needs a README.md" in m for m in messages(repo))


def test_misplaced_skill(repo):
    write(
        repo / "skills/demo/demo-skill/nested/SKILL.md",
        SKILL_MD.format(name="nested", version="1.0.0", domain="demo"),
    )
    assert any("skills/<domain>/<skill>/SKILL.md" in m for m in messages(repo))


def test_warnings_for_long_body_orphans_and_toc(repo):
    skill = repo / "skills/demo/demo-skill"
    path = skill / "SKILL.md"
    path.write_text(path.read_text() + "\n".join(f"line {i}" for i in range(600)) + "\n")
    write(skill / "references/orphan.md", "# Orphan\n" + "text\n" * 150)
    warnings = messages(repo, "warning")
    assert any("keep it under 500" in m for m in warnings)
    assert any("not referenced from SKILL.md" in m for m in warnings)
    assert any("Contents" in m for m in warnings)


def test_nested_reference_warning(repo):
    skill = repo / "skills/demo/demo-skill"
    write(skill / "references/second.md", "# Second\n")
    (skill / "SKILL.md").write_text((skill / "SKILL.md").read_text() + "\nAlso references/second.md.\n")
    write(skill / "references/guide.md", "# Guide\n\nSee [second](second.md).\n")
    assert any("one level deep" in m for m in messages(repo, "warning"))


def test_duplicate_names_across_domains(repo):
    add_skill(repo, name="demo-skill", domain="other")
    sync(repo)
    assert any("is also used by" in m for m in messages(repo))


# --------------------------------------------------------------------------- #
# Catalog and marketplace
# --------------------------------------------------------------------------- #


def test_catalog_lists_skill(repo):
    readme = (repo / "README.md").read_text()
    assert "[`demo-skill`](skills/demo/demo-skill/README.md)" in readme
    assert "| 1.0.0 |" in readme


def test_catalog_drift_detected_and_fixed(repo):
    edit_frontmatter(repo, 'version: "1.0.0"', 'version: "1.0.1"')
    log = repo / "skills/demo/demo-skill/CHANGELOG.md"
    log.write_text(log.read_text().replace("## [1.0.0]", "## [1.0.1] - 2026-02-01\n\n- Fix.\n\n## [1.0.0]"))
    assert "README.md" in skillkit.catalog_drift(repo, skillkit.discover(repo))
    sync(repo)
    assert skillkit.catalog_drift(repo, skillkit.discover(repo)) == []
    assert messages(repo) == []


def test_marketplace_sync_creates_domain_plugin(repo):
    data = skillkit.load_marketplace(repo)
    (plugin,) = data["plugins"]
    assert plugin == {
        "name": "demo",
        "description": "Skills for demo.",
        "source": "./",
        "strict": False,
        "skills": ["./skills/demo/demo-skill"],
    }


def test_marketplace_sync_keeps_extra_fields(repo):
    data = skillkit.load_marketplace(repo)
    data["plugins"][0]["tags"] = ["x"]
    write(repo / skillkit.MARKETPLACE, json.dumps(data, indent=2) + "\n")
    add_skill(repo, name="second-skill")
    sync(repo)
    plugin = skillkit.load_marketplace(repo)["plugins"][0]
    assert plugin["tags"] == ["x"]
    assert plugin["skills"] == ["./skills/demo/demo-skill", "./skills/demo/second-skill"]


def test_marketplace_errors(repo):
    data = skillkit.load_marketplace(repo)
    data["plugins"][0]["skills"] = ["./skills/demo/missing"]
    data["plugins"][0]["version"] = "1.0.0"
    write(repo / skillkit.MARKETPLACE, json.dumps(data))
    found = messages(repo)
    assert any("has no SKILL.md" in m for m in found)
    assert any("not in any plugin" in m for m in found)
    assert any("pins users" in m for m in messages(repo, "warning"))


# --------------------------------------------------------------------------- #
# Packaging
# --------------------------------------------------------------------------- #


def test_package_contents_and_determinism(repo, tmp_path):
    skill = skillkit.discover(repo)[0]
    write(skill.path / "references" / "__pycache__" / "x.pyc", "junk")
    first = skillkit.package_skill(skill, tmp_path / "a")
    second = skillkit.package_skill(skill, tmp_path / "b")
    assert first.name == "demo-skill-1.0.0.zip"
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as zf:
        assert sorted(zf.namelist()) == ["demo-skill/SKILL.md", "demo-skill/references/guide.md"]
    digest = (tmp_path / "a" / "demo-skill-1.0.0.zip.sha256").read_text().split()[0]
    assert len(digest) == 64


# --------------------------------------------------------------------------- #
# Changelog sections
# --------------------------------------------------------------------------- #


def test_changelog_section_extraction():
    text = (
        "# c\n\n## [Unreleased]\n\n## [1.1.0] - 2026-02-01\n\n### Added\n\n- New.\n\n"
        "## [1.0.0] - 2026-01-01\n\n- First.\n\n[1.1.0]: https://example.com/compare\n"
    )
    assert skillkit.changelog_section(text, "1.1.0") == "### Added\n\n- New."
    assert skillkit.changelog_section(text, "1.0.0") == "- First."
    assert skillkit.changelog_section(text, "2.0.0") is None


# --------------------------------------------------------------------------- #
# Version gate and releases (need git)
# --------------------------------------------------------------------------- #

needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


@needs_git
def test_check_versions_requires_bump(repo):
    init_git(repo)
    git(repo, "checkout", "-q", "-b", "feature")
    guide = repo / "skills/demo/demo-skill/references/guide.md"
    guide.write_text(guide.read_text() + "\nMore.\n")
    report, findings = skillkit.check_versions(repo, "main")
    assert any("bump it" in f.message for f in findings.errors)

    edit_frontmatter(repo, 'version: "1.0.0"', 'version: "1.1.0"')
    report, findings = skillkit.check_versions(repo, "main")
    assert any("add a '## [1.1.0]" in f.message for f in findings.errors)

    log = repo / "skills/demo/demo-skill/CHANGELOG.md"
    log.write_text(log.read_text().replace("## [1.0.0]", "## [1.1.0] - 2026-02-01\n\n- More.\n\n## [1.0.0]"))
    report, findings = skillkit.check_versions(repo, "main")
    assert not findings.errors
    assert report == ["demo-skill: 1.0.0 -> 1.1.0"]


@needs_git
def test_check_versions_ignores_human_files(repo):
    init_git(repo)
    readme = repo / "skills/demo/demo-skill/README.md"
    readme.write_text(readme.read_text() + "\nMore docs.\n")
    report, findings = skillkit.check_versions(repo, "main")
    assert not findings.errors
    assert report == []


@needs_git
def test_check_versions_new_and_removed_skills(repo):
    init_git(repo)
    add_skill(repo, name="new-skill", version="0.1.0")
    shutil.rmtree(repo / "skills/demo/demo-skill")
    report, findings = skillkit.check_versions(repo, "main")
    assert "new-skill: new skill at 0.1.0" in report
    assert "demo-skill: removed" in report
    assert not findings.errors


@needs_git
def test_pending_releases(repo):
    init_git(repo)
    skills = skillkit.discover(repo)
    assert [s.tag for s in skillkit.pending_releases(repo, skills)] == ["demo-skill-v1.0.0"]
    git(repo, "tag", "demo-skill-v1.0.0")
    assert skillkit.pending_releases(repo, skills) == []


@needs_git
def test_release_dry_run(repo, capsys):
    init_git(repo)
    assert skillkit.main(["--root", str(repo), "release", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "would release demo-skill-v1.0.0" in out
    assert "- Something." in out


# --------------------------------------------------------------------------- #
# Scaffolding
# --------------------------------------------------------------------------- #


def test_new_skill_scaffold_validates(repo):
    shutil.copytree(REPO / "templates", repo / "templates")
    write(repo / "docs/versioning-and-releases.md", "# Versioning\n")  # linked from the template
    code = skillkit.main(
        [
            "--root",
            str(repo),
            "new",
            "fixed-income",
            "bond-math",
            "--description",
            "Bond pricing for tests. Use when a test needs bond math.",
        ]
    )
    assert code == 0
    skill = repo / "skills/fixed-income/bond-math"
    assert (skill / "SKILL.md").is_file()
    assert (repo / "skills/fixed-income/README.md").is_file()
    errors = messages(repo)
    assert errors == [], errors
    assert any("TODO" in m for m in messages(repo, "warning"))
    plugins = {p["name"] for p in skillkit.load_marketplace(repo)["plugins"]}
    assert plugins == {"demo", "fixed-income"}


@pytest.mark.parametrize("domain, name", [("Bad", "ok-name"), ("ok", "claude-x"), ("ok", "a--b")])
def test_new_rejects_bad_names(repo, domain, name):
    shutil.copytree(REPO / "templates", repo / "templates")
    with pytest.raises(ValueError):
        skillkit.scaffold(repo, domain, name, None)


def test_new_rejects_existing_name(repo):
    shutil.copytree(REPO / "templates", repo / "templates")
    with pytest.raises(ValueError, match="already exists"):
        skillkit.scaffold(repo, "other", "demo-skill", None)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Values a company. Use when asked.", "Values a company."),
        ("Builds the U.S. Treasury curve. Use when asked.", "Builds the U.S. Treasury curve."),
        ("Checks ratios, e.g. P/E. Use it.", "Checks ratios, e.g. P/E."),
        ("No full stop", "No full stop"),
    ],
)
def test_first_sentence(text, expected):
    assert skillkit.first_sentence(text) == expected
