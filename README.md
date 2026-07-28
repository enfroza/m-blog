# My Blog (Netlify-ready)

Static blog you can host for free on **Netlify**.

## Features

- Admin panel to create & edit posts (`/admin/`)
- Add images / media to posts
- Every post becomes its own page (`/posts/my-post/`)
- Markdown support
- Dark modern design

## Deploy to Netlify (5 minutes)

1. **Push this folder to GitHub** (create a new repo and upload these files)

2. Go to [https://app.netlify.com](https://app.netlify.com) → **Add new site** → **Import an existing project**

3. Connect your GitHub repo

4. Netlify will detect `netlify.toml` automatically.  
   Build command and publish folder are already set.

5. Click **Deploy site**

### Enable Admin login (Netlify Identity)

1. In Netlify dashboard → **Identity** → **Enable Identity**
2. Under **Registration** → set to **Invite only** (recommended)
3. **Services** → **Git Gateway** → **Enable Git Gateway**
4. Invite yourself: Identity → Invite users → enter your email
5. Open `https://YOUR-SITE.netlify.app/admin/` and log in

Now you can create, edit, and publish posts from the browser. Media uploads go into the repo automatically.

## Local preview

```bash
pip install -r requirements.txt
python build.py
```

Then open the `dist/` folder with any static server, e.g.:

```bash
cd dist && python -m http.server 8080
```

Visit http://localhost:8080

## Project structure

```
├── content/posts/     ← Markdown posts (edit here or via /admin)
├── static/            ← CSS + uploaded media
├── templates/         ← HTML templates
├── admin/             ← Decap CMS (the admin UI)
├── build.py           ← generates the static site
├── netlify.toml       ← Netlify config
└── dist/              ← output (do not edit, generated on build)
```

## Adding posts without the admin UI

Create a file in `content/posts/my-post.md`:

```markdown
---
title: My Post Title
slug: my-post
date: 2026-07-28
published: true
media: photo.jpg
---

Your content in **Markdown** here.
```

Put images in `static/uploads/`. Then run `python build.py` (or just push — Netlify rebuilds automatically).
