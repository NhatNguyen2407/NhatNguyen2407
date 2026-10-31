"""Read a Spotify or Last.fm listening snapshot, without playback control."""

from datetime import datetime, timezone
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from common import write_json


def api(url, data=None, bearer=None):
    headers = {"User-Agent": "NhatNguyen2407-profile"}
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    if data is not None:
        data = urllib.parse.urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=30) as response:
            return None if response.status == 204 else json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Music provider returned HTTP {error.code}; check the connection without publishing credentials") from None


def require(name):
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError("Missing configured value: " + name)
    return value


def safe_link(value, domain):
    return value if value and value.startswith("https://" + domain + "/") else "https://" + domain + "/"


def spotify():
    token = api("https://accounts.spotify.com/api/token", {"grant_type": "refresh_token", "client_id": require("SPOTIFY_CLIENT_ID"), "refresh_token": require("SPOTIFY_REFRESH_TOKEN")})["access_token"]
    playback = api("https://api.spotify.com/v1/me/player/currently-playing", bearer=token) or {}
    top = api("https://api.spotify.com/v1/me/top/artists?limit=5&time_range=short_term", bearer=token)
    item = playback.get("item") or {}
    result = {"provider": "Spotify", "playing": bool(playback.get("is_playing")), "period": "LAST 4 WEEKS / AFFINITY", "top_artists": []}
    if item:
        result.update(track=item.get("name", "Untitled"), artist=", ".join(artist["name"] for artist in item.get("artists", [])), track_url=safe_link((item.get("external_urls") or {}).get("spotify"), "open.spotify.com"))
    result["top_artists"] = [{"name": item["name"], "url": safe_link(item.get("external_urls", {}).get("spotify"), "open.spotify.com")} for item in top.get("items", [])[:5]]
    return result


def lastfm():
    params = {"api_key": require("LASTFM_API_KEY"), "user": require("LASTFM_USERNAME"), "format": "json"}
    def get(method, **extra):
        data = api("https://ws.audioscrobbler.com/2.0/?" + urllib.parse.urlencode({**params, "method": method, **extra}))
        if "error" in data:
            raise RuntimeError("Last.fm rejected the request; check the configured account")
        return data
    recent = get("user.getRecentTracks", limit=1).get("recenttracks", {}).get("track", [])
    if isinstance(recent, dict):
        recent = [recent]
    top = get("user.getTopArtists", limit=5, period="1month").get("topartists", {}).get("artist", [])
    result = {"provider": "Last.fm", "playing": False, "period": "LAST MONTH / RECORDED SCROBBLES", "top_artists": []}
    if recent:
        track = recent[0]
        result.update(playing=track.get("@attr", {}).get("nowplaying") == "true", track=track["name"], artist=track["artist"]["#text"], track_url=safe_link(track.get("url"), "www.last.fm"))
        if not result["playing"]:
            result["last_recorded"] = True
    result["top_artists"] = [{"name": item["name"], "url": safe_link(item.get("url"), "www.last.fm")} for item in top[:5]]
    return result


if __name__ == "__main__":
    provider = os.environ.get("MUSIC_PROVIDER", "").casefold()
    try:
        if provider not in {"spotify", "lastfm"}:
            raise RuntimeError("Set MUSIC_PROVIDER to spotify or lastfm before running the music workflow")
        result = spotify() if provider == "spotify" else lastfm()
        result["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        write_json("data/music.json", result)
        print("Updated the public listening snapshot. No credentials were written to profile data.")
    except (RuntimeError, urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as error:
        print(str(error) if isinstance(error, RuntimeError) else "Music request failed; previous snapshot was kept.", file=sys.stderr)
        sys.exit(1)
