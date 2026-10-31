"""Render the README, project notes and theme-aware SVG cards from local data."""

from datetime import datetime
from html import escape

from common import ROOT, read_json

PALETTES = {
    "dark": {"bg": "#17212C", "panel": "#202E3B", "ink": "#EDF4FF", "muted": "#A8B8CB", "accent": "#C5B8DC", "line": "#41566D"},
    "light": {"bg": "#EDF2F6", "panel": "#DDE6EE", "ink": "#283C51", "muted": "#536C83", "accent": "#77638B", "line": "#B8C9D8"},
}


def rect(x, y, w, h, fill, radius=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}"/>'


def text(x, y, value, size, fill, extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" {extra}>{escape(str(value))}</text>'


def save_svg(base, theme, width, height, body, title, background=True):
    palette = PALETTES[theme]
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title" font-family="ui-monospace,Consolas,monospace"><title id="title">{escape(title)}</title>'
    if background:
        svg += rect(0, 0, width, height, palette["bg"], 8)
    svg += body + "</svg>\n"
    (ROOT / f"assets/{base}-{theme}.svg").write_text(svg, encoding="utf-8")


def picture(base, alt, width=760):
    alt = escape(alt, quote=True)
    return f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="assets/{base}-dark.svg">\n  <source media="(prefers-color-scheme: light)" srcset="assets/{base}-light.svg">\n  <img src="assets/{base}-light.svg" alt="{alt}" width="{width}">\n</picture>'


def heading(base, alt):
    return "<h2>\n" + picture(base, alt, 280) + "\n</h2>"


def md(value):
    return str(value).replace("\n", " ").replace("[", "\\[").replace("]", "\\]").replace("|", "\\|")


def render_terminal(theme):
    p = PALETTES[theme]
    body = rect(0, 0, 760, 34, p["panel"], 8)
    for x, color in [(17, "#DC9C9F"), (31, "#E4CF99"), (45, "#A2C7B0")]:
        body += f'<circle cx="{x}" cy="17" r="4" fill="{color}"/>'
    body += text(70, 22, "john@github: ~/workbench", 12, p["muted"])
    body += text(24, 70, "$ whoami", 16, p["accent"])
    body += text(24, 103, "Nhat Nguyen / John", 24, p["ink"])
    body += text(24, 133, "Computer Science / Swinburne Vietnam", 15, p["muted"])
    body += text(24, 174, "$ cat focus.txt", 16, p["accent"])
    body += text(24, 205, "Web interfaces. Data exploration. Small ideas.", 15, p["ink"])
    save_svg("terminal", theme, 760, 232, body, "John's terminal introduction and focus")


def render_stats(data, theme):
    p = PALETTES[theme]
    body = text(24, 31, f"GITHUB / LAST {data['days']} DAYS", 13, p["accent"])
    stats = data["stats"]
    fields = [("Repo stars / total", stats["stars"]), ("Commits / selected scope", stats["commits"]), ("Public PRs opened", stats["pull_requests"]),
              ("Public issues opened", stats["issues"]), ("Lines added (+)", stats["added"]), ("Lines deleted (-)", stats["deleted"])]
    for index, (label, value) in enumerate(fields):
        x, y = 24 + index % 3 * 248, 52 + index // 3 * 88
        body += rect(x, y, 232, 73, p["panel"], 5)
        body += text(x + 12, y + 22, label, 11, p["muted"])
        display = f"{value:,}" if value is not None else "pending"
        if label.startswith("Lines") and value is not None:
            display = ("+" if "added" in label else "-") + display
        body += text(x + 12, y + 56, display, 28, p["ink"])
    body += text(24, 252, "Updated " + data["updated_at"][:16].replace("T", " ") + " UTC", 11, p["muted"])
    save_svg("github-stats", theme, 792, 273, body, "GitHub metrics with explicit scope; line changes are not proficiency")


def render_languages(data, theme):
    p = PALETTES[theme]
    values = data["languages"]
    total = sum(values.values())
    top = list(values.items())[:7]
    height = 100 + len(top) * 42
    body = text(24, 31, "LANGUAGES / REPOSITORY BYTES", 13, p["accent"])
    colors = ["#94B9E4", "#D8C281", "#A4C5A2", "#D79C8C", "#BCA1D2", "#9DC9CA", "#C4B8A9"]
    for index, (name, amount) in enumerate(top):
        percentage = amount / total * 100 if total else 0
        y = 66 + index * 42
        body += text(24, y, name, 14, p["ink"])
        body += text(736, y, f"{percentage:.1f}%", 13, p["muted"], 'text-anchor="end"')
        body += rect(24, y + 8, 712, 5, p["panel"], 2)
        body += rect(24, y + 8, 712 * percentage / 100, 5, colors[index], 2)
    body += text(24, height - 18, "Code composition, not a proficiency rating.", 11, p["muted"])
    save_svg("code-languages", theme, 760, height, body, "Programming language proportions from selected repositories")


def render_music(data, theme):
    p = PALETTES[theme]
    body = text(24, 31, data["provider"].upper() + " / LISTENING SNAPSHOT", 12, p["accent"])
    state = "Playing at the last check" if data.get("playing") else "No active playback at the last check"
    if data.get("track") and not data.get("playing"):
        state = "Most recently recorded track" if data.get("last_recorded") else "Paused at the last check"
    body += text(24, 64, state, 14, p["muted"])
    body += text(24, 101, data.get("track", "No track available")[:64], 23, p["ink"])
    body += text(24, 129, data.get("artist", "")[:80], 14, p["muted"])
    body += text(24, 172, "TOP 5 ARTISTS / " + data["period"], 12, p["accent"])
    for index, artist in enumerate(data.get("top_artists", [])[:5]):
        body += text(24, 206 + index * 30, f"0{index + 1}  " + artist["name"][:70], 16, p["ink"])
    body += text(24, 374, "Checked " + data["updated_at"][:16].replace("T", " ") + " UTC / not a live stream", 10, p["muted"])
    save_svg("music", theme, 760, 397, body, "Music playback snapshot and top five artists")


def render_project_notes(projects):
    for project in projects:
        lines = [f"# {project['title']}", "", "[Back to my profile](../../README.md)", "", "## Introduction", "", project["introduction"],
                 "", "## Problem", "", project["problem"], "", "## My role", "", project["role"], "", "## Main features", ""]
        lines += ["- " + item for item in project["features"]]
        lines += ["", "## Stack", "", ", ".join(project["stack"]), "", "## Demo or walkthrough", ""]
        if project.get("demo"):
            lines += [f"[Open the demo]({project['demo']})", "", "This is the deployment linked by the project repository. Its current availability has not been re-tested for this profile release."]
        else:
            lines += [f"[Open the repository and run instructions]({project['repo']})", "", "No verified public demo is linked for this project."]
        lines += ["", "## Learning focus", "", "These notes describe the concepts I am practising in the implementation.", ""]
        lines += ["- " + item for item in project["learningFocus"]]
        lines += ["", "## Status and outcome", "", "**" + project["status"] + "**", "", project["outcome"], "", "## Limits", ""]
        lines += ["- " + item for item in project["limits"]]
        lines += ["", "## Source", "", f"[Repository]({project['repo']}) - [Project README]({project['evidence']})", ""]
        (ROOT / f"docs/projects/{project['id']}.md").write_text("\n".join(lines).replace("I’m", "I'm").replace("–", "-").replace("—", "-"), encoding="utf-8")


def build():
    projects = read_json("data/projects.json")
    github = read_json("data/github.json")
    music = read_json("data/music.json")
    for theme in PALETTES:
        render_terminal(theme)
        if github:
            render_stats(github, theme)
            render_languages(github, theme)
        if music:
            render_music(music, theme)
    render_project_notes(projects)
    parts = ["<!-- Generated by tools/build_profile.py; edit the data and generator to keep automatic updates consistent. -->", "", picture("scene", "John / Nhat Nguyen. Small ideas. Built with care. My orange tabby cat sits beside the monitor.", 960),
             "", heading("about", "自己紹介 / About me"), "", "I'm **Nhat Nguyen (John)**, a Computer Science student at **Swinburne Vietnam**, with a minor in **Data Science**.",
             "", "I build web interfaces, explore data, and make small interactive projects. The orange companion above is based on my own cat.",
             "", "[Portfolio projects](https://github.com/NhatNguyen2407/Portfolio) · [LinkedIn](https://www.linkedin.com/in/nhatnguyen2407) · [Email](mailto:john.bibibi@gmail.com)",
             "", heading("heading-focus", "現在地 / Current focus"), "", picture("terminal", "Computer Science, web interfaces and data exploration"),
             "", heading("heading-work", "作品 / Selected work"), ""]
    for project in projects:
        parts += [f'<a href="docs/projects/{project["id"]}.md">', picture("project-" + project["id"], project["title"] + " - open project overview", 360), "</a>"]
    parts += ["", heading("heading-notes", "制作記録 / Project notes"), "", "<details>", "<summary>Open project overviews, demos and learning notes</summary>", ""]
    for project in projects:
        link = f"[Overview](docs/projects/{project['id']}.md) · [Source]({project['repo']})"
        link += f" · [Demo]({project['demo']})" if project.get("demo") else " · Local run instructions in the source"
        parts += [f"- **{project['title']}** - {link}"]
    parts += ["", "### A small storefront walkthrough", "", '<picture><source media="(prefers-reduced-motion: reduce)" srcset="assets/project-walkthrough-still.svg"><img src="assets/project-walkthrough.svg" alt="Illustrative Dioxyzine Frog flow: explore a product, review the cart and use Sandbox checkout. This is a conceptual animation, not recorded app footage." width="760"></picture>',
              "", "Illustrative flow, not recorded application footage. Each overview explains the project's actual scope and limitations.", "", "</details>",
              "", heading("heading-github", "活動統計 / GitHub activity"), ""]
    if github:
        parts += [picture("github-stats", "GitHub stats, including added and deleted lines"), "", f"Code changes: **{github['days']} days**, selected default branches and my linked GitHub author identity. PRs and issues: my public activity across GitHub. Stars: selected repositories, all time.",
                  "", "[Scope, exclusions and counting rules](docs/data-methods.md)"]
    else:
        parts += ["[My public GitHub activity](https://github.com/NhatNguyen2407)"]
    parts += ["", heading("heading-code-languages", "使用言語 / Code languages"), ""]
    if github:
        parts += [picture("code-languages", "Programming language proportions by repository bytes"), "", "Repository code composition, not a proficiency rating. The mixed coursework repository is excluded from this chart."]
    else:
        parts += ["JavaScript · TypeScript · Python · SQL · HTML · CSS"]
    parts += ["", heading("heading-spoken", "言語 / Languages I speak and learn"), "", "| Language | Current level |", "| --- | --- |"]
    parts += [f"| {item['name']} | {item['level']} |" for item in read_json("data/spoken-languages.json")]
    parts += ["", heading("heading-music", "音楽 / In my headphones"), ""]
    if music:
        parts += [picture("music", "Listening snapshot and top five artists"), ""]
        if music.get("track_url"):
            parts += [f"[Listen to {md(music['track'])}]({music['track_url']})", ""]
        parts += [" · ".join(f"[{md(item['name'])}]({item['url']})" for item in music.get("top_artists", [])[:5]), "", "Playback is a timestamped snapshot. GitHub's image cache can delay updates."]
    else:
        parts += ["A soft spot for Japanese music and slower love songs."]
    parts += ["", heading("heading-updates", "近況 / Recent updates"), ""]
    if github and github.get("events"):
        parts += [f"- {event['date']} - [{md(event['title'])}]({event['url']})" for event in github["events"]]
    else:
        parts += ["[See my public activity on GitHub](https://github.com/NhatNguyen2407)"]
    parts += ["", heading("heading-contributions", "活動の軌跡 / Contribution trail"), ""]
    if (ROOT / "assets/contributions-light.svg").exists():
        parts += [picture("contributions", "Contribution art made from my public profile's contribution grid"), "", "A little catwalk around my contribution map."]
    else:
        parts += ["[Open my contribution graph](https://github.com/NhatNguyen2407?tab=overview)"]
    parts += ["", "<sub>Small ideas. Built with care.</sub>", ""]
    (ROOT / "README.md").write_text("\n".join(parts), encoding="utf-8")
    print("Built the full profile and four project overviews.")


if __name__ == "__main__":
    build()
