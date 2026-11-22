param(
    [switch]$Push,
    [string]$WikiDir
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root "docs"
$remote = "https://github.com/pi-3-14159265/kitty.wiki.git"

if ([string]::IsNullOrWhiteSpace($WikiDir)) {
    $WikiDir = Join-Path ([System.IO.Path]::GetTempPath()) ("kitty-wiki-" + [guid]::NewGuid())
    git clone $remote $WikiDir
} elseif (-not (Test-Path (Join-Path $WikiDir ".git"))) {
    throw "WikiDir must be an existing Git wiki clone: $WikiDir"
}

Get-ChildItem -Path $WikiDir -Filter "*.md" | Remove-Item -Force
Get-ChildItem -Path $source -Filter "*.md" |
    Where-Object { $_.Name -ne "README.md" } |
    Copy-Item -Destination $WikiDir -Force

@'
* [Home](Home)
* [Getting Started](getting-started)
* [Scripts](scripts)
* [Values and Math](values-and-math)
* [Choices and Loops](choices-and-loops)
* [Lists](lists)
* [Dictionaries](dictionaries)
* [Functions](functions)
* [Sprites](sprites)
* [Reference](reference)
* [Events](events)
* [Motion](motion)
* [Looks](looks)
* [Sound](sound)
* [Control](control)
* [Sensing](sensing)
* [Operators](operators)
* [Variables and Lists](variables-and-lists)
* [Messages](messages)
* [Pen](pen)
* [Costumes, Sounds, and Names](costumes-sounds-and-names)
'@ | Set-Content -Path (Join-Path $WikiDir "_Sidebar.md") -Encoding utf8

Push-Location $WikiDir
try {
    Copy-Item -Path (Join-Path $source "README.md") -Destination (Join-Path $WikiDir "Home.md") -Force
    git add -A
    git diff --cached --stat
    if ($Push) {
        if (-not (git diff --cached --quiet)) {
            git commit -m "Update Kitty documentation"
        }
        git push origin HEAD
    } else {
        Write-Host "Wiki staged in $WikiDir"
        Write-Host "Review with: git diff --cached"
        Write-Host "Publish with: git commit -m 'Update Kitty documentation'; git push origin master"
    }
} finally {
    Pop-Location
}
