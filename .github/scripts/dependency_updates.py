#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["packaging>=24,<27"]
# ///
"""Work out the lockfile updates one side of the repo needs, and report them.

Nothing is committed: the lockfile is updated in the throwaway checkout only to
learn the exact versions an update lands on, which are then reported.

Two kinds of update share this script:

``security``
    OSV-Scanner checks the lockfile of the checked out branch against the
    OSV.dev database (which includes the GitHub Advisory Database used by
    Dependabot), the vulnerable packages are upgraded to a patched version,
    and the lockfile is scanned again to tell what is fixed from what is not.
    Accepted risks are ignored through ``osv-scanner.toml``.

``version``
    Every package moves to the newest version the ranges already declared in
    the manifest allow: minor and patch updates, as every direct dependency is
    capped below its next major. Internal packages (the ones not resolved from
    the public npm registry, i.e. ``@swo/*``) are held at their locked version:
    their patch releases move the exact peer versions they require, so they
    are bumped by hand together with those peers.

Only lockfiles change. Manifests (``pyproject.toml``, ``package.json``) are
never edited, so a security fix that needs a constraint bump is reported as
manual work instead of being forced in, and a version update never crosses a
major of a direct dependency.

Outputs a JSON report, read by the Teams notification, a Markdown report for
the job summary, and ``has_updates`` on ``$GITHUB_OUTPUT``.
"""

import argparse
import json
import os
import re
import subprocess
import tomllib
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

SIDES: dict[str, dict[str, str]] = {
    "backend": {
        "label": "Backend",
        "ecosystem": "pip",
        "directory": "backend",
        "lockfile": "backend/uv.lock",
        "manifest": "pyproject.toml",
    },
    "frontend": {
        "label": "Frontend",
        "ecosystem": "npm",
        "directory": "frontend",
        "lockfile": "frontend/package-lock.json",
        "manifest": "package.json",
    },
    "e2e": {
        "label": "E2E",
        "ecosystem": "npm",
        "directory": "e2e",
        "lockfile": "e2e/package-lock.json",
        "manifest": "package.json",
    },
}

PUBLIC_NPM_REGISTRY = "https://registry.npmjs.org/"

SEVERITY_ORDER = ("critical", "high", "medium", "low")
# GitHub advisories label severity; the other OSV sources only give a CVSS score.
GHSA_SEVERITIES = {
    "CRITICAL": "critical",
    "HIGH": "high",
    "MODERATE": "medium",
    "LOW": "low",
}
CVSS_SEVERITIES = ((9.0, "critical"), (7.0, "high"), (4.0, "medium"), (0.1, "low"))
OSV_ECOSYSTEMS = {"pip": "PyPI", "npm": "npm"}
UPDATE_TYPE_ORDER = ("major", "minor", "patch", "other", "added", "removed")

# GitHub caps each step's job summary at 1 MiB.
MAX_SUMMARY_LENGTH = 1_000_000

SEMVER = re.compile(
    r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$"
)


@dataclass
class Vulnerability:
    id: str
    cve_id: str | None
    severity: str
    summary: str
    vulnerable_ranges: list[str]
    patched_versions: list[str]
    advisory_url: str


@dataclass
class PackageFix:
    package: str
    relationship: str
    affected_versions: list[str]
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    patched_versions: list[str] = field(default_factory=list)
    fixed_versions: list[str] = field(default_factory=list)
    reason: str | None = None

    @property
    def severity_rank(self) -> int:
        return min(severity_rank(v.severity) for v in self.vulnerabilities)


@dataclass
class PackageUpdate:
    package: str
    direct: bool
    from_versions: list[str]
    to_versions: list[str]
    update_type: str


def severity_rank(severity: str) -> int:
    """Lower is more severe; unknown severities sort last."""
    try:
        return SEVERITY_ORDER.index(severity.lower())
    except ValueError:
        return len(SEVERITY_ORDER)


