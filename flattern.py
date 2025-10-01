#!/usr/bin/env python3
import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Set

DEFAULT_EXTS = [
    ".py", ".cs", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".cpp", ".c", ".h", ".hpp",
    ".html", ".htm", ".css",
    ".json", ".yaml", ".yml", ".md", ".txt",
    ".sql", ".go", ".rs", ".php",
    ".sh", ".bash", ".zsh", ".bat", ".cmd", ".ps1",
]

DEFAULT_EXCLUDES = {
    "node_modules", ".git", ".venv", ".idea", ".vscode", "dist", "build",
    "__pycache__", ".mypy_cache", ".pytest_cache", "bin", "obj", "target",
    ".next", "out", ".turbo", "coverage", ".gradle", ".cache", "vendor",
    "TestResults",
}

SEPARATOR = "\n\n===== FILE: {relpath} =====\n\n"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Flatten source files into paste friendly chunks."
    )
    p.add_argument("--root", default=".", help="Root directory to scan.")
    p.add_argument(
        "--exts",
        default=",".join(DEFAULT_EXTS),
        help="Comma separated list of file extensions to include, e.g. .py,.cs",
    )
    p.add_argument(
        "--exclude-dir",
        default=",".join(DEFAULT_EXCLUDES),
        help="Comma separated directory names to exclude.",
    )
    p.add_argument("--strip-comments", action="store_true", help="Strip comments.")
    p.add_argument("--strip-py-docstrings", action="store_true", help="Remove Python docstrings.")
    p.add_argument("--tab-spaces", type=int, default=2, help="Spaces per tab.")
    p.add_argument("--collapse-blank-to", type=int, default=1, help="Max consecutive blank lines.")
    p.add_argument("--max-mb", type=float, default=0.0, help="Skip files larger than this size in MB.")
    p.add_argument("--chunk-chars", type=int, default=13000, help="Max chars per chunk.")
    p.add_argument(
        "--out-dir",
        default=".",
        help="Directory to write output files. Defaults to the current working directory.",
    )
    p.add_argument("--prefix", default="output", help="Prefix for output files.")
    return p.parse_args()


def find_files(root: Path, exts: Set[str], exclude_dirs: Set[str]) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for fname in filenames:
            p = Path(dirpath, fname)
            if p.suffix.lower() in exts:
                yield p


def normalise_whitespace(text: str, tab_spaces: int = 2, collapse_blank_to: int = 1) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.expandtabs(tab_spaces)
    lines = [ln.rstrip() for ln in text.split("\n")]
    collapsed: List[str] = []
    blank_run = 0
    for ln in lines:
        if ln == "":
            blank_run += 1
            if blank_run <= collapse_blank_to:
                collapsed.append("")
        else:
            blank_run = 0
            collapsed.append(ln)
    out = "\n".join(collapsed).strip()
    return (out + "\n") if out else ""


def strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def strip_c_like_comments(text: str) -> str:
    out, i, n = [], 0, len(text)
    in_line, in_block, in_str, in_char, escape, quote = False, False, False, False, False, ""
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if in_line:
            if ch == "\n":
                in_line = False
                out.append(ch)
            i += 1
            continue
        if in_block:
            if ch == "*" and nxt == "/":
                in_block = False
                i += 2
            else:
                i += 1
            continue
        if in_str or in_char:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif in_str and ch == quote:
                in_str = False
            elif in_char and ch == "'":
                in_char = False
            i += 1
            continue
        if ch == "/" and nxt == "/":
            in_line = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block = True
            i += 2
            continue
        if ch in ('"', "`"):
            in_str, quote = True, ch
            out.append(ch)
            i += 1
            continue
        if ch == "'":
            in_char = True
            out.append(ch)
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def strip_sql_comments(text: str) -> str:
    # Handle -- line comments and /* ... */ blocks, keep quoted strings intact.
    out = []
    i, n = 0, len(text)
    in_block = False
    in_str = False
    quote = ""
    escape = False
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if in_block:
            if ch == "*" and nxt == "/":
                in_block = False
                i += 2
            else:
                i += 1
            continue

        if in_str:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_str = False
            i += 1
            continue

        # not in string or block comment
        if ch in ("'", '"'):
            in_str = True
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "*":
            in_block = True
            i += 2
            continue
        if ch == "-" and nxt == "-":
            while i < n and text[i] != "\n":
                i += 1
            continue

        out.append(ch)
        i += 1
    return "".join(out)


