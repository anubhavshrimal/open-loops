#!/usr/bin/env python3
"""The Change check: a no-LLM step in front of the Cycle. It starts a Cycle only when a signal changed.

Each time, it runs the Read commands, hashes their output into the Change marker, and runs the Cycle
command only when the marker changed, a read failed, or the Safety Cycle is due. Before each Cycle it
runs every Auth probe, and starts no Cycle when one fails. The marker of a Cycle becomes the last
marker only when the Cycle command exits 0.

    python3 change-check.py check --home <home> -- <Cycle command ...>
    python3 change-check.py test --home <home> [--runs 3]

The settings, the commands and the Send command come from <home>/change-check.md (see
docs/cost-saver.md). The Orchestrator never reads that file. The runner writes only
<home>/change-check.json, <home>/change-check.log and <home>/change-check.lock. It never reads or
writes state.json, and never writes a Slot.
Python standard library only.
"""
import argparse
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

CORE = Path(__file__).resolve().parent
NOTES = ("tracker.md", "host.md", "runtime.md", "notifier.md", "review.md")
CONFIG = "change-check.md"
READ_SLOTS = {"Tracker": "tracker", "Review System": "review", "Runtime": "runtime"}  # section -> read id prefix
SETTINGS = {  # name in the Settings section -> (key, unit)
    "Safety Cycle": ("safety", "time"),
    "Error gap": ("error_gap", "time"),
    "Failed Check gap": ("check_gap", "time"),
    "Retry gap": ("retry_gap", "time"),
    "Repeat limit": ("repeat_limit", "count"),
    "Transient Change checks": ("transient_checks", "count"),
    "Reminder": ("reminder", "time"),
    "Read timeout": ("read_timeout", "time"),
}
CONFIG_EVERY = 6  # with a bad config, one Cycle each this many Change checks
SEND_TIMEOUT = 60  # seconds, for a Send command when the settings cannot be read
UNITS = {"seconds": 1, "second": 1, "minutes": 60, "minute": 60, "hours": 3600, "hour": 3600}
TRANSIENT_RE = re.compile(
    r"(?i)timed? ?out|connect|network|temporar|unreachable|reset by peer|broken pipe|\beof\b|"
    r"\b(http|status)\W{0,3}(429|5\d\d)\b|throttl|rate limit|unavailable|try again")
NOTICE = {
    "AUTH": "⚠️ Change check: the Auth probe of {detail} fails since {start}. No Cycle starts until it passes. "
            "Fix that login.",
    "TRANSIENT": "⚠️ Change check: the Read commands failed {n} Change checks in a row since {start} ({detail}). "
                 "At most one Cycle each Error gap until they work.",
    "UNKNOWN": "⚠️ Change check: a Read command fails since {start} ({detail}). "
               "At most one Cycle each Error gap until it works.",
    "FAILED": "⚠️ Change check: {n} Cycles in a row exited with a code that is not 0 since {start} (last: {detail}). "
              "Repeat limit on: no Cycle until the Change marker changes or the Safety Cycle.",
    "BUSY": "⚠️ Change check: a Cycle (process {detail}) runs longer than the Safety Cycle, seen at {start}. "
            "No other Cycle starts until it ends. Check the time limit of the Host's Cycle command.",
    "CONFIG": "⚠️ Change check config is bad: {detail}. One Cycle each %d Change checks until it is fixed." % CONFIG_EVERY,
}
RECOVERED = "✅ Change check: the {cls} problem from {start} is over ({how})."
REMINDER = "⏰ Reminder: the Change check {cls} problem is open since {start} ({detail})."


class ConfigError(Exception):
    pass


class ReadError(Exception):
    def __init__(self, slot, rid, detail, timed_out=False):
        super().__init__(f"{slot} {rid}: {detail}")
        self.slot, self.timed_out = slot, timed_out


def now():
    return time.time()


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


def scrub(text):
    text = re.sub(r"(?i)((bearer|basic)\s+\S+|(token|password|secret|api[_-]?key)[=:]\s*\S+|[A-Za-z0-9_\-]{40,})",
                  "<redacted>", str(text))
    return " ".join(text.split())[:200]


