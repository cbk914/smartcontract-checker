#!/usr/bin/env python3
# Author: cbk914
"""Install the smart contract analyzers into a dedicated virtual environment.

The original version of this script ran five unpinned `pip install` commands
with shell=True, at run time, into whatever Python interpreter happened to be
active:

    subprocess.check_output(f"pip show {tool}", shell=True, ...)
    subprocess.check_call("pip install mythril", shell=True, ...)

That is unpinned code execution from the ambient interpreter, and two of the
five package names are not the upstream projects at all. See tool-requirements.txt
for the full write-up and the provenance of every pin.

This version:

  * installs into a dedicated virtual environment, never the ambient one,
  * installs exact pinned versions, and refuses to install an unpinned name,
  * invokes pip as a list, never through a shell,
  * installs the two tools that are not on PyPI from their upstream
    repositories at a pinned commit, and reports clearly if they are absent,
  * only reports success when every tool is actually present.
"""

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

# Analyzers distributed on PyPI, pinned to an exact released version.
# The sha256 of each released artifact is recorded in tool-requirements.txt.
PYPI_TOOLS = {
    "mythril": "0.24.8",
    "oyente": "0.2.7",
    "slither-analyzer": "0.11.6",
}

# Analyzers that are NOT distributed on PyPI. `smartcheck` does not exist on
# PyPI at all and `securify` exists as a project name with no uploaded files,
# so `pip install <name>` for either would either fail or pull down whatever
# unrelated party registers under that name later. These are installed from
# their upstream repositories at a pinned commit instead.
UPSTREAM_TOOLS = {
    "smartcheck": (
        "https://github.com/smartdec/smartcheck",
        "7b02010c4b4de20297c6daff5490dd374a796d55",
    ),
    "securify": (
        "https://github.com/eth-sri/securify2",
        "1913dfe797e512e549d02e97ce8ea467be73d3df",
    ),
}

# The command names smartcontract-checker.py probes for on PATH.
TOOL_COMMANDS = {
    "mythril": "myth",
    "oyente": "oyente",
    "slither-analyzer": "slither",
    "smartcheck": "smartcheck",
    "securify": "securify",
}

DEFAULT_VENV = REPO_ROOT / ".venv-tools"

# Names that may be installed from PyPI at all. Anything else is refused.
ALLOWED_PYPI_NAMES = frozenset(PYPI_TOOLS)


class InstallError(Exception):
    """Raised when a tool could not be installed."""


def venv_python(venv_dir):
    """Return the interpreter inside `venv_dir` for the current platform."""
    venv_dir = Path(venv_dir)
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def create_venv(venv_dir):
    """Create the virtual environment if it is not already there."""
    venv_dir = Path(venv_dir)
    if venv_python(venv_dir).exists():
        return venv_python(venv_dir)

    print(f"Creating virtual environment at {venv_dir}")
    venv.create(venv_dir, with_pip=True, clear=False)
    return venv_python(venv_dir)


def build_pip_install_argv(python, package, version):
    """Return the argv for installing `package==version` into `python`.

    Raises ValueError for a package that is not on the allow list, or for a
    missing or non-pinned version. This is what makes an unpinned install
    impossible rather than merely discouraged.
    """
    if package not in ALLOWED_PYPI_NAMES:
        raise ValueError(
            f"refusing to install {package!r} from PyPI: it is not a pinned "
            f"PyPI package (allowed: {sorted(ALLOWED_PYPI_NAMES)})"
        )
    if not version:
        raise ValueError(f"refusing to install {package!r} without a pinned version")
    if "==" not in f"{package}=={version}":
        raise ValueError(f"refusing to install unpinned requirement {package!r}")

    return [
        str(python),
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-input",
        f"{package}=={version}",
    ]


def build_upstream_install_argv(python, repo_url, commit):
    """Return the argv for installing a tool from a pinned upstream commit."""
    if not commit or len(commit) != 40:
        raise ValueError(f"refusing to install from unpinned ref: {commit!r}")
    return [
        str(python),
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-input",
        f"git+{repo_url}@{commit}",
    ]


def tool_installed(python, tool):
    """Return True if `tool` is importable in the environment at `python`."""
    result = subprocess.run(
        [str(python), "-m", "pip", "show", tool],
        shell=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def run_install(argv):
    """Run an install command as a list, never through a shell."""
    print(f"Running: {' '.join(argv)}")
    result = subprocess.run(
        argv,
        shell=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise InstallError(
            f"command failed with exit status {result.returncode}: "
            f"{' '.join(argv)}\n{result.stderr.strip()}"
        )
    return result


def download_tools(venv_dir=DEFAULT_VENV, install_upstream=True):
    """Ensure every analyzer is present in the dedicated virtual environment.

    Returns True only when all of them are present. Raises InstallError when
    an install fails.
    """
    python = create_venv(venv_dir)

    for package, version in PYPI_TOOLS.items():
        if tool_installed(python, package):
            print(f"{package} already installed in {venv_dir}.")
            continue

        print(f"Installing {package}=={version} ...")
        run_install(build_pip_install_argv(python, package, version))

    for tool, (repo_url, commit) in UPSTREAM_TOOLS.items():
        if tool_installed(python, tool):
            print(f"{tool} already installed in {venv_dir}.")
            continue

        if not install_upstream:
            print(
                f"ERROR: {tool} is not installed. It is not distributed on PyPI; "
                f"install it from {repo_url} at commit {commit}."
            )
            continue

        print(f"Installing {tool} from {repo_url}@{commit[:12]} ...")
        try:
            run_install(build_upstream_install_argv(python, repo_url, commit))
        except InstallError as exc:
            # A git install needs a toolchain and network; do not abort the
            # whole run over it, but do not claim success either.
            print(f"ERROR: failed to install {tool}: {exc}")

    missing = [tool for tool in TOOL_COMMANDS if not tool_installed(python, tool)]
    if missing:
        print(
            "The following tools are still missing from "
            f"{venv_dir}: {', '.join(sorted(missing))}"
        )
        return False

    print(f"All tools installed in {venv_dir}.")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Install the smart contract analyzers into a dedicated virtual environment."
    )
    parser.add_argument(
        "--venv",
        default=str(DEFAULT_VENV),
        help="path of the virtual environment to install into "
             f"(default: {DEFAULT_VENV})",
    )
    parser.add_argument(
        "--no-upstream-install",
        action="store_true",
        help="do not install the tools that are not on PyPI; just report them",
    )
    args = parser.parse_args()

    try:
        ok = download_tools(
            venv_dir=Path(args.venv),
            install_upstream=not args.no_upstream_install,
        )
    except InstallError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