def semver_key(version: str) -> tuple[Any, ...]:
    """Sort key following the SemVer 2 precedence rules used by npm."""
    match = SEMVER.match(version.strip())
    if not match:
        raise ValueError(f"Not a semantic version: {version!r}")
    major, minor, patch, pre = match.groups()
    core = (int(major), int(minor), int(patch))
    if pre is None:
        # A release outranks every pre-release of the same core version.
        return (core, (1,))
    parts = tuple(
        (0, int(part), "") if part.isdigit() else (1, 0, part)
        for part in pre.split(".")
    )
    return (core, (0, parts))


def version_parser(ecosystem: str) -> Callable[[str], Any]:
    return Version if ecosystem == "pip" else semver_key


def release_parts(version: str, ecosystem: str) -> tuple[int, int, int]:
    """The major, minor and patch numbers of a version."""
    if ecosystem == "pip":
        release = (*Version(version).release, 0, 0)
        return release[0], release[1], release[2]
    return semver_key(version)[0]


def update_type(old: str, new: str, ecosystem: str) -> str:
    old_parts = release_parts(old, ecosystem)
    new_parts = release_parts(new, ecosystem)
    for kind, old_part, new_part in zip(
        ("major", "minor", "patch"), old_parts, new_parts, strict=True
    ):
        if old_part != new_part:
            return kind
    # e.g. 2.9.0.20260807 -> 2.9.0.20261104 for typing stubs, or a new pre-release.
    return "patch"


def normalize(name: str, ecosystem: str) -> str:
    return canonicalize_name(name) if ecosystem == "pip" else name


def read_npm_lock(side: dict[str, str]) -> dict[str, dict[str, Any]]:
    return json.loads(Path(side["lockfile"]).read_text())["packages"]


def npm_name(path: str, package: dict[str, Any]) -> str:
    return package.get("name") or path.rsplit("node_modules/", 1)[1]


def internal_packages(side: dict[str, str]) -> dict[str, str]:
    """Locked packages that come from a private registry, by path."""
    if side["ecosystem"] != "npm":
        return {}
    return {
        path: package["version"]
        for path, package in read_npm_lock(side).items()
        if "node_modules/" in path
        and package.get("resolved")
        and not package["resolved"].startswith(PUBLIC_NPM_REGISTRY)
    }


def check_internal_held(before: dict[str, str], side: dict[str, str]) -> None:
    """Fail when an update moved an internal package."""
    after = internal_packages(side)
    moved = [
        f"{path.rsplit('node_modules/', 1)[1]} {version} -> {after.get(path, 'removed')}"
        for path, version in before.items()
        if after.get(path) != version
    ]
    if moved:
        raise SystemExit(f"Internal packages must not move: {', '.join(moved)}")


def locked_versions(side: dict[str, str]) -> dict[str, set[str]]:
    """Map every package in the lockfile to the versions it is locked at."""
    versions: dict[str, set[str]] = {}
    if side["ecosystem"] == "pip":
        lock = tomllib.loads(Path(side["lockfile"]).read_text())
        for package in lock["package"]:
            if "version" in package:
                name = canonicalize_name(package["name"])
                versions.setdefault(name, set()).add(package["version"])
        return versions

    for path, package in read_npm_lock(side).items():
        if (
            "node_modules/" not in path
            or package.get("link")
            or "version" not in package
        ):
            continue
        versions.setdefault(npm_name(path, package), set()).add(package["version"])
    return versions


def direct_dependencies(side: dict[str, str]) -> set[str]:
    """Names declared in the manifest, in every dependency group."""
    manifest = Path(side["directory"]) / side["manifest"]
    if side["ecosystem"] == "pip":
        pyproject = tomllib.loads(manifest.read_text())
        project = pyproject.get("project", {})
        specs = list(project.get("dependencies", []))
        for group in project.get("optional-dependencies", {}).values():
            specs += group
        for group in pyproject.get("dependency-groups", {}).values():
            specs += [spec for spec in group if isinstance(spec, str)]
        return {canonicalize_name(Requirement(spec).name) for spec in specs}

    package = json.loads(manifest.read_text())
    return {
        name
        for key in (
            "dependencies",
            "devDependencies",
            "optionalDependencies",
            "peerDependencies",
        )
        for name in package.get(key, {})
    }


