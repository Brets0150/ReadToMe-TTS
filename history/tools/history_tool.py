#!/usr/bin/env python3
"""history_tool.py: transcript export + session routing for the documentation skill.

  history_tool.py export  <transcript.jsonl> <out.md> [--raw <out.jsonl>] [--start-line N] [--project DIR ...]
  history_tool.py route   <transcript.jsonl> <cwd>          # prints one initialized project dir per line
  history_tool.py meta    <transcript.jsonl>                # prints: <session-id> <YYYY-MM-DD> <first-ts> <last-ts>

Supported transcript format: Claude Code session JSONL (records with type user/assistant and
message.content blocks). Other tools: save their export into history/sessions/raw/ by hand.
Secrets: common credential patterns are masked in the Markdown (see REDACT). Not a guarantee.
"""
import json, os, re, sys

MARKER = os.path.join("history", "SESSIONS.md")   # a dir containing this is an initialized project
RESULT_MAX, WRITE_MAX, OLD_MAX = 2000, 4000, 1500

REDACT = [
    (re.compile(r'(-----BEGIN [A-Z ]*PRIVATE KEY-----)[\s\S]*?(-----END [A-Z ]*PRIVATE KEY-----)'), r'\1 [REDACTED] \2'),
    (re.compile(r'(sshpass\s+-p\s*)(\'[^\']*\'|"[^"]*"|\S+)'), r'\1[REDACTED]'),
    (re.compile(r'(\b(?:password|passwd|passphrase|secret|token|api[_-]?key|apikey|auth[_-]?token|access[_-]?key|private[_-]?key)\b["\']?\s*[:=]\s*)(?:"[^"\n]*"|\'[^\'\n]*\'|[^\s"\',;]+)', re.I), r'\1[REDACTED]'),
    (re.compile(r'(\bBearer\s+)[A-Za-z0-9._~+/=-]{8,}'), r'\1[REDACTED]'),
    (re.compile(r'\b(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})\b'), '[REDACTED]'),
    (re.compile(r'(://[^/\s:@]+:)[^@/\s]+(@)'), r'\1[REDACTED]\2'),   # user:pass@host in URLs
]

def redact(s):
    for rx, rep in REDACT:
        s = rx.sub(rep, s)
    return s

def trunc(s, n):
    s = s if isinstance(s, str) else json.dumps(s, indent=1)
    return s if len(s) <= n else s[:n] + f"\n... [truncated {len(s)-n} chars]"

def fence(s):
    s = s.rstrip("\n"); f = "```"
    while f in s: f += "`"
    return f"{f}\n{s}\n{f}"

def records(path, start=0):
    with open(path, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh):
            if i < start: continue
            try: yield i, line, json.loads(line)
            except Exception: continue

def text_of(content):
    if isinstance(content, str): return content
    if isinstance(content, list):
        return "\n".join(x.get("text", "") for x in content if isinstance(x, dict) and x.get("type") == "text")
    return ""

PATH_RX = re.compile(r'(?<![\w.-])(/[A-Za-z0-9._~-][A-Za-z0-9._~/-]*)')

def touched_paths(transcript):
    """Absolute paths mentioned in tool inputs, plus every record's cwd."""
    out = []
    for _, _, d in records(transcript):
        if d.get("cwd"): out.append(d["cwd"])
        if d.get("type") != "assistant": continue
        for x in d.get("message", {}).get("content", []) or []:
            if not isinstance(x, dict) or x.get("type") != "tool_use": continue
            inp = x.get("input", {}) or {}
            for k in ("file_path", "path", "notebook_path"):
                if isinstance(inp.get(k), str): out.append(inp[k])
            if isinstance(inp.get("command"), str): out += PATH_RX.findall(inp["command"])
    return out

def project_of(path):
    """Nearest ancestor (or self) that is an initialized project, else None."""
    p = os.path.abspath(path)
    while True:
        if os.path.isfile(os.path.join(p, MARKER)): return p
        q = os.path.dirname(p)
        if q == p: return None
        p = q

def route(transcript, cwd):
    counts = {}
    for p in touched_paths(transcript):
        pr = project_of(p)
        if pr: counts[pr] = counts.get(pr, 0) + 1
    cwd_pr = project_of(cwd)
    if not counts:
        return [cwd_pr] if cwd_pr else []
    # prefer the most specific projects: drop an ancestor project if a descendant project was touched more
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], -len(kv[0])))
    top = ranked[0][1]
    chosen = [p for p, c in ranked if c * 4 >= top]
    return chosen

def meta(transcript):
    sid = first = last = None
    for _, _, d in records(transcript):
        sid = sid or d.get("sessionId")
        ts = d.get("timestamp")
        if ts: first = first or ts; last = ts
    return sid or os.path.basename(transcript).split(".")[0], (first or "")[:10], first or "", last or ""

