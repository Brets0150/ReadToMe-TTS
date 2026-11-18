#!/bin/bash
# log-entry.sh <project-dir> decision|problem|session "<title>" [--updates ID] [--supersedes ID] [--by "<tool/model>"] < body.md
# Appends ONE immutable entry (D-/P-/S- id, UTC date, title, body from stdin) to the right history log.
# --updates / --supersedes also add a one-line forward pointer under the referenced entry's heading
# (the only edit ever made to an existing entry). Never edit the logs any other way.
# Result lines: OK <id> <file> | FAIL <reason>
set -u
P=${1:-}; K=${2:-}; T=${3:-}; shift 3 2>/dev/null || { echo "FAIL usage: log-entry.sh <project-dir> decision|problem|session <title> [--updates ID] [--supersedes ID] [--by WHO] < body"; exit 2; }
UPD=""; SUP=""; BY=${DOC_AUTHOR:-unknown}
while [ $# -gt 0 ]; do case "$1" in
  --updates) UPD=$2; shift 2;; --supersedes) SUP=$2; shift 2;; --by) BY=$2; shift 2;;
  *) echo "FAIL unknown option $1"; exit 2;; esac; done
case "$K" in decision) F=DECISIONS.md; X=D;; problem) F=PROBLEMS.md; X=P;; session) F=SESSIONS.md; X=S;; *) echo "FAIL kind must be decision|problem|session"; exit 2;; esac
H="$P/history"; LOG="$H/$F"
[ -f "$LOG" ] || { echo "FAIL not an initialized project (missing $LOG); run init-project.sh"; exit 1; }
[ -n "$T" ] || { echo "FAIL empty title"; exit 2; }
BODY=$(cat); [ -n "$BODY" ] || { echo "FAIL empty body on stdin"; exit 2; }
python3 -I - "$H" "$F" "$X" "$T" "$BY" "$UPD" "$SUP" "$BODY" <<'PY'
import sys, re, os, datetime
h, f, x, title, by, upd, sup, body = sys.argv[1:9]
log = os.path.join(h, f)
now = datetime.datetime.now(datetime.timezone.utc)
day = now.strftime("%Y-%m-%d"); stamp = now.strftime("%Y-%m-%d %H:%M UTC")
ids = [int(m) for m in re.findall(r'^### %s-(\d{4})\b' % x, open(log, encoding="utf-8").read(), re.M)]
new = "%s-%04d" % (x, (max(ids) + 1) if ids else 1)
links = []
FN = {"D": "DECISIONS.md", "P": "PROBLEMS.md", "S": "SESSIONS.md"}
def target(ref):
    fn = FN.get(ref[:1]); path = os.path.join(h, fn) if fn else None
    if not path or not os.path.isfile(path): sys.exit("FAIL bad reference id " + ref)
    s = open(path, encoding="utf-8").read()
    rx = re.compile(r'^(### %s\b[^\n]*\n)' % re.escape(ref), re.M)
    if not rx.search(s): sys.exit("FAIL referenced entry not found: " + ref)
    return path, s, rx
refs = []                                   # validate every reference BEFORE anything is written
if upd: links.append("updates " + upd); refs.append((upd, "Updated by"))
if sup: links.append("supersedes " + sup); refs.append((sup, "Superseded by"))
checked = [(ref, text) + target(ref) for ref, text in refs]
entry = "\n### %s — %s — %s\n- **Logged:** %s by %s\n%s%s\n" % (
    new, day, title.strip(), stamp, by, ("- **Links:** " + "; ".join(links) + "\n") if links else "", body.rstrip() + "\n")
with open(log, "a", encoding="utf-8") as fh: fh.write(entry)
for ref, text, path, s, rx in checked:
    s = open(path, encoding="utf-8").read()      # re-read: the log may be the same file we just appended to
    s = rx.sub(lambda m: m.group(1) + "> %s %s (%s)\n" % (text, new, day), s, count=1)
    open(path, "w", encoding="utf-8").write(s)
print("OK", new, log)
PY