def check_npm_tree(before: dict[str, dict[str, Any]], side: dict[str, str]) -> None:
    """Fail when npm dropped a package that something still requires.

    A healthy update only drops packages nobody depends on any more; a missing
    required one means npm resolved the tree in a way ``npm ci`` would reject.
    """
    after = read_npm_lock(side)

    def names(packages: dict[str, dict[str, Any]]) -> set[str]:
        return {
            npm_name(path, p) for path, p in packages.items() if "node_modules/" in path
        }

    dropped = names(before) - names(after)
    missing = set()
    for path, package in after.items():
        optional_peers = package.get("peerDependenciesMeta", {})
        for key in ("dependencies", "optionalDependencies", "peerDependencies"):
            for name in package.get(key, {}):
                if name not in dropped:
                    continue
                if key == "peerDependencies" and optional_peers.get(name, {}).get(
                    "optional"
                ):
                    continue
                missing.add(f"{name} (required by {path or 'the root package'})")
    if missing:
        raise SystemExit(
            f"npm dropped packages that are still required: {', '.join(sorted(missing))}"
        )


def osv_scan(
    side: dict[str, str], scanner: str, config: Path | None, output: Path
) -> dict[str, Any]:
    """Scan the side's lockfile with OSV-Scanner and return its JSON report."""
    command = [scanner, "scan", "source", "--lockfile", side["lockfile"]]
    if config:
        command += ["--config", str(config)]
    command += ["--format", "json", "--output-file", str(output)]
    print(f"$ {' '.join(command)}", flush=True)
    result = subprocess.run(  # noqa: S603
        command, check=False, capture_output=True, text=True
    )
    print(result.stderr, flush=True)
    # 0: nothing found, 1: vulnerabilities found, anything else: the scan failed.
    if result.returncode not in (0, 1):
        raise SystemExit(f"OSV-Scanner failed: {failure_reason(result)}")
    return json.loads(output.read_text())


def osv_packages(scan: dict[str, Any], side: dict[str, str]) -> list[dict[str, Any]]:
    return [
        package
        for result in scan.get("results", [])
        for package in result.get("packages", [])
        if package["package"]["ecosystem"] == OSV_ECOSYSTEMS[side["ecosystem"]]
    ]


def vulnerable_ids(scan: dict[str, Any], side: dict[str, str]) -> dict[str, set[str]]:
    """Every id and alias of the vulnerabilities reported for each package."""
    ids: dict[str, set[str]] = {}
    for package in osv_packages(scan, side):
        name = normalize(package["package"]["name"], side["ecosystem"])
        for group in package.get("groups", []):
            ids.setdefault(name, set()).update(group["ids"], group.get("aliases", []))
    return ids


def affected_interval(
    record: dict[str, Any], name: str, version: str, side: dict[str, str]
) -> tuple[str, str | None] | None:
    """The OSV range that contains ``version``, and the version that fixes it."""
    parse = version_parser(side["ecosystem"])
    current = parse(version)
    for affected in record.get("affected", []):
        if normalize(affected["package"]["name"], side["ecosystem"]) != name:
            continue
        for osv_range in affected.get("ranges", []):
            if osv_range["type"] not in ("ECOSYSTEM", "SEMVER"):
                continue
            introduced: str | None = None
            for event in [*osv_range["events"], {}]:
                if "introduced" in event:
                    introduced = event["introduced"]
                    continue
                if introduced is None:
                    continue
                upper = event.get("fixed") or event.get("last_affected")
                try:
                    above = introduced == "0" or current >= parse(introduced)
                    below = upper is None or (
                        current < parse(upper)
                        if "fixed" in event
                        else current <= parse(upper)
                    )
                except ValueError:
                    introduced = None
                    continue
                if above and below:
                    clauses = [] if introduced == "0" else [f">= {introduced}"]
                    if "fixed" in event:
                        clauses.append(f"< {upper}")
                    elif upper:
                        clauses.append(f"<= {upper}")
                    return ", ".join(clauses) or "all versions", event.get("fixed")
                introduced = None
    return None


