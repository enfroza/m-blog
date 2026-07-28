#!/usr/bin/env python3
"""
Static site generator for the blog.
Reads Markdown posts from content/posts/ and outputs pure HTML to dist/.
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension

ROOT = Path(__file__).parent
CONTENT = ROOT / "content" / "posts"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
DIST = ROOT / "dist"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:80] or "post"


def parse_frontmatter(raw: str) -> tuple:
    """Simple frontmatter parser that also handles basic YAML lists."""
    meta = {}
    body = raw
    if not raw.startswith("---"):
        return meta, body

    parts = raw.split("---", 2)
    if len(parts) < 3:
        return meta, body

    fm = parts[1].strip()
    body = parts[2].strip()

    current_list_key = None
    for line in fm.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # List item: "  - value" or "  - /uploads/foo.jpg"
        if stripped.startswith("- ") and current_list_key:
            val = stripped[2:].strip().strip("'").strip('"')
            meta.setdefault(current_list_key, []).append(val)
            continue

        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")

            if val == "" or val == "[]":
                # Start of a list (or empty)
                current_list_key = key
                meta[key] = []
            else:
                current_list_key = None
                if val.lower() in ("true", "yes"):
                    val = True
                elif val.lower() in ("false", "no"):
                    val = False
                meta[key] = val
        else:
            current_list_key = None

    return meta, body


def load_posts() -> list:
    posts = []
    if not CONTENT.exists():
        return posts

    for path in sorted(CONTENT.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)

        title = meta.get("title") or path.stem.replace("-", " ").title()
        slug = meta.get("slug") or slugify(title)
        date = meta.get("date") or datetime.now().strftime("%Y-%m-%d")
        published = meta.get("published", True)
        if isinstance(published, str):
            published = published.lower() not in ("false", "no", "0")

        media_raw = meta.get("media", "") or ""
        media = []
        if isinstance(media_raw, list):
            for m in media_raw:
                if isinstance(m, dict):
                    # Decap list-of-objects: {image: /uploads/foo.jpg}
                    m = m.get("image") or m.get("file") or next(iter(m.values()), "")
                m = str(m).strip()
                if m:
                    media.append(m)
        else:
            for m in str(media_raw).strip("[] ").split(","):
                m = m.strip().strip("'").strip('"')
                if m:
                    media.append(m)

        # Normalize: Decap may store /uploads/name.jpg
        media = [m.replace("/uploads/", "").lstrip("/") for m in media]

        html_body = markdown.markdown(
            body,
            extensions=[FencedCodeExtension(), TableExtension(), "nl2br"],
        )

        posts.append({
            "title": title,
            "slug": slug,
            "date": date,
            "published": published,
            "media": media,
            "content_html": html_body,
            "excerpt": re.sub(r"<[^>]+>", "", html_body)[:180].strip(),
            "source": path.name,
        })

    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def render(template_name: str, **ctx) -> str:
    tpl = (TEMPLATES / template_name).read_text(encoding="utf-8")
    for key, val in ctx.items():
        if isinstance(val, str):
            tpl = tpl.replace("{{ " + key + " }}", val)
            tpl = tpl.replace("{{" + key + "}}", val)
    return tpl


def build_index(posts: list):
    published = [p for p in posts if p["published"]]
    cards = []
    for p in published:
        cards.append(f"""
        <article class="post-card">
            <h2><a href="/posts/{p['slug']}/">{p['title']}</a></h2>
            <time datetime="{p['date']}">{p['date']}</time>
            <p class="excerpt">{p['excerpt']}{'…' if len(p['excerpt']) >= 170 else ''}</p>
            <a href="/posts/{p['slug']}/" class="read-more">Read more →</a>
        </article>
        """)
    cards_html = "\n".join(cards) if cards else '<p class="empty">No posts yet.</p>'

    html = render(
        "index.html",
        title="Home — My Blog",
        posts_html=cards_html,
        year=str(datetime.now().year),
    )
    (DIST / "index.html").write_text(html, encoding="utf-8")


def build_post(post: dict):
    media_html = ""
    if post["media"]:
        parts = []
        for m in post["media"]:
            ext = m.rsplit(".", 1)[-1].lower()
            src = f"/uploads/{m}"
            if ext in ("png", "jpg", "jpeg", "gif", "webp"):
                parts.append(f'<figure><img src="{src}" alt="{post["title"]}"></figure>')
            elif ext in ("mp4", "webm"):
                parts.append(f'<figure><video controls src="{src}"></video></figure>')
            elif ext == "pdf":
                parts.append(f'<p><a href="{src}" target="_blank" class="btn">View PDF</a></p>')
        media_html = f'<div class="post-media">{"".join(parts)}</div>'

    html = render(
        "post.html",
        title=f"{post['title']} — My Blog",
        post_title=post["title"],
        post_date=post["date"],
        post_media=media_html,
        post_content=post["content_html"],
        year=str(datetime.now().year),
    )
    out_dir = DIST / "posts" / post["slug"]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    if STATIC.exists():
        for item in STATIC.iterdir():
            dest = DIST / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

    admin_src = ROOT / "admin"
    if admin_src.exists():
        shutil.copytree(admin_src, DIST / "admin")

    posts = load_posts()
    build_index(posts)

    for post in posts:
        if post["published"]:
            build_post(post)

    html_404 = render("404.html", title="Not Found — My Blog", year=str(datetime.now().year))
    (DIST / "404.html").write_text(html_404, encoding="utf-8")

    print(f"Built {len([p for p in posts if p['published']])} published post(s) → dist/")


if __name__ == "__main__":
    build()
