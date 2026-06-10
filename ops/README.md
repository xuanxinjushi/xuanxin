# Release to PyPI with Twine

This project publishes from the `usao` conda environment.

## 1) Bump version

Update both version fields before every release:

- `pyproject.toml` (`[project].version`)
- `xuanxin/__init__.py` (`__version__`)

For development releases, use PEP 440 format, for example: `0.1.2.dev0`.

## 2) Build and validate

From repo root:

```bash
conda env usao
python -m pip install --upgrade build twine
rm -rf dist build xuanxin.egg-info
python -m build
python -m twine check dist/*
```

## 3) Upload

Upload using credentials from `.pypirc`:

```bash
python -m twine upload dist/*
```

If you use a named repository in `.pypirc`:

```bash
python -m twine upload --repository <name> dist/*
```

## 4) Verify

Open the package page for the new version:

- https://pypi.org/project/xuanxin/

For a dev release example:

- https://pypi.org/project/xuanxin/0.1.1.dev0/