def group_severity(group: dict[str, Any], records: list[dict[str, Any]]) -> str:
    for record in records:
        label = (record.get("database_specific") or {}).get("severity")
        if label in GHSA_SEVERITIES:
            return GHSA_SEVERITIES[label]
    try:
        score = float(group.get("max_severity") or 0)
    except ValueError:
        score = 0
    return next((name for floor, name in CVSS_SEVERITIES if score >= floor), "unknown")


def collect_fixes(
    scan: dict[str, Any], side: dict[str, str], direct: set[str]
) -> list[PackageFix]:
    """Group the vulnerabilities found in the lockfile by package."""
    ecosystem = side["ecosystem"]
    parse = version_parser(ecosystem)
    fixes: dict[str, PackageFix] = {}

    for package in osv_packages(scan, side):
        name = normalize(package["package"]["name"], ecosystem)
        version = package["package"]["version"]
        records = {record["id"]: record for record in package["vulnerabilities"]}
        fix = fixes.setdefault(
            name,
            PackageFix(
                package=name,
                relationship="direct" if name in direct else "transitive",
                affected_versions=[],
            ),
        )
        fix.affected_versions = sorted({*fix.affected_versions, version}, key=parse)

        # A group is one vulnerability published under several ids (GHSA,
        # PYSEC, CVE, ...); the GitHub advisory is preferred for the display.
        for group in package.get("groups", []):
            ids = [*group["ids"], *group.get("aliases", [])]
            grouped = [records[i] for i in group["ids"] if i in records]
            grouped.sort(key=lambda r: not r["id"].startswith("GHSA-"))
            shown_id = next((i for i in ids if i.startswith("GHSA-")), group["ids"][0])
            intervals = [
                interval
                for record in grouped
                if (interval := affected_interval(record, name, version, side))
            ]
            vulnerable_range, patched = (
                intervals[0] if intervals else (f"= {version}", None)
            )

            existing = next((v for v in fix.vulnerabilities if v.id == shown_id), None)
            if existing:
                # The same advisory hits another locked version of the package.
                if vulnerable_range not in existing.vulnerable_ranges:
                    existing.vulnerable_ranges.append(vulnerable_range)
                if patched and patched not in existing.patched_versions:
                    existing.patched_versions.append(patched)
                continue
            fix.vulnerabilities.append(
                Vulnerability(
                    id=shown_id,
                    cve_id=next((i for i in ids if i.startswith("CVE-")), None),
                    severity=group_severity(group, grouped),
                    summary=next(
                        (r["summary"] for r in grouped if r.get("summary")), ""
                    ),
                    vulnerable_ranges=[vulnerable_range],
                    patched_versions=[patched] if patched else [],
                    advisory_url=(
                        f"https://github.com/advisories/{shown_id}"
                        if shown_id.startswith("GHSA-")
                        else f"https://osv.dev/vulnerability/{shown_id}"
                    ),
                )
            )

    for fix in fixes.values():
        fix.vulnerabilities.sort(key=lambda v: severity_rank(v.severity))
        fix.patched_versions = sorted(
            {p for v in fix.vulnerabilities for p in v.patched_versions}, key=parse
        )
    return sorted(fixes.values(), key=lambda f: (f.severity_rank, f.package))