def strip_hash_line_comments(text: str) -> str:
    # For languages where # starts a comment to end of line, outside strings.
    out_lines = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        buf = []
        i, in_str, quote, escape = 0, False, "", False
        while i < len(line):
            ch = line[i]
            if in_str:
                buf.append(ch)
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == quote:
                    in_str = False
                i += 1
                continue
            if ch in ("'", '"'):
                in_str, quote = True, ch
                buf.append(ch)
                i += 1
                continue
            if ch == "#":
                break
            buf.append(ch)
            i += 1
        out_lines.append("".join(buf))
    return "\n".join(out_lines)


def strip_python_comments(text: str, strip_docstrings: bool) -> str:
    s = text.replace("\r\n", "\n").replace("\r", "\n")
    out_lines: List[str] = []
    in_triple, triple_quote = False, ""
    for line in s.split("\n"):
        if strip_docstrings:
            if in_triple:
                if triple_quote in line:
                    end_idx = line.find(triple_quote)
                    line = line[end_idx + 3 :]
                    in_triple = False
                else:
                    continue
            for q in ("'''", '"""'):
                idx = line.find(q)
                if idx != -1:
                    in_triple, triple_quote, line = True, q, line[:idx]
                    break
        i, in_str, quote, escape, buf = 0, False, "", False, []
        while i < len(line):
            ch = line[i]
            if in_str:
                buf.append(ch)
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == quote:
                    in_str = False
                i += 1
                continue
            if ch in ("'", '"'):
                in_str, quote = True, ch
                buf.append(ch)
                i += 1
                continue
            if ch == "#":
                break
            buf.append(ch)
            i += 1
        out_lines.append("".join(buf))
    return "\n".join(out_lines)


def process_content(text: str, ext: str, strip_comments: bool, strip_py_docstrings: bool) -> str:
    if not strip_comments:
        return text
    e = ext.lower()
    if e == ".py":
        return strip_python_comments(text, strip_docstrings=strip_py_docstrings)
    if e in {".html", ".htm", ".md"}:
        return strip_html_comments(text)
    if e == ".sql":
        return strip_sql_comments(text)
    if e in {".sh", ".bash", ".zsh", ".ps1"}:
        return strip_hash_line_comments(text)
    if e in {".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".css", ".php", ".rs", ".go"}:
        s = strip_c_like_comments(text)
        if e == ".php":
            s = strip_hash_line_comments(s)
        return s
    return text


def should_skip_file(p: Path, max_mb: float) -> bool:
    if max_mb <= 0:
        return False
    try:
        return p.stat().st_size > max_mb * 1024 * 1024
    except OSError:
        return False


def chunk_text(text: str, max_chunk_chars: int) -> List[str]:
    if max_chunk_chars <= 0 or len(text) <= max_chunk_chars:
        return [text] if text else []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + max_chunk_chars, len(text))
        if end < len(text):
            split_pos = text.rfind("\n===== FILE:", start, end)
            if split_pos == -1 or split_pos <= start:
                split_pos = text.rfind("\n\n", start, end)
                if split_pos == -1 or split_pos <= start:
                    split_pos = end
            end = split_pos
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk + "\n")
        start = end
    return chunks


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    exts = {e.strip().lower() for e in args.exts.split(",") if e.strip()}
    exclude_dirs = {e.strip() for e in args.exclude_dir.split(",") if e.strip()}

    if not root.exists():
        print(f"Root does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    files = sorted(find_files(root, exts, exclude_dirs))
    collected_parts: List[str] = []
    for p in files:
        if should_skip_file(p, args.max_mb):
            continue
        try:
            raw = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        processed = process_content(raw, p.suffix, args.strip_comments, args.strip_p y_docstrings)  # noqa: E501
        normalised = normalise_whitespace(processed, args.tab_spaces, args.collapse_blank_to)
        if not normalised:
            continue
        relpath = p.relative_to(root)
        header = SEPARATOR.format(relpath=str(relpath).replace("\\", "/"))
        collected_parts.append(header + normalised)

    combined = "".join(collected_parts).strip() + ("\n" if collected_parts else "")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not combined:
        print("No content matched the filters. Nothing written.", file=sys.stderr)
        return

    chunks = chunk_text(combined, args.chunk_chars)
    if len(chunks) == 1:
        out_path = out_dir / f"{args.prefix}.txt"
        out_path.write_text(chunks[0], encoding="utf-8")
        print(f"Wrote {out_path}")
    else:
        width = max(3, len(str(len(chunks))))
        for i, chunk in enumerate(chunks, start=1):
            out_path = out_dir / f"{args.prefix}_part{str(i).zfill(width)}.txt"
            out_path.write_text(chunk, encoding="utf-8")
            print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
