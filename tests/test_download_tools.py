"""Regression tests for download-tools.py.

Original defects in download-tools.py:

    download-tools.py:8   subprocess.check_output(f"pip show {tool}", shell=True, ...)
    download-tools.py:21  subprocess.check_call("pip install mythril", shell=True, ...)
    download-tools.py:23  subprocess.check_call("pip install oyente", shell=True, ...)
    download-tools.py:25  subprocess.check_call("pip install slither-analyzer", shell=True, ...)
    download-tools.py:27  subprocess.check_call("pip install smartcheck", shell=True, ...)
    download-tools.py:29  subprocess.check_call("pip install securify", shell=True, ...)

Three things were wrong with that:

  * no version pins, so the code executed was whatever the index served,
  * shell=True, so the command was parsed by a shell,
  * it installed into the ambient interpreter rather than a dedicated
    environment, mutating whatever Python the operator happened to be using.

Plus a supply-chain problem the brief did not mention: two of the five names
are not the upstream projects. `smartcheck` does not exist on PyPI (HTTP 404
on the simple index) and `securify` is a project name with zero uploaded
files. `pip install smartcheck` / `pip install securify` would therefore
either fail or install whatever unrelated party registers under those names
in future -- a dependency-confusion surface.

The tests below never install anything and never touch the network.
"""

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "download-tools.py"

SPEC = importlib.util.spec_from_file_location("download_tools", SCRIPT)
download_tools = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(download_tools)


# --------------------------------------------------------------------------
# No shell, ever
# --------------------------------------------------------------------------

def test_no_shell_true_and_no_os_system():
    """AST proof that the module never asks for a shell."""
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))

    shell_true = []
    os_system = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id == "os" and func.attr == "system":
                os_system.append(node.lineno)
        for keyword in node.keywords:
            if keyword.arg == "shell" and getattr(keyword.value, "value", None) is True:
                shell_true.append(node.lineno)

    assert shell_true == [], f"shell=True still present at line(s) {shell_true}"
    assert os_system == [], f"os.system still present at line(s) {os_system}"


def test_every_subprocess_call_uses_a_list():
    """No subprocess call may take an interpolated string as its argv."""
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))

    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)):
            continue
        if func.value.id != "subprocess":
            continue
        if node.args and isinstance(node.args[0], (ast.JoinedStr, ast.BinOp)):
            offenders.append(node.lineno)

    assert offenders == [], f"subprocess built an argv string at line(s) {offenders}"


# --------------------------------------------------------------------------
# Versions must be pinned
# --------------------------------------------------------------------------

def test_every_pypi_tool_has_an_exact_pin():
    for package, version in download_tools.PYPI_TOOLS.items():
        assert version, f"{package} has no pinned version"
        assert version[0].isdigit(), f"{package} version is not pinned: {version!r}"


def test_install_argv_pins_the_version():
    argv = download_tools.build_pip_install_argv("C:/venv/Scripts/python.exe", "mythril", "0.24.8")

    assert argv[0].endswith("python.exe")
    assert argv[1:4] == ["-m", "pip", "install"]
    assert argv[-1] == "mythril==0.24.8"
    assert "==" in argv[-1]


def test_install_argv_refuses_an_unpinned_requirement():
    """A bare package name must be refused, not installed."""
    with pytest.raises(ValueError) as excinfo:
        download_tools.build_pip_install_argv("python", "some-random-package", "1.0")

    assert "not a pinned PyPI package" in str(excinfo.value)


def test_install_argv_refuses_a_missing_version():
    with pytest.raises(ValueError):
        download_tools.build_pip_install_argv("python", "mythril", "")


def test_smartcheck_and_securify_are_not_pypi_packages():
    """The two names that are not the upstream projects must not be pip-installed.

    smartcheck is a 404 on the PyPI simple index and securify has no
    uploaded files, so pip-installing either bare name is a dependency
    confusion surface.
    """
    assert "smartcheck" not in download_tools.PYPI_TOOLS
    assert "securify" not in download_tools.PYPI_TOOLS

    for name in ("smartcheck", "securify"):
        with pytest.raises(ValueError):
            download_tools.build_pip_install_argv("python", name, "1.0")