def stamp(t):
    return time.strftime("%Y-%m-%d %H:%M %Z", time.localtime(t))


# ------------------------------------------------------------------ config file

def section(text, heading):
    """The text under `heading` up to the next heading of the same or a higher level, or None."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.splitlines()
    if heading not in lines:
        return None
    out = []
    for line in lines[lines.index(heading) + 1:]:
        m = re.match(r"(#+) ", line)
        if m and len(m.group(1)) <= level:
            break
        out.append(line)
    return "\n".join(out)


def sh_block(text):
    m = re.search(r"```sh\n(.*?)```", text or "", re.S)
    return m.group(1).strip() if m else None


def subsections(text):
    """[(title, body)] for each `### ` heading in text."""
    parts = re.split(r"^### (.+)$", text or "", flags=re.M)
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts), 2)]


def read_send(home):
    """The Send command of the Notifier section, or None. Works also when the settings are bad."""
    try:
        text = (Path(home) / CONFIG).read_text()
    except (OSError, ValueError):
        return None
    for title, body in subsections(section(text, "## Notifier")):
        if title == "Send":
            return sh_block(body)
    return None


def load_config(home):
    """The settings, the reads, the Auth probes and the Send command, from change-check.md in home."""
    path = Path(home) / CONFIG
    if not path.exists():
        raise ConfigError(f"no {CONFIG} in the home directory")
    text = path.read_text()
    cfg = {"reads": [], "probes": {}, "send": read_send(home), "settings": {}}
    for name, prefix in READ_SLOTS.items():
        for title, body in subsections(section(text, f"## {name}")):
            command = sh_block(body)
            if title == "Auth probe" and command:
                cfg["probes"][name] = command
            elif title.startswith("Read: ") and command:
                cfg["reads"].append({"slot": name, "id": f"{prefix}.{title[6:].strip()}", "command": command,
                                     "failed_checks": bool(re.search(r"^Failed Checks only: yes$", body, re.M))})
    for m in re.finditer(r"^- ([A-Za-z ]+): (\S+)(?: (\S+))?", section(text, "## Settings") or "", re.M):
        if m.group(1) in SETTINGS:
            key, unit = SETTINGS[m.group(1)]
            if not m.group(2).isdigit():
                raise ConfigError(f"'{m.group(1)}' needs a whole number")
            n = int(m.group(2))
            if unit == "time":
                if m.group(3) not in UNITS:
                    raise ConfigError(f"'{m.group(1)}' needs seconds, minutes or hours")
                n *= UNITS[m.group(3)]
            cfg["settings"][key] = n
    missing = [name for name, (key, _) in SETTINGS.items() if key not in cfg["settings"]]
    if missing:
        raise ConfigError("the Settings section has no " + ", ".join(missing))
    if not cfg["reads"]:
        raise ConfigError("no Read commands in the Tracker, Review System or Runtime section")
    ids = [r["id"] for r in cfg["reads"]]
    if len(set(ids)) != len(ids):
        raise ConfigError("two Read commands have the same id: give each its own id")
    return cfg


# ------------------------------------------------------------------ reads

def run_sh(command, home, timeout, env=None):
    """(exit code, stdout bytes, stderr text, timed out). Never waits for input."""
    p = subprocess.Popen(["sh", "-c", command], cwd=home, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, start_new_session=True, env=env)
    try:
        out, err = p.communicate(timeout=timeout)
        return p.returncode, out, err.decode(errors="replace"), False
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        p.communicate()
        return None, b"", "", True


def snapshot(cfg, home):
    """{read id: {"sha", "empty", "bytes", "ms"}} for every Read command. Raises ReadError on the first failure."""
    reads = {}
    for r in cfg["reads"]:
        t0 = time.monotonic()
        code, out, err, timed_out = run_sh(r["command"], home, cfg["settings"]["read_timeout"])
        if timed_out:
            raise ReadError(r["slot"], r["id"], "timed out", timed_out=True)
        if code != 0:
            raise ReadError(r["slot"], r["id"], f"exit {code}: {scrub(err)}")
        reads[r["id"]] = {"sha": sha(out), "empty": not out.strip(), "bytes": len(out),
                          "ms": int((time.monotonic() - t0) * 1000)}
    return reads


def rules_sha(home):
    """The rules the Orchestrator follows: its prompt and the five notes files."""
    parts = [(CORE / "orchestrator.md").read_bytes()]
    parts += [(Path(home) / n).read_bytes() if (Path(home) / n).exists() else b"" for n in NOTES]
    return sha(b"\0".join(sha(p).encode() for p in parts))


def marker_of(reads, rules):
    return sha(json.dumps({"reads": {k: v["sha"] for k, v in reads.items()}, "rules": rules}, sort_keys=True))


def failing_probes(cfg, home, slots=None):
    """The Slots whose Auth probe fails (only those in `slots`, if given)."""
    bad = []
    for slot, command in sorted(cfg["probes"].items()):
        if slots is None or slot in slots:
            code, _, _, timed_out = run_sh(command, home, cfg["settings"]["read_timeout"])
            if timed_out or code != 0:
                bad.append(slot)
    return bad


def classify(cfg, home, error):
    if failing_probes(cfg, home, [error.slot]):
        return "AUTH"
    if error.timed_out or TRANSIENT_RE.search(str(error)):
        return "TRANSIENT"
    return "UNKNOWN"


# ------------------------------------------------------------------ decide

def changed_reads(last, reads, rules):
    old = last.get("reads", {})
    out = sorted(k for k in set(old) | set(reads) if old.get(k) != (reads.get(k) or {}).get("sha"))
    if last.get("rules") != rules:
        out.append("rules")
    return out


def decide(st, s, t, marker, reads, rules, err_cls, flagged):
    """(reasons, changed ids, skip line). A skip line means: start no Cycle. It sets st["hold_since"] on a release.

    AUTH never reaches here. The Repeat limit runs last, over every reason, so no reason can go around it."""
    last = st.get("last")
    reasons, changed = [], []
    safety_due = t - st.get("last_success", 0) >= s["safety"]  # an AUTH problem never resets this time
    if err_cls:
        if err_cls == "TRANSIENT" and st.get("transient_streak", 0) <= s["transient_checks"]:
            return [], [], f"TRANSIENT {st.get('transient_streak', 0)}/{s['transient_checks']} (no Cycle)"
        if t - st.get("last_error_cycle", 0) < s["error_gap"]:
            return [], [], f"ERROR {err_cls} (no Cycle, Error gap)"
        reasons.append("error")
    elif not last:
        reasons.append("first")
    elif last["marker"] != marker:
        changed = changed_reads(last, reads, rules)
        if changed and all(c in flagged for c in changed) and any(not reads[c]["empty"] for c in changed):
            if t - st.get("last_check_cycle", 0) < s["check_gap"] and not safety_due:
                return [], changed, "DEFER failed Check (no Cycle, Failed Check gap)"
            reasons.append("failed-check")
        else:
            reasons.append("changed")
    if safety_due:
        reasons.append("safety")
    if not reasons:
        return [], [], "UNCHANGED"
    streak = st.get("fail_streak", 0)
    if streak:
        if t - st.get("last_fail", 0) < s["retry_gap"]:
            return [], changed, f"HOLD Retry gap: {streak} failed Cycle(s); reasons={','.join(reasons)}"
        if streak >= s["repeat_limit"]:
            new_marker = marker is not None and marker != st.get("fail_marker")
            if not new_marker and t - st.get("hold_since", t) < s["safety"]:
                return [], changed, f"HOLD Repeat limit: {streak} failed Cycles; reasons={','.join(reasons)}"
            reasons.append("release:" + ("changed" if new_marker else "safety"))
            st["hold_since"] = t
        else:
            reasons.append(f"retry:{streak}")
    return reasons, changed, None


# ------------------------------------------------------------------ state, log, alerts

def load_state(home):
    try:
        return json.loads((Path(home) / "change-check.json").read_text())
    except (OSError, ValueError):
        return {}


def save_state(home, st):
    path = Path(home) / "change-check.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, sort_keys=True, indent=1))
    os.replace(tmp, path)


class CheckState:
    def __init__(self, home, cfg):
        self.home, self.cfg, self.s = Path(home), cfg, cfg["settings"]
        self.st = load_state(home)
        self.outbox = []

    def save(self):
        save_state(self.home, self.st)

    def log(self, line):
        log(self.home, line)

    def open_incident(self, cls, detail, n=None):
        inc = self.st.setdefault("incidents", {})
        if cls in inc:
            inc[cls]["detail"] = scrub(detail)
            return
        t = now()
        inc[cls] = {"start": t, "last_notice": t, "detail": scrub(detail)}
        self.outbox.append(("system_alert", NOTICE[cls].format(start=stamp(t), detail=scrub(detail), n=n)))

    def close_incident(self, cls, how):
        inc = self.st.get("incidents", {}).pop(cls, None)
        if inc:
            self.outbox.append(("system_recovered", RECOVERED.format(cls=cls, start=stamp(inc["start"]), how=how)))
        return inc

    def finish(self, line):
        t = now()
        for cls, inc in sorted(self.st.get("incidents", {}).items()):
            if t - inc.get("last_notice", t) >= self.s["reminder"]:
                inc["last_notice"] = t
                self.outbox.append(("system_alert", REMINDER.format(cls=cls, start=stamp(inc["start"]),
                                                                    detail=inc.get("detail"))))
        self.save()
        if line:
            self.log(line)
        for event, text in self.outbox:
            send(self.cfg, self.home, event, text)
        self.outbox = []


def log(home, line):
    with open(Path(home) / "change-check.log", "a") as f:
        f.write(time.strftime("%Y-%m-%dT%H:%M:%S%z ") + line + "\n")


def send(cfg, home, event, text):
    """One message through the Notifier's Send command; with none, the log only."""
    if not cfg.get("send"):
        log(home, f"NOTIFY {event} (no Send command): {text}")
        return
    env = dict(os.environ, OL_EVENT=event, OL_MESSAGE=text)
    code, _, err, timed_out = run_sh(cfg["send"], home, cfg["settings"].get("read_timeout", SEND_TIMEOUT), env)
    log(home, f"NOTIFY {event}: {text}" if code == 0 and not timed_out
        else f"NOTIFY_FAILED {event} ({'timed out' if timed_out else scrub(err)}): {text}")