def run(command: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
    shown = (
        command if len(command) <= 12 else [*command[:8], f"… {len(command) - 8} more"]
    )
    print(f"$ {' '.join(shown)}", flush=True)
    # Fixed argument lists, no shell: package names only come from the lockfile
    # and the OSV-Scanner report.
    result = subprocess.run(  # noqa: S603
        command, check=False, cwd=cwd, capture_output=True, text=True
    )
    print(result.stdout + result.stderr, flush=True)
    return result


def failure_reason(result: subprocess.CompletedProcess[str]) -> str:
    """Pick the line of a resolver error that explains the conflict."""
    lines = [line.strip() for line in result.stderr.splitlines() if line.strip()]
    for prefix in ("cause:", "npm error code", "error:"):
        for line in lines:
            if line.startswith(prefix):
                return line
    return lines[-1] if lines else f"exit code {result.returncode}"


def uv_lock(side: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return run(["uv", "lock", "--project", side["directory"], *args], cwd=".")


def npm_update(side: dict[str, str], *names: str) -> subprocess.CompletedProcess[str]:
    # Only the lockfile changes: package.json ranges are left as they are.
    return run(
        [
            "npm",
            "update",
            *names,
            "--package-lock-only",
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
        ],
        cwd=side["directory"],
    )


def apply_security_backend(
    fixes: list[PackageFix], side: dict[str, str]
) -> dict[str, str]:
    """Pin each package to the patched version in uv.lock, one at a time."""
    errors: dict[str, str] = {}
    for fix in fixes:
        if not fix.patched_versions:
            continue
        # The exact patched version keeps the bump minimal; ">=" covers a
        # patched release that has no wheel for one of the resolver splits.
        target = max(fix.patched_versions, key=Version)
        for requirement in (f"{fix.package}=={target}", f"{fix.package}>={target}"):
            result = uv_lock(side, "--upgrade-package", requirement)
            if result.returncode == 0:
                errors.pop(fix.package, None)
                break
            errors[fix.package] = failure_reason(result)
    return errors


def apply_security_npm(fixes: list[PackageFix], side: dict[str, str]) -> dict[str, str]:
    """Let npm move every vulnerable package to the newest version its parents allow."""
    names = [fix.package for fix in fixes if fix.patched_versions]
    if not names:
        return {}
    result = npm_update(side, *names)
    if result.returncode == 0:
        return {}
    return dict.fromkeys(names, failure_reason(result))


def internal_blocker(name: str, side: dict[str, str]) -> str | None:
    """Describe the internal package whose declared range holds ``name`` back."""
    if side["ecosystem"] != "npm":
        return None
    packages = read_npm_lock(side)
    for path in internal_packages(side):
        package = packages[path]
        for key in ("peerDependencies", "dependencies"):
            if name in package.get(key, {}):
                return (
                    f"Held by {npm_name(path, package)} {package['version']}, "
                    f"which requires {name} {package[key][name]}"
                )
    return None


def classify(
    fixes: list[PackageFix],
    side: dict[str, str],
    locked_before: dict[str, set[str]],
    still_vulnerable: dict[str, set[str]],
    errors: dict[str, str],
) -> tuple[list[PackageFix], list[PackageFix]]:
    """Split the packages into fixed ones and ones that need a manual bump.

    ``still_vulnerable`` comes from scanning the lockfile again after the update.
    """
    parse = version_parser(side["ecosystem"])
    locked = locked_versions(side)
    fixed: list[PackageFix] = []
    manual: list[PackageFix] = []
    for fix in fixes:
        after = locked.get(fix.package, set())
        # npm can lock one package at several majors; the unaffected copies
        # were already there and are not what this update introduced.
        fix.fixed_versions = sorted(
            (after - locked_before.get(fix.package, set())) or after, key=parse
        )
        remaining_ids = still_vulnerable.get(fix.package, set())
        remaining = [v for v in fix.vulnerabilities if v.id in remaining_ids]
        if not remaining:
            fixed.append(fix)
            continue
        if not all(v.patched_versions for v in remaining):
            fix.reason = "No patched version has been published yet."
        elif fix.package in errors:
            fix.reason = errors[fix.package]
        elif fix.relationship == "direct":
            fix.reason = (
                f"The range in {side['manifest']} excludes the patched version."
            )
        elif blocker := internal_blocker(fix.package, side):
            fix.reason = f"{blocker}."
        else:
            fix.reason = "A parent dependency pins a vulnerable version."
        manual.append(fix)
    return fixed, manual


def apply_version_backend(side: dict[str, str], direct: set[str]) -> None:
    """Upgrade uv.lock within pyproject.toml, holding direct deps on their major."""
    before = locked_versions(side)
    result = uv_lock(side, "--upgrade")
    if result.returncode != 0:
        raise SystemExit(f"uv lock --upgrade failed: {failure_reason(result)}")

    # A direct dependency declared without an upper bound (e.g. ">=0.10.2")
    # could jump a major; hold it below the next one, as Dependabot did.
    parse = version_parser(side["ecosystem"])
    for name, versions in locked_versions(side).items():
        if name not in direct or not before.get(name):
            continue
        old = max(before[name], key=parse)
        new = max(versions, key=parse)
        if update_type(old, new, "pip") != "major":
            continue
        next_major = release_parts(old, "pip")[0] + 1
        result = uv_lock(side, "--upgrade-package", f"{name}<{next_major}")
        if result.returncode != 0:
            raise SystemExit(
                f"Could not hold {name} below {next_major}: {failure_reason(result)}"
            )


def apply_version_npm(side: dict[str, str]) -> None:
    """Upgrade package-lock.json within the package.json ranges.

    Naming every public package, rather than running a bare ``npm update``,
    leaves the internal ones, and so the peers they pin, where they are.
    """
    internal = {
        npm_name(path, package)
        for path, package in read_npm_lock(side).items()
        if path in internal_packages(side)
    }
    names = sorted(set(locked_versions(side)) - internal)
    result = npm_update(side, *names)
    if result.returncode != 0:
        raise SystemExit(f"npm update failed: {failure_reason(result)}")


def collect_updates(
    side: dict[str, str],
    before: dict[str, set[str]],
    direct: set[str],
) -> list[PackageUpdate]:
    """Compare the lockfile with its state before the update, package by package."""
    ecosystem = side["ecosystem"]
    parse = version_parser(ecosystem)
    after = locked_versions(side)
    updates = []
    for name in sorted(before.keys() | after.keys()):
        old = before.get(name, set())
        new = after.get(name, set())
        if old == new:
            continue
        removed = sorted(old - new, key=parse)
        added = sorted(new - old, key=parse)
        if not old:
            kind = "added"
        elif not new:
            kind = "removed"
        elif removed and added:
            kind = update_type(
                max(removed, key=parse), max(added, key=parse), ecosystem
            )
        else:
            # One copy was deduplicated into, or split from, another version.
            kind = "other"
        updates.append(
            PackageUpdate(
                package=name,
                direct=name in direct,
                from_versions=removed or sorted(old, key=parse),
                to_versions=added or sorted(new, key=parse),
                update_type=kind,
            )
        )
    return sorted(
        updates,
        key=lambda u: (not u.direct, UPDATE_TYPE_ORDER.index(u.update_type), u.package),
    )


def escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def vulnerability_markdown(fix: PackageFix) -> str:
    lines = []
    for v in fix.vulnerabilities:
        cve = f" ({v.cve_id})" if v.cve_id else ""
        lines.append(
            f"[{v.id}]({v.advisory_url}){cve} **{v.severity}** "
            f"`{'; '.join(v.vulnerable_ranges)}`: {escape_cell(v.summary)}"
        )
    return "<br>".join(lines)


def footer() -> list[str]:
    return [
        "",
        "---",
        (
            "Reported by the **Dependency updates** workflow. Nothing was committed: "
            "the updates have to be applied by hand."
        ),
    ]


def apply_commands(side: dict[str, str], fixed: list[PackageFix]) -> list[str]:
    """The commands that reproduce the security fixes locally."""
    if side["ecosystem"] == "pip":
        upgrades = " ".join(
            f"--upgrade-package '{fix.package}=={max(fix.fixed_versions, key=Version)}'"
            for fix in fixed
            if fix.fixed_versions
        )
        return [f"uv lock --project {side['directory']} {upgrades}"]
    names = " ".join(fix.package for fix in fixed)
    return [f"cd {side['directory']}", f"npm update {names} --package-lock-only"]


def render_security_body(
    side: dict[str, str],
    base: str,
    fixed: list[PackageFix],
    manual: list[PackageFix],
) -> str:
    label = side["label"]
    body = [
        (
            f"Known vulnerabilities in the **{label}** dependencies locked on "
            f"`{base}`, found by [OSV-Scanner](https://google.github.io/osv-scanner/), "
            "and the lockfile updates that fix them."
        ),
        "",
        "## Dependencies to update",
        "",
        "| Package | Affected version | Fixed version | Vulnerability |",
        "| --- | --- | --- | --- |",
    ]
    for fix in fixed:
        body.append(
            f"| `{fix.package}` | {', '.join(fix.affected_versions)} | "
            f"{', '.join(fix.fixed_versions) or 'removed'} | "
            f"{vulnerability_markdown(fix)} |"
        )
    if fixed:
        body += ["", "To apply them:", "", "```sh", *apply_commands(side, fixed), "```"]
    if manual:
        body += [
            "",
            "## Needs manual action",
            "",
            "These vulnerabilities could not be fixed from the lockfile alone.",
            "",
            "| Package | Affected version | Patched in | Vulnerability | Why |",
            "| --- | --- | --- | --- | --- |",
        ]
        for fix in manual:
            body.append(
                f"| `{fix.package}` | {', '.join(fix.affected_versions)} | "
                f"{', '.join(fix.patched_versions) or 'n/a'} | "
                f"{vulnerability_markdown(fix)} | "
                f"{escape_cell(fix.reason or '')} |"
            )
    return "\n".join(body + footer()) + "\n"


def update_rows(updates: list[PackageUpdate]) -> list[str]:
    return [
        f"| `{u.package}` | {', '.join(u.from_versions)} | "
        f"{', '.join(u.to_versions)} | {u.update_type} |"
        for u in updates
    ]


def render_version_body(
    side: dict[str, str],
    base: str,
    updates: list[PackageUpdate],
    internal: dict[str, str],
) -> str:
    label = side["label"]
    header = [
        "| Package | Current version | New version | Update |",
        "| --- | --- | --- | --- |",
    ]
    direct = [u for u in updates if u.direct]
    transitive = [u for u in updates if not u.direct]
    body = [
        (
            f"Minor and patch updates available for the **{label}** dependencies "
            f"on `{base}`, within the ranges declared in `{side['manifest']}`."
        ),
        "",
        "## Direct dependencies",
        "",
    ]
    body += [*header, *update_rows(direct)] if direct else ["None."]
    if internal:
        held = ", ".join(f"`{name}` {version}" for name, version in internal.items())
        body += [
            "",
            (
                f"Internal packages are held at their current version: {held}. "
                "Bump them by hand, together with the peers they pin."
            ),
        ]
    if transitive:
        body += [
            "",
            "<details>",
            f"<summary>{len(transitive)} transitive dependencies</summary>",
            "",
            *header,
        ]
        tail = ["", "</details>", *footer()]
        used = len("\n".join(body + tail))
        for row in update_rows(transitive):
            if used + len(row) + 80 > MAX_SUMMARY_LENGTH:
                body.append("| … | | | too many to list |")
                break
            body.append(row)
            used += len(row) + 1
        return "\n".join(body + tail) + "\n"
    return "\n".join(body + footer()) + "\n"


def write_outputs(
    args: argparse.Namespace, report: dict[str, Any], body: str, has_updates: bool
) -> None:
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2))
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    # Appended, as $GITHUB_STEP_SUMMARY may already hold other output.
    with args.summary.open("a", encoding="utf-8") as summary:
        summary.write(f"# {args.title}\n\n{body}")
    if github_output := os.environ.get("GITHUB_OUTPUT"):
        with open(github_output, "a", encoding="utf-8") as output:
            output.write(f"has_updates={str(has_updates).lower()}\n")


