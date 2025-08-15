from datetime import datetime, timedelta
import csv, os, sys, hashlib

KSA_OFFSET = 3  # hours
INPUT_CSV = os.environ.get("INPUT_CSV", "matches.csv")
OUTPUT_ICS = os.environ.get("OUTPUT_ICS", "website/hilal_2025_2026.ics")

def to_utc_ical(dt_local_str):
    dt_local = datetime.strptime(dt_local_str, "%Y-%m-%d %H:%M")
    dt_utc = dt_local - timedelta(hours=KSA_OFFSET)
    return dt_utc.strftime("%Y%m%dT%H%M%SZ")

def uid(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest() + "@hilalcal"

rows = []
with open(INPUT_CSV, newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    for x in r:
        rows.append(x)

cal = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//HILAL AUTO CAL 2025-26//EN"]

now_utc = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

for r in rows:
    local_str = f"{r['date']} {r['time']}"
    start_utc = to_utc_ical(local_str)
    end_utc = to_utc_ical((datetime.strptime(local_str, "%Y-%m-%d %H:%M")+timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"))
    summary = f"الهلال vs {r['opponent']} – {r['competition']}"
    location = r['venue']
    u = uid(summary + start_utc + location)
    cal += [
        "BEGIN:VEVENT",
        f"UID:{u}",
        f"DTSTAMP:{now_utc}",
        f"DTSTART:{start_utc}",
        f"DTEND:{end_utc}",
        f"SUMMARY:{summary}",
        f"LOCATION:{location}",
        "END:VEVENT"
    ]

cal.append("END:VCALENDAR")

os.makedirs(os.path.dirname(OUTPUT_ICS), exist_ok=True)
with open(OUTPUT_ICS, "w", encoding="utf-8") as f:
    f.write("\n".join(cal))

print(f"Wrote {OUTPUT_ICS} with {len(rows)} events.")
