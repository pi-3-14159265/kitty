# GitHub Wiki publishing

The pages in `docs/` are the documentation source of truth.

## First-time setup

1. Enable Wikis in the GitHub repository settings.
2. Open or initialize the Wiki once in GitHub.
3. Run `powershell -ExecutionPolicy Bypass -File scripts/publish-wiki.ps1`.

The publisher clones `https://github.com/pi-3-14159265/kitty.wiki.git`,
copies `docs/*.md` into that separate repository, updates `_Sidebar.md`,
and stages the result for review before pushing.

Use `-Push` to publish immediately:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-wiki.ps1 -Push
```

Use `-WikiDir C:\path\to\wiki` to publish into an existing local clone.