def run_security(args: argparse.Namespace, side: dict[str, str]) -> None:
    scan_dir = args.report.parent
    scan_dir.mkdir(parents=True, exist_ok=True)

    def scan(name: str) -> dict[str, Any]:
        return osv_scan(side, args.osv_scanner, args.osv_config, scan_dir / name)

    locked_before = locked_versions(side)
    npm_before = read_npm_lock(side) if side["ecosystem"] == "npm" else {}
    internal_before = internal_packages(side)
    fixes = collect_fixes(scan("osv-before.json"), side, direct_dependencies(side))
    print(f"{len(fixes)} {side['label']} package(s) affected on {args.base}.")

    if side["ecosystem"] == "pip":
        errors = apply_security_backend(fixes, side)
    else:
        errors = apply_security_npm(fixes, side)
        check_npm_tree(npm_before, side)
        check_internal_held(internal_before, side)
    still_vulnerable = vulnerable_ids(scan("osv-after.json"), side)
    fixed, manual = classify(fixes, side, locked_before, still_vulnerable, errors)

    report = {
        "kind": "security",
        "side": args.side,
        "label": side["label"],
        "base": args.base,
        "repo": args.repo,
        "fixed": [asdict(fix) for fix in fixed],
        "manual": [asdict(fix) for fix in manual],
    }
    body = render_security_body(side, args.base, fixed, manual)
    write_outputs(args, report, body, has_updates=bool(fixed or manual))
    print(f"Fixed {len(fixed)}, manual {len(manual)}.")


