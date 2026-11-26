# Testing and publishing a release

Never upload a release directly to PyPI without testing it first.

## 1. Install release tools

```powershell
python -m pip install --upgrade build twine
```

## 2. Run repository tests

```powershell
python tests/run.py
python -m twine check dist/*
```

Before building, remove old artifacts:

```powershell
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
```

## 3. Build the release

The player's Scratch runtime lives in `kitty_player/vendor/`. To fetch it
again, run `python tools/update_player_vendor.py`; `SOURCES.txt` records each
file's URL and SHA-256, and `python tests/run.py` checks them. Keep the BSD
versions pinned there: later Scratch releases are AGPL-3.0-only.

Update `project.version` in `pyproject.toml` and `__version__` in `kitty.py`
to the same version first.

```powershell
python -m build
python -m twine check dist/*
```

This creates one wheel and one source distribution in `dist/`.

## Windows signing

The package is published by **Thayaden Pi**
(`thayaden_pi@proton.me`) and is identified in package metadata. The
`0.1.2` wheel and `.cmd` launch shims are not automatically Authenticode
signed by the build process.

Before a Windows installer or signed executable is distributed:

1. Obtain a code-signing certificate.
2. Sign the exact executable or installer artifacts with Windows
   Authenticode.
3. Sign the source tag or release checksums in
   [GitHub Releases](https://github.com/pi-3-14159265/kitty/releases).
4. Verify signatures with `Get-AuthenticodeSignature` before upload.
5. Do not claim the plain `.cmd` shims are signed; sign the real executable
   or installer that contains them.

## 4. Test the wheel locally

```powershell
python -m venv .venv-release
.\.venv-release\Scripts\Activate.ps1
python -m pip install --force-reinstall dist\kitty_scratch-0.1.2-py3-none-any.whl
kitty version
```

Create a sample project and compile it:

```powershell
@"
import kitty

@kitty.green_flag
def start():
    kitty.say("Package test")
"@ | Set-Content -Encoding utf8 test_package.py

kitty build test_package.py
```

Then deactivate:

```powershell
deactivate
```

## 5. Upload to TestPyPI

Create an account and API token for TestPyPI at:

```text
https://test.pypi.org/manage/account/token/
```

Upload the same artifacts:

```powershell
python -m twine upload --repository testpypi dist/*
```

## Re-uploading a release

Package indexes do not allow replacing an already published file.

If Twine failed before the upload completed and no `0.1.2` release appears on
TestPyPI, it is safe to retry the exact same artifacts:

```powershell
python -m twine upload --repository testpypi --skip-existing dist/*
```

`--skip-existing` skips files that TestPyPI already has. It does not modify or
replace any published file.

If TestPyPI reports that `kitty-scratch 0.1.2` is already published and the
package needs a correction, do not use the same version. Update both version
values, rebuild a new clean `dist/`, and continue with the next version:

```powershell
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
python -m build
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*
```

PyPI is also immutable for a published version. A published `0.1.2` on PyPI
cannot be overwritten. Release the corrected package as `0.1.3`.

Twine may ask for a username and password. For TestPyPI, use `__token__` as
the username and paste the API token as the password.

Do not add API tokens to source files or this repository.

## 6. Install from TestPyPI

TestPyPI may not contain every dependency. Kitty currently has no dependencies,
so a direct isolated install is enough:

```powershell
python -m venv .venv-testpypi
.\.venv-testpypi\Scripts\Activate.ps1
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps kitty-scratch==0.1.2
kitty version
kitty build test_package.py
deactivate
```

If TestPyPI cannot find the package, confirm the package was uploaded and that
the version is unique and available.

## 7. Upload to PyPI

Create a separate PyPI API token at:

```text
https://pypi.org/manage/account/token/
```

Upload only after TestPyPI installation succeeds:

```powershell
python -m twine upload dist/*
```

Use `__token__` and the PyPI token. PyPI package versions are permanent; a
published version cannot normally be replaced. Build and test a new version
instead.

## 8. Verify the real package

```powershell
python -m venv .venv-pypi
.\.venv-pypi\Scripts\Activate.ps1
python -m pip install kitty-scratch==0.1.2
kitty version
kitty build test_package.py
deactivate
```
