# Installation Guide

## Windows PowerShell

```powershell
cd C:\Users\ASUS\Desktop\new-AI
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install --cache-dir .pip-cache -e .
```

## Linux Or macOS

```bash
cd /path/to/new-AI
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install --cache-dir .pip-cache -e .
```

## Optional Extras (Install Only What You Need)

```bash
python -m pip install --cache-dir .pip-cache -e ".[dev]"
python -m pip install --cache-dir .pip-cache -e ".[providers]"
python -m pip install --cache-dir .pip-cache -e ".[tree-sitter]"
python -m pip install --cache-dir .pip-cache -e ".[mcp]"
```

On slower or unstable machines, install extras one-by-one. If `tree-sitter` fails, skip it first and continue with local fallback parsers.

## One-Line Full Setup (Slower, More Dependencies)

```bash
python -m pip install --cache-dir .pip-cache -e ".[dev,providers,tree-sitter,mcp]"
```

## Verify

```powershell
repobrain doctor --format text
repobrain index --format text
repobrain query "Where is RepoBrain CLI implemented?" --format text
repobrain report --format text
repobrain chat
```