def export(transcript, out_md, raw=None, start=0, projects=()):
    tool_names, md = {}, []
    counts = {"user": 0, "assistant": 0, "tools": 0}
    rawfh = open(raw, "w", encoding="utf-8") if raw else None
    sid, day, first, last = meta(transcript)
    for _, line, d in records(transcript, start):
        if rawfh: rawfh.write(line)
        t = d.get("type"); ts = d.get("timestamp", "")
        if t not in ("user", "assistant"): continue
        stamp = ts.replace("T", " ")[:16] + " UTC" if ts else ""
        cont = d.get("message", {}).get("content")
        if t == "user":
            s = text_of(cont).strip()
            if s and not s.startswith("<"):
                md.append(f"\n---\n\n## USER — {stamp}\n\n{s}\n"); counts["user"] += 1
            for x in (cont if isinstance(cont, list) else []):
                if isinstance(x, dict) and x.get("type") == "tool_result":
                    c = x.get("content"); c = text_of(c) if isinstance(c, list) else (c or "")
                    c = c.strip()
                    if not c: continue
                    err = " [ERROR]" if x.get("is_error") else ""
                    name = tool_names.get(x.get("tool_use_id"), "tool")
                    md.append(f"<details><summary>result of {name}{err}</summary>\n\n{fence(trunc(c, RESULT_MAX))}\n\n</details>\n")
        else:
            for x in (cont if isinstance(cont, list) else []):
                if not isinstance(x, dict): continue
                k = x.get("type")
                if k == "text":
                    s = x.get("text", "").strip()
                    if s: md.append(f"\n### ASSISTANT — {stamp}\n\n{s}\n"); counts["assistant"] += 1
                elif k == "tool_use":
                    name = x.get("name"); inp = x.get("input", {}) or {}
                    tool_names[x.get("id")] = name; counts["tools"] += 1
                    if name == "Bash":
                        md.append(f"**{name}** — {inp.get('description', '')}\n\n{fence(inp.get('command', ''))}\n")
                    elif name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                        fp = inp.get("file_path", inp.get("notebook_path", ""))
                        if name == "Write": body = fence(trunc(inp.get("content", ""), WRITE_MAX))
                        else: body = f"old:\n{fence(trunc(inp.get('old_string', ''), OLD_MAX))}\nnew:\n{fence(trunc(inp.get('new_string', ''), WRITE_MAX))}"
                        md.append(f"**{name}** `{fp}`\n\n{body}\n")
                    elif name in ("Read", "Glob", "Grep"):
                        md.append(f"**{name}** `{inp.get('file_path', inp.get('pattern', ''))}`\n")
                    elif name in ("Agent", "Task"):
                        md.append(f"**{name}** — {inp.get('description', '')}\n\n{fence(trunc(inp.get('prompt', ''), 3000))}\n")
                    else:
                        md.append(f"**{name}**\n\n{fence(trunc(json.dumps(inp, indent=1), 1500))}\n")
    if rawfh: rawfh.close()
    header = (
        f"# Session transcript {day} — {sid[:8]}\n\n"
        f"Generated by the documentation skill from a Claude Code session log. Read `history/SESSIONS.md` for the\n"
        f"summary; grep this file for detail. Long tool outputs are truncated; thinking blocks omitted; common\n"
        f"credential patterns masked.\n\n"
        f"- Session id: `{sid}`\n- Span: {first} → {last}\n"
        f"- Human turns: {counts['user']} · Assistant messages: {counts['assistant']} · Tool calls: {counts['tools']}\n"
        + (f"- Projects touched: {', '.join(projects)}\n" if projects else "")
        + (f"- Raw copy: `raw/{os.path.basename(raw)}`\n" if raw else "")
    )
    body = redact("\n".join(md))
    with open(out_md, "w", encoding="utf-8") as fh: fh.write(header + body + "\n")
    return counts

def main(a):
    if not a or a[0] not in ("export", "route", "meta"):
        print(__doc__); return 2
    if a[0] == "meta":
        print(*meta(a[1])); return 0
    if a[0] == "route":
        for p in route(a[1], a[2]): print(p)
        return 0
    tr, out = a[1], a[2]; raw = None; start = 0; projects = []
    i = 3
    while i < len(a):
        if a[i] == "--raw": raw = a[i+1]; i += 2
        elif a[i] == "--start-line": start = int(a[i+1]); i += 2
        elif a[i] == "--project": projects.append(a[i+1]); i += 2
        else: print("unknown arg", a[i]); return 2
    c = export(tr, out, raw, start, projects)
    print(f"OK export {out} user={c['user']} assistant={c['assistant']} tools={c['tools']}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