# ------------------------------------------------------------------ check

def settle(tk, code, pend):
    """Store the result of one Cycle. Exit 0: the pending marker becomes the last marker."""
    st, t = tk.st, now()
    st.pop("pending", None)
    tk.close_incident("BUSY", "the long Cycle ended")
    if code == 0:
        if pend.get("marker"):
            st["last"] = {"marker": pend["marker"], "reads": pend["reads"], "rules": pend["rules"]}
        st["last_success"] = t
        for k in ("fail_streak", "last_fail", "fail_marker", "hold_since"):
            st.pop(k, None)
        tk.close_incident("FAILED", "a Cycle exited 0")
        tk.log("SUCCESS Cycle exit 0")
        return
    cause = "lost" if code is None else f"exit {code}"
    bad = failing_probes(tk.cfg, tk.home)
    if bad:
        tk.open_incident("AUTH", ", ".join(bad))
        st["incidents"]["AUTH"]["slots"] = bad
        tk.log(f"FAILED Cycle {cause}; Auth probe fails: {', '.join(bad)} (AUTH, no Repeat limit count)")
        return
    st["fail_streak"] = st.get("fail_streak", 0) + 1
    st["last_fail"], st["fail_marker"] = t, pend.get("marker")
    if st["fail_streak"] >= tk.s["repeat_limit"]:
        st.setdefault("hold_since", t)
        tk.open_incident("FAILED", cause, n=st["fail_streak"])
    tk.log(f"FAILED Cycle {cause}; fail_streak={st['fail_streak']}")


