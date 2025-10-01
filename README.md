# Code Flattener

Flatten, strip, and chunk source code files for easier review, analysis, or pasting into AI tools. This utility walks a project, collects files with selected extensions, removes comments where safe, normalises whitespace, and writes paste-friendly chunks. It is dependency free.

## Description

**Code Flattener** is a lightweight Python utility that helps you prepare large or multi-language codebases for sharing or analysis. It:

* Recursively scans project directories.
* Includes only the file extensions you specify.
* Excludes noisy directories like `node_modules`, `dist`, `build`, etc.
* Strips comments (with language-specific handling).
* Optionally strips Python docstrings.
* Normalises whitespace.
* Splits output into chunked files to respect paste or token limits.

Outputs are written as plain `.txt` files either to the current working directory or to a path you specify.

## Install

Use Python 3.8 or newer. No external packages required.

```
python flatten.py --help
```

## Output location

* By default, files are written to the current working directory.
* Use `--out-dir` to set a specific folder (absolute or relative).

Examples:

```
python flatten.py --root . --exts .py --strip-comments
python flatten.py --root . --exts .py --strip-comments --out-dir output/exports
python flatten.py --root . --exts .py --strip-comments --out-dir /tmp/exports
```

## Key flags

* `--root` directory to scan.
* `--exts` comma separated extensions, for example `.py,.cs`.
* `--exclude-dir` directory names to ignore.
* `--strip-comments` enable comment removal.
* `--strip-py-docstrings` remove Python docstrings.
* `--tab-spaces` convert tabs to spaces.
* `--collapse-blank-to` maximum consecutive blank lines.
* `--max-mb` skip files larger than this size in MB.
* `--chunk-chars` maximum characters per output chunk.
* `--out-dir` directory for outputs.
* `--prefix` filename prefix for outputs.

## Presets

Ready-to-use presets for different languages:

### Python

```
python flatten.py --root . --exts .py --exclude-dir .git,.venv,__pycache__,.mypy_cache,.pytest_cache \
  --strip-comments --strip-py-docstrings \
  --tab-spaces 4 --collapse-blank-to 1 --max-mb 1.5 \
  --chunk-chars 13000 --out-dir . --prefix python_flat
```

### C#

```
python flatten.py --root . --exts .cs,.csproj \
  --exclude-dir .git,.idea,.vscode,bin,obj,TestResults,packages \
  --strip-comments --tab-spaces 4 --collapse-blank-to 1 --max-mb 2 \
  --chunk-chars 13000 --out-dir . --prefix csharp_flat
```

### JavaScript & TypeScript

```
python flatten.py --root . --exts .js,.jsx,.ts,.tsx \
  --exclude-dir node_modules,.git,.vscode,dist,build,.next,out,.turbo,coverage \
  --strip-comments --tab-spaces 2 --collapse-blank-to 1 --max-mb 1.5 \
  --chunk-chars 13000 --out-dir . --prefix tsjs_flat
```

### Java

```
python flatten.py --root . --exts .java \
  --exclude-dir .git,.idea,.vscode,target,build,out,.gradle \
  --strip-comments --tab-spaces 4 --collapse-blank-to 1 --max-mb 2 \
  --chunk-chars 13000 --out-dir . --prefix java_flat
```

### C and C++

```
python flatten.py --root . --exts .c,.cpp,.h,.hpp \
  --exclude-dir .git,.vscode,build,cmake-build-debug,cmake-build-release,.cache \
  --strip-comments --tab-spaces 4 --collapse-blank-to 1 --max-mb 1.5 \
  --chunk-chars 12000 --out-dir . --prefix cpp_flat
```

### HTML and CSS

```
python flatten.py --root . --exts .html,.htm,.css \
  --exclude-dir .git,dist,build,.next,out \
  --strip-comments --tab-spaces 2 --collapse-blank-to 1 --max-mb 1 \
  --chunk-chars 12000 --out-dir . --prefix htmlcss_flat
```

### JSON and YAML

```
python flatten.py --root . --exts .json,.yaml,.yml \
  --exclude-dir .git,node_modules,dist,build \
  --tab-spaces 2 --collapse-blank-to 1 --max-mb 0.8 \
  --chunk-chars 11000 --out-dir . --prefix config_flat
```

### Markdown and Text

```
python flatten.py --root . --exts .md,.txt \
  --exclude-dir .git,.obsidian,.vitepress,.docusaurus,build,dist \
  --strip-comments --tab-spaces 2 --collapse-blank-to 1 --max-mb 1 \
  --chunk-chars 12000 --out-dir . --prefix docs_flat
```

### Shell, Batch, PowerShell

```
python flatten.py --root . --exts .sh,.bash,.zsh,.bat,.cmd,.ps1 \
  --exclude-dir .git,.venv,node_modules,dist,build \
  --strip-comments --tab-spaces 2 --collapse-blank-to 1 --max-mb 0.5 \
  --chunk-chars 10000 --out-dir . --prefix scripts_flat
```

### Go

```
python flatten.py --root . --exts .go \
  --exclude-dir .git,bin,dist,build,vendor \
  --strip-comments --tab-spaces 4 --collapse-blank-to 1 --max-mb 1.5 \
  --chunk-chars 12000 --out-dir . --prefix go_flat
```

### Rust

```
python flatten.py --root . --exts .rs \
  --exclude-dir .git,target \
  --strip-comments --tab-spaces 4 --collapse-blank-to 1 --max-mb 1.2 \
  --chunk-chars 12000 --out-dir . --prefix rust_flat
```

### PHP

```
python flatten.py --root . --exts .php \
  --exclude-dir .git,vendor,storage,cache,build,dist \
  --strip-comments --tab-spaces 4 --collapse-blank-to 1 --max-mb 1.5 \
  --chunk-chars 12000 --out-dir . --prefix php_flat
```

### SQL

```
python flatten.py --root . --exts .sql \
  --exclude-dir .git,build,dist \
  --strip-comments --tab-spaces 2 --collapse-blank-to 1 --max-mb 1 \
  --chunk-chars 12000 --out-dir . --prefix sql_flat
```

### Mixed monorepo

```
python flatten.py --root . --exts .py,.cs,.js,.jsx,.ts,.tsx,.java,.go,.rs,.php,.c,.cpp,.h,.hpp,.html,.htm,.css \
  --exclude-dir node_modules,.git,.venv,__pycache__,dist,build,.next,out,.turbo,coverage,bin,obj,target,vendor \
  --strip-comments --strip-py-docstrings \
  --tab-spaces 2 --collapse-blank-to 1 --max-mb 1.5 \
  --chunk-chars 13000 --out-dir . --prefix monorepo_flat
```

## Behaviour

* Output files are written to `--out-dir` (default: current directory).
* Large outputs are chunked to respect `--chunk-chars`.
* Comment stripping preserves strings/char literals.
* JSON/YAML remain unchanged.

## Tips

* Raise `--chunk-chars` if your paste target supports larger sizes.
* Keep licence headers by exporting without `--strip-comments`.

## Summary

**Code Flattener** is a simple, flexible way to export large, multi-language codebases into a clean text format for analysis or sharing.
