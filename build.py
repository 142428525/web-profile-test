#!/usr/bin/env python3
"""使用 Jinja2 模板和环境变量构建个人主页。

公开模板只包含占位符；真实姓名、邮箱、学校等信息由环境变量或可选的
.env 文件提供。渲染后的完整站点写入 dist/，其中可能包含联系方式，
因此 dist/ 与 .env 都被 .gitignore 忽略，禁止提交到公开仓库。

用法：
    python build.py

环境变量优先于 .env；至少需要配置 AUTHOR_NAME、CONTACT_EMAIL、
GITHUB_USER、GITHUB_REPO、SITE_TITLE、SITE_SUBTITLE、SCHOOL、MAJOR、GRADE。
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Dict, Iterable

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
DIST = ROOT / "dist"
SUBMISSION = DIST / "submission"

REQUIRED = (
    "AUTHOR_NAME",
    "CONTACT_EMAIL",
    "GITHUB_USER",
    "GITHUB_REPO",
    "SITE_TITLE",
    "SITE_SUBTITLE",
    "SCHOOL",
    "MAJOR",
    "GRADE",
)

PUBLIC_FILES = (
    "README.md",
    ".env.example",
    "build.py",
    "requirements.txt",
)
PUBLIC_DIRS = (
    "templates",
    ".github",
)

PLACEHOLDERS = {
    "AUTHOR_NAME": {"", "你的名字", "your-name"},
    "CONTACT_EMAIL": {"", "you@example.com", "someone@example.com"},
    "GITHUB_USER": {"", "your-github-username"},
    "GITHUB_REPO": {"", "your-repo-name"},
    "SCHOOL": {"", "你的学校", "your-school"},
    "MAJOR": {"", "你的专业", "your-major"},
}

SCAN_SUFFIXES = {".html", ".htm", ".css", ".js", ".md", ".yml", ".yaml", ".py", ".txt", ".json"}


def read_dotenv(path: Path) -> Dict[str, str]:
    """读取简单的 KEY=VALUE 文件；缺少文件时返回空字典。"""
    values: Dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        values[key] = value
    return values


def collect_values() -> Dict[str, str]:
    values = read_dotenv(ROOT / ".env")
    for key, value in os.environ.items():
        if key in values or key in REQUIRED or key in {"PAGES_URL", "REPO_URL", "LAST_UPDATED"}:
            values[key] = value
    for key in REQUIRED:
        values.setdefault(key, "")
    values.setdefault("PAGES_URL", "")
    values.setdefault("REPO_URL", "")
    values.setdefault("LAST_UPDATED", date.today().isoformat())
    if not values["REPO_URL"]:
        values["REPO_URL"] = (
            f"https://github.com/{values['GITHUB_USER']}/{values['GITHUB_REPO']}"
        )
    year = values["LAST_UPDATED"][:4]
    values["BUILD_YEAR"] = year if year.isdigit() else str(date.today().year)
    return values


def validate_values(values: Dict[str, str]) -> None:
    problems: list[str] = []
    for key in REQUIRED:
        if not values.get(key):
            problems.append(f"缺少 {key}")
    for key, bad in PLACEHOLDERS.items():
        if values.get(key) in bad:
            problems.append(f"{key} 仍是占位符：{values.get(key)!r}")
    if problems:
        print("构建前请先配置真实信息：", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print("可复制 .env.example 为 .env 并填写，或直接设置同名环境变量。", file=sys.stderr)
        raise SystemExit(2)


def scan_file(path: Path, secrets: Iterable[str]) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    hits: list[str] = []
    for secret in secrets:
        if secret and secret in text:
            hits.append(f"{path.relative_to(ROOT)} 包含真实隐私值 {secret!r}")
    return hits


def privacy_check(values: Dict[str, str]) -> None:
    secrets = [values["AUTHOR_NAME"], values["CONTACT_EMAIL"], values["SCHOOL"]]
    secrets = [secret for secret in secrets if len(secret) >= 3]
    hits: list[str] = []
    for rel in PUBLIC_FILES:
        path = ROOT / rel
        if path.is_file():
            hits.extend(scan_file(path, secrets))
    for rel in PUBLIC_DIRS:
        path = ROOT / rel
        if path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and child.suffix.lower() in SCAN_SUFFIXES:
                    hits.extend(scan_file(child, secrets))
    if hits:
        print("隐私检查失败：以下公开文件包含真实隐私值：", file=sys.stderr)
        for hit in hits:
            print(f"  - {hit}", file=sys.stderr)
        raise SystemExit(3)
    print("隐私检查：公开模板与 README 未包含真实姓名/邮箱/学校。")


def build_environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        undefined=StrictUndefined,
        autoescape=select_autoescape(("html", "htm", "xml")),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def render(env: Environment, name: str, **extra: object) -> str:
    return env.get_template(name).render(**extra)


def file_block(name: str, content: str) -> str:
    if "-->" in content:
        raise SystemExit(
            f"{name} 含有 HTML 注释结束符 '-->'，无法安全内嵌；"
            "请把该字符串改成等价写法后再构建。"
        )
    return (
        "<!--\n"
        f"==================== FILE: {name} ====================\n"
        f"{content.rstrip()}\n"
        f"==================== END FILE: {name} ====================\n"
        "-->\n"
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def find_unresolved(text: str) -> list[str]:
    return re.findall(r"\{\{.*?\}\}|\{%.*?%\}", text)


def main() -> int:
    values = collect_values()
    validate_values(values)
    privacy_check(values)

    env = build_environment()
    style_css = render(env, "style.css", **values)
    script_js = render(env, "script.js", **values)
    common = {"inline_assets": False, "style_css": style_css, "script_js": script_js, **values}

    pages = {
        "index.html": render(env, "index.html", **common),
        "learn.html": render(env, "learn.html", **common),
        "projects.html": render(env, "projects.html", **common),
    }
    index_inline = render(
        env,
        "index.html",
        **{**common, "inline_assets": True},
    )
    manifest = render(env, "submission_manifest.html", **values).strip()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    if DIST.exists():
        shutil.rmtree(DIST)
    SUBMISSION.mkdir(parents=True, exist_ok=True)

    for name, content in pages.items():
        write(DIST / name, content)
    write(DIST / "style.css", style_css)
    write(DIST / "script.js", script_js)
    write(DIST / "README.md", readme)

    submission = index_inline
    charset = '<meta charset="UTF-8">'
    if charset in submission:
        submission = submission.replace(charset, charset + "\n" + manifest, 1)
    elif "<head>" in submission:
        submission = submission.replace("<head>", "<head>\n" + manifest, 1)
    else:
        raise SystemExit("index.html 中找不到 charset 或 <head>，无法插入提交说明。")

    embedded = "\n".join(
        [
            file_block("learn.html", pages["learn.html"]),
            file_block("projects.html", pages["projects.html"]),
            file_block("README.md", readme),
        ]
    )
    if "</body>" not in submission:
        raise SystemExit("index.html 中找不到 </body>，无法插入内嵌文件。")
    submission = submission.replace("</body>", embedded + "\n</body>", 1)
    write(SUBMISSION / "index.html", submission)

    for name, content in [
        *pages.items(),
        ("style.css", style_css),
        ("script.js", script_js),
        ("submission/index.html", submission),
    ]:
        unresolved = find_unresolved(content)
        if unresolved:
            raise SystemExit(f"{name} 仍有未解析的模板标记：{unresolved[:3]}")

    print(f"构建完成：{DIST}")
    print("  - 站点：index.html / learn.html / projects.html")
    print("  - 资源：style.css / script.js / README.md")
    print(f"  - 提交包：dist/submission/index.html（{len(submission.encode('utf-8'))} 字节）")
    print(f"  - 仓库：{values['REPO_URL']}")
    if values["PAGES_URL"]:
        print(f"  - 线上：{values['PAGES_URL']}")
    else:
        print("  - 线上：未配置 PAGES_URL（GitHub Pages 属鼓励项，非强制）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