def check(home, cycle):
    """One Change check. The runner holds the lock only while it reads, decides and records; never while a
    Cycle runs, so a process that a Cycle leaves running cannot hold it. The Cycle's process id in the
    pending entry stops a second Cycle while the first one runs."""
    home = Path(home)
    lock_path = home / "change-check.lock"
    with open(lock_path, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            log(home, "BUSY a check runs")
            return 0
        started = locked_check(home, cycle)
    if started:
        proc, cfg = started
        code = proc.wait()
        with open(lock_path, "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            tk = CheckState(home, cfg)
            pend = tk.st.get("pending")
            if pend and pend.get("pid") == proc.pid:
                settle(tk, code, pend)
                tk.finish(None)
    return 0


def alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def run_cycle(cycle):
    """The exit code of the Cycle command. The Cycle gets no file descriptor of the runner."""
    return subprocess.run(cycle).returncode


def bad_config(home, cycle, error):
    """Fail open, with a limit: one Cycle each CONFIG_EVERY Change checks, and one alert."""
    st, t, detail = load_state(home), now(), scrub(error)
    cfg = {"send": read_send(home), "settings": {}}
    inc = st.setdefault("incidents", {})
    new = "CONFIG" not in inc
    inc["CONFIG"] = {"start": inc.get("CONFIG", {}).get("start", t), "last_notice": t, "detail": detail}
    n = st.get("config_checks", 0)
    st["config_checks"] = n + 1
    save_state(home, st)
    if new:
        send(cfg, home, "system_alert", NOTICE["CONFIG"].format(detail=detail))
    if n % CONFIG_EVERY:
        log(home, f"CONFIG error ({detail}): no Cycle ({n % CONFIG_EVERY}/{CONFIG_EVERY})")
        return 0
    log(home, f"CONFIG error ({detail}): fail open, run the Cycle")
    log(home, f"CONFIG Cycle exit {run_cycle(cycle)}")
    return 0


def locked_check(home, cycle):
    """None, or (the Cycle process, cfg) when it started a Cycle; the caller waits for it."""
    try:
        cfg = load_config(home)
    except (ConfigError, OSError, ValueError) as e:
        bad_config(home, cycle, e)
        return None
    tk = CheckState(home, cfg)
    st = tk.st
    if "CONFIG" in st.get("incidents", {}):
        st.pop("config_checks", None)
        tk.close_incident("CONFIG", "the config is good again")

    # 1. A pending Cycle: wait while its process runs; with no process, the runner stopped and lost its result.
    pend = st.get("pending")
    if pend and alive(pend.get("pid")):
        if now() - pend["started"] >= tk.s["safety"]:
            tk.open_incident("BUSY", str(pend["pid"]))
        tk.finish(f"BUSY a Cycle runs (process {pend['pid']})")
        return None
    if pend:
        settle(tk, None, pend)

    # 2. AUTH hold: only the Auth probes until they pass.
    auth = st.get("incidents", {}).get("AUTH")
    if auth:
        bad = failing_probes(cfg, home, auth.get("slots"))
        if bad:
            tk.finish(f"AUTH hold (no Cycle): Auth probe fails: {', '.join(bad)}")
            return None
        tk.log("AUTH probe passes: one full check")

    # 3. Read.
    t0 = time.monotonic()
    err, cls, reads, marker, rules = None, None, None, None, rules_sha(home)
    try:
        reads = snapshot(cfg, home)
        marker = marker_of(reads, rules)
    except ReadError as e:
        err, cls = e, classify(cfg, home, e)
    stats = f"secs={time.monotonic() - t0:.1f}"
    if cls == "AUTH":
        tk.open_incident("AUTH", err.slot)
        st["incidents"]["AUTH"]["slots"] = [err.slot]
        tk.finish(f"AUTH (no Cycle) {scrub(err)} {stats}")
        return None
    if err:
        if cls == "TRANSIENT":
            st["transient_streak"] = st.get("transient_streak", 0) + 1
            if st["transient_streak"] > tk.s["transient_checks"]:
                tk.open_incident("TRANSIENT", str(err), n=st["transient_streak"])
        else:
            tk.open_incident("UNKNOWN", str(err))
    else:
        st.pop("transient_streak", None)
        for c in ("AUTH", "TRANSIENT", "UNKNOWN"):
            tk.close_incident(c, "the Read commands work again")

    # 4. Decide.
    flagged = {r["id"] for r in cfg["reads"] if r["failed_checks"]}
    reasons, changed, skip = decide(st, tk.s, now(), marker, reads, rules, cls, flagged)
    if skip:
        tk.finish(f"{skip} {stats}")
        return None

    # 5. Every Auth probe passes, or no Cycle starts: a Cycle with a failed login would only stop early.
    bad = failing_probes(cfg, home)
    if bad:
        tk.open_incident("AUTH", ", ".join(bad))
        st["incidents"]["AUTH"]["slots"] = bad
        tk.finish(f"AUTH (no Cycle) Auth probe fails: {', '.join(bad)} {stats}")
        return None

    # 6. Start the Cycle. Its marker is pending until the Cycle command exits 0.
    t = now()
    st["pending"] = {"marker": marker, "reads": {k: v["sha"] for k, v in (reads or {}).items()},
                     "rules": rules, "started": t, "reasons": reasons}
    if "error" in reasons:
        st["last_error_cycle"] = t
    if "failed-check" in reasons:
        st["last_check_cycle"] = t
    tk.finish(f"CYCLE reasons={','.join(reasons)} changed={changed} err={scrub(err) if err else '-'} {stats}")
    proc = subprocess.Popen(cycle)
    st["pending"]["pid"] = proc.pid
    tk.save()
    return proc, cfg


# ------------------------------------------------------------------ test

def test(home, runs):
    """Run every Read command and Auth probe `runs` times. Exit 0 when all work and each read is stable."""
    home = Path(home)
    try:
        cfg = load_config(home)
    except (ConfigError, OSError, ValueError) as e:
        print(f"CONFIG error: {e}")
        return 2
    print("settings: " + ", ".join(f"{k}={v}" for k, v in sorted(cfg["settings"].items())))
    print("Send command: " + ("yes" if cfg["send"] else "none (alerts go to change-check.log only)"))
    ok = True
    for slot in sorted(cfg["probes"]):
        bad = failing_probes(cfg, home, [slot])
        print(f"Auth probe {slot}: {'FAILS' if bad else 'passes'}")
        ok = ok and not bad
    seen = {}
    for n in range(1, runs + 1):
        try:
            reads = snapshot(cfg, home)
        except ReadError as e:
            print(f"run {n}: ERROR {scrub(e)}")
            return 1
        for rid, r in reads.items():
            seen.setdefault(rid, set()).add(r["sha"])
            print(f"run {n}: {rid} sha={r['sha'][:16]} bytes={r['bytes']} ms={r['ms']}")
        print(f"run {n}: marker={marker_of(reads, rules_sha(home))[:16]}")
        if n < runs:
            time.sleep(2)
    for rid, shas in sorted(seen.items()):
        print(f"{rid}: {'stable' if len(shas) == 1 else 'NOT STABLE'}")
        ok = ok and len(shas) == 1
    return 0 if ok else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("check", help="one check; start the Cycle command when needed")
    t.add_argument("--home", required=True)
    t.add_argument("cycle", nargs=argparse.REMAINDER, help="-- then the Cycle command")
    r = sub.add_parser("test", help="run the reads and Auth probes; check that each read is stable")
    r.add_argument("--home", required=True)
    r.add_argument("--runs", type=int, default=3)
    args = parser.parse_args(argv)
    if args.cmd == "test":
        return test(args.home, args.runs)
    cycle = args.cycle[1:] if args.cycle[:1] == ["--"] else args.cycle
    if not cycle:
        parser.error("check needs the Cycle command after --")
    return check(args.home, cycle)


if __name__ == "__main__":
    sys.exit(main())
