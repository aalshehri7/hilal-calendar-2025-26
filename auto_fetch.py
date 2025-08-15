import os, requests, datetime, sys
from pathlib import Path

API_KEY = os.environ.get("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_KEY}

TEAM_SEARCH = "Al Hilal"
SEASONS = [2025, 2026]

def api_get(path, params):
    r = requests.get(f"https://v3.football.api-sports.io/{path}",
                     headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    js = r.json()
    if js.get("errors"):
        raise RuntimeError(str(js["errors"]))
    return js["response"]

def find_team_id():
    resp = api_get("teams", {"search": TEAM_SEARCH})
    for t in resp:
        if t["team"]["name"].lower().startswith("al hilal"):
            return t["team"]["id"]
    raise RuntimeError("Al Hilal team id not found")

def fetch_fixtures(team_id):
    out = []
    for season in SEASONS:
        out += api_get("fixtures", {"team": team_id, "season": season})
    seen, uniq = set(), []
    for f in out:
        fid = f["fixture"]["id"]
        if fid not in seen:
            seen.add(fid); uniq.append(f)
    uniq.sort(key=lambda x: x["fixture"]["date"] or "")
    return uniq

def write_ics(fixtures, out_path="public/hilal_2025_2026.ics"):
    def esc(s): return (s or "").replace("\\","\\\\").replace(",","\\,").replace(";","\\;")
    now = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//HILAL AUTO//AR"]
    for m in fixtures:
        fx, lg, tm = m["fixture"], m["league"], m["teams"]
        start_iso = fx.get("date")
        if not start_iso:
            continue
        try:
            dt = datetime.datetime.fromisoformat(start_iso.replace("Z","+00:00"))
        except Exception:
            continue
        dt_end = dt + datetime.timedelta(hours=2)
        home, away = tm["home"]["name"], tm["away"]["name"]
        comp = lg.get("name") or ""
        venue = (fx.get("venue") or {}).get("name") or ""
        city  = (fx.get("venue") or {}).get("city") or ""
        title = f"{home} vs {away} – {comp}"
        uid = f"{fx['id']}@hilal"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now}",
            f"DTSTART:{dt.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{dt_end.strftime('%Y%m%dT%H%M%SZ')}",
            f"SUMMARY:{esc(title)}",
            f"LOCATION:{esc(venue + (', ' + city if city else ''))}",
            "END:VEVENT"
        ]
    lines.append("END:VCALENDAR")
    Path("public").mkdir(exist_ok=True)
    Path("public/index.html").write_text(
        '<!doctype html><meta charset="utf-8"><h1>Al Hilal – 2025/26</h1>'
        '<p><a href="hilal_2025_2026.ics">Subscribe / Download ICS</a></p>',
        encoding="utf-8")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path} with {len(fixtures)} fixtures")

def main():
    if not API_KEY:
        print("Missing API_FOOTBALL_KEY", file=sys.stderr); sys.exit(1)
    team_id = find_team_id()
    fixtures = fetch_fixtures(team_id)
    write_ics(fixtures)

if __name__ == "__main__":
    main()