def run_version(args: argparse.Namespace, side: dict[str, str]) -> None:
    direct = direct_dependencies(side)
    before = locked_versions(side)
    internal_before = internal_packages(side)
    if side["ecosystem"] == "pip":
        apply_version_backend(side, direct)
    else:
        npm_before = read_npm_lock(side)
        apply_version_npm(side)
        check_npm_tree(npm_before, side)
        check_internal_held(internal_before, side)
    internal = {
        path.rsplit("node_modules/", 1)[1]: version
        for path, version in internal_before.items()
    }
    updates = collect_updates(side, before, direct)

    report = {
        "kind": "version",
        "side": args.side,
        "label": side["label"],
        "base": args.base,
        "repo": args.repo,
        "updates": [asdict(update) for update in updates],
        "internal": internal,
    }
    body = render_version_body(side, args.base, updates, internal)
    write_outputs(args, report, body, has_updates=bool(updates))
    print(f"{len(updates)} package(s) updated.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--kind", required=True, choices=("security", "version"))
    parser.add_argument("--side", required=True, choices=sorted(SIDES))
    parser.add_argument("--base", required=True, help="Branch the updates target")
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument(
        "--summary",
        required=True,
        type=Path,
        help="Markdown report, appended to (e.g. $GITHUB_STEP_SUMMARY)",
    )
    parser.add_argument("--title", required=True, help="Heading of the report")
    parser.add_argument(
        "--osv-scanner", default="osv-scanner", help="OSV-Scanner executable"
    )
    parser.add_argument(
        "--osv-config",
        type=Path,
        help="osv-scanner.toml with the ignored vulnerabilities",
    )
    args = parser.parse_args()

    side = SIDES[args.side]
    if args.kind == "security":
        run_security(args, side)
    else:
        run_version(args, side)


if __name__ == "__main__":
    main()
