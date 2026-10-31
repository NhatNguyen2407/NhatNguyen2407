"""Draw contribution art from the calendar visible on my public GitHub profile."""

from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
import urllib.request
import xml.etree.ElementTree as ET

from build_profile import PALETTES, rect, save_svg, text
from common import ROOT, read_json, write_json


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "data-date" in attrs and "data-level" in attrs:
            day = date.fromisoformat(attrs["data-date"])
            level = int(attrs["data-level"])
            if level not in range(5):
                raise ValueError("Unexpected contribution level")
            self.days[day.isoformat()] = level


def render(data):
    days = data["days"]
    first = date.fromisoformat(days[0]["date"])
    start = first - timedelta(days=(first.weekday() + 1) % 7)
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    cat = ET.parse(ROOT / "assets/mascot-cat.svg").getroot().find("{http://www.w3.org/2000/svg}g")
    artwork = ET.tostring(cat, encoding="unicode")
    for theme, p in PALETTES.items():
        colors = [p["panel"], "#A898BD", "#8C75A5", "#705388", "#553768"] if theme == "light" else [p["panel"], "#4D425E", "#74608D", "#9C83B4", "#C9AFE0"]
        body = text(24, 30, "A LITTLE CATWALK / MY CONTRIBUTION MAP", 12, p["accent"])
        for item in days:
            offset = (date.fromisoformat(item["date"]) - start).days
            body += rect(24 + offset // 7 * 13, 50 + offset % 7 * 13, 10, 10, colors[item["level"]], 2)
        body += '<style>.catwalk{animation:walk 26s linear infinite alternate}@keyframes walk{to{transform:translateX(650px)}}@media(prefers-reduced-motion:reduce){.catwalk{animation:none}}</style>'
        body += '<g class="catwalk"><g transform="translate(24 146) scale(.35)">' + artwork + "</g></g>"
        body += text(24, 211, first.isoformat() + " / " + days[-1]["date"] + " / public profile calendar", 10, p["muted"])
        save_svg("contributions", theme, 760, 232, body, "My cat walks beneath the contribution intensity grid shown on my public GitHub profile")


def update():
    username = read_json("config/profile.json")["username"]
    source = f"https://github.com/users/{username}/contributions"
    request = urllib.request.Request(source, headers={"User-Agent": "NhatNguyen2407-profile"})
    with urllib.request.urlopen(request, timeout=30) as response:
        content = response.read().decode("utf-8")
    parser = CalendarParser()
    parser.feed(content)
    today = datetime.now(timezone.utc).date()
    earliest = today - timedelta(days=364)
    days = [{"date": day, "level": level} for day, level in sorted(parser.days.items()) if earliest <= date.fromisoformat(day) <= today]
    if len(days) < 350 or len(days) > 365:
        raise ValueError("GitHub calendar markup is incomplete or has changed; keeping the previous artwork")
    data = {"username": username, "updated_at": datetime.now(timezone.utc).isoformat(), "source": source, "days": days}
    render(data)
    write_json("data/contributions.json", data)
    print(f"Rendered contribution art from {len(days)} real calendar days.")


if __name__ == "__main__":
    update()