def test_upstream_install_argv_is_pinned_to_a_commit():
    argv = download_tools.build_upstream_install_argv(
        "python", "https://github.com/smartdec/smartcheck",
        "7b02010c4b4de20297c6daff5490dd374a796d55",
    )

    assert argv[-1] == "git+https://github.com/smartdec/smartcheck@7b02010c4b4de20297c6daff5490dd374a796d55"


def test_upstream_install_argv_refuses_an_unpinned_ref():
    with pytest.raises(ValueError):
        download_tools.build_upstream_install_argv("python", "https://example.com/x", "master")


# --------------------------------------------------------------------------
# Dedicated environment, not the ambient interpreter
# --------------------------------------------------------------------------

def test_venv_python_path_is_platform_correct(tmp_path):
    import os

    python = download_tools.venv_python(tmp_path / "venv")
    expected = "Scripts" if os.name == "nt" else "bin"
    assert expected in python.parts
    assert python.name in ("python.exe", "python")


def test_download_tools_uses_the_venv_interpreter(monkeypatch, tmp_path):
    """pip must be invoked through the venv interpreter, not sys.executable."""
    calls = []
    venv_dir = tmp_path / "venv"

    def fake_create_venv(_dir):
        return download_tools.venv_python(_dir)

    def fake_tool_installed(_python, tool):
        return True  # nothing to install

    monkeypatch.setattr(download_tools, "create_venv", fake_create_venv)
    monkeypatch.setattr(download_tools, "tool_installed", fake_tool_installed)
    monkeypatch.setattr(download_tools, "run_install", lambda argv: calls.append(argv))

    download_tools.download_tools(venv_dir=venv_dir)

    assert calls == [], "nothing should be installed when every tool is present"
    # The interpreter that would be used is the one inside the venv.
    assert download_tools.venv_python(venv_dir) != Path(sys.executable)


def test_install_lands_in_the_venv(monkeypatch, tmp_path):
    """The recorded install argv must point at the venv interpreter."""
    calls = []
    venv_dir = tmp_path / "venv"

    def fake_create_venv(_dir):
        return download_tools.venv_python(_dir)

    seen = {}

    def fake_tool_installed(python, tool):
        seen.setdefault("python", python)
        # Report present only for the pinned PyPI tools, so the upstream ones
        # are also exercised.
        return tool in download_tools.PYPI_TOOLS

    def fake_run_install(argv):
        calls.append(argv)
        raise download_tools.InstallError("skipped in test")

    monkeypatch.setattr(download_tools, "create_venv", fake_create_venv)
    monkeypatch.setattr(download_tools, "tool_installed", fake_tool_installed)
    monkeypatch.setattr(download_tools, "run_install", fake_run_install)

    download_tools.download_tools(venv_dir=venv_dir)

    assert calls, "expected install commands to be issued"
    for argv in calls:
        assert argv[0] == str(download_tools.venv_python(venv_dir))
        assert argv[0] != sys.executable, "must not install into the ambient interpreter"
        assert argv[1:4] == ["-m", "pip", "install"]


# --------------------------------------------------------------------------
# Honest reporting
# --------------------------------------------------------------------------

def test_missing_tools_are_reported_not_claimed_installed(monkeypatch, tmp_path, capsys):
    """The original printed 'All tools successfully installed.' after a failure."""
    monkeypatch.setattr(download_tools, "create_venv", lambda d: download_tools.venv_python(d))
    monkeypatch.setattr(download_tools, "tool_installed", lambda python, tool: False)
    monkeypatch.setattr(download_tools, "run_install", lambda argv: None)

    ok = download_tools.download_tools(venv_dir=tmp_path / "venv", install_upstream=False)

    out = capsys.readouterr().out
    assert ok is False
    assert "All tools installed" not in out
    assert "still missing" in out


def test_requirements_file_pins_every_installed_package():
    """tool-requirements.txt must pin exactly the packages that get installed."""
    text = (REPO_ROOT / "tool-requirements.txt").read_text(encoding="utf-8")

    for package, version in download_tools.PYPI_TOOLS.items():
        assert f"{package}=={version}" in text, f"{package} is not pinned in tool-requirements.txt"
