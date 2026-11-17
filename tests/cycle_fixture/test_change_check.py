"""Offline tests of the Change check runner (core/change-check.py). They need no agent and no network.

Each test makes a fake home directory with a change-check.md whose Read commands print files of the
test, and a fake Cycle command that logs each start and exits with a code that the test sets.
"""
import importlib.util
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("change_check", REPO / "core" / "change-check.py")
cc = importlib.util.module_from_spec(spec)
sys.dont_write_bytecode, _old = True, sys.dont_write_bytecode  # no __pycache__ in core/
spec.loader.exec_module(cc)
sys.dont_write_bytecode = _old

MIN, HOUR = 60, 3600

SETTINGS = """- Safety Cycle: 240 minutes
- Error gap: 30 minutes
- Failed Check gap: 30 minutes
- Retry gap: 30 minutes
- Repeat limit: 3
- Transient Change checks: 2
- Reminder: 240 minutes
- Read timeout: 10 seconds
"""


def slot(slot_reads, probe=None):
    """The body of a Slot section of change-check.md: {read id: (command, failed checks only)}."""
    out = []
    if probe:
        out += ["### Auth probe", "", "```sh", probe, "```", ""]
    for rid, (command, failed) in slot_reads.items():
        out += [f"### Read: {rid}", ""]
        if failed:
            out += ["Failed Checks only: yes", ""]
        out += ["```sh", command, "```", ""]
    return "\n".join(out)


class Home:
    """A fake home directory, a fake clock and a fake Cycle command."""

    def __init__(self, send=True):
        self.dir = Path(tempfile.mkdtemp())
        self.t = 1_000_000.0
        for name in ("tasks", "prs", "checks", "workers"):
            (self.dir / f"{name}.txt").write_text(f"{name} v1\n")
        (self.dir / "checks.txt").write_text("")
        (self.dir / "auth_ok").write_text("")
        for name in cc.NOTES:  # the rules files of the Orchestrator; the runner only hashes them
            (self.dir / name).write_text(f"# {name}\n")
        probe = "test -e auth_ok"
        self.parts = {
            "Settings": SETTINGS,
            "Tracker": slot({"tasks": ("cat tasks.txt", False)}, probe),
            "Review System": slot({"prs": ("cat prs.txt", False), "checks": ("cat checks.txt", True)}, probe),
            "Runtime": slot({"workers": ("cat workers.txt", False)}),
            "Notifier": "### Send\n\n```sh\nprintf '%s %s\\n' \"$OL_EVENT\" \"$OL_MESSAGE\" >> sent.log\n```\n" if send else "",
        }
        self.save_config()
        (self.dir / "exit_code").write_text("0")
        # The Cycle exits with the code in exit_code; with the file cycle_breaks_auth, it also breaks the login.
        self.cycle = [sys.executable, "-c",
                      "import pathlib, sys; h = pathlib.Path(sys.argv[1]);"
                      "open(h / 'cycles.log', 'a').write('cycle\\n');"
                      "(h / 'cycle_breaks_auth').exists() and (h / 'auth_ok').unlink();"
                      "sys.exit(int((h / 'exit_code').read_text()))", str(self.dir)]

    def save_config(self):
        (self.dir / "change-check.md").write_text(
            "# change-check.md\n\n" + "".join(f"## {k}\n\n{v}\n" for k, v in self.parts.items()))

    def set(self, section, text):
        self.parts[section] = text
        self.save_config()

    def close(self):
        shutil.rmtree(self.dir)

    def check(self, minutes=5):
        """Advance the clock, then run one Change check. The number of Cycles it started (0 or 1)."""
        self.t += minutes * MIN
        before = self.cycles()
        with mock.patch.object(cc, "now", lambda: self.t):
            self.assertEqual(cc.check(self.dir, self.cycle), 0)
        return self.cycles() - before

    def assertEqual(self, a, b):
        if a != b:
            raise AssertionError(f"{a!r} != {b!r}")

    def cycles(self):
        p = self.dir / "cycles.log"
        return len(p.read_text().splitlines()) if p.exists() else 0

    def write(self, name, text):
        (self.dir / name).write_text(text)

    def state(self):
        return json.loads((self.dir / "change-check.json").read_text())

    def log(self):
        return (self.dir / "change-check.log").read_text()

    def sent(self):
        p = self.dir / "sent.log"
        return p.read_text().splitlines() if p.exists() else []


class ChangeCheckCase(unittest.TestCase):
    def setUp(self):
        self.h = Home()

    def tearDown(self):
        self.h.close()


class DecideTest(ChangeCheckCase):
    def test_first_check_starts_a_cycle_then_an_unchanged_one_does_not(self):
        self.assertEqual(self.h.check(), 1)
        self.assertIn("reasons=first", self.h.log())
        self.assertEqual(self.h.check(), 0)
        self.assertIn("UNCHANGED", self.h.log())

    def test_a_changed_read_starts_one_cycle(self):
        self.h.check()
        self.h.write("tasks.txt", "tasks v2\n")
        self.assertEqual(self.h.check(), 1)
        self.assertIn("reasons=changed changed=['tracker.tasks']", self.h.log())
        self.assertEqual(self.h.check(), 0)

    def test_safety_cycle_starts_with_no_change(self):
        self.h.check()
        cycles = sum(self.h.check(minutes=30) for _ in range(8))  # 4 hours
        self.assertEqual(cycles, 1)
        self.assertIn("reasons=safety", self.h.log())

    def test_a_rules_change_starts_a_cycle(self):
        self.h.check()
        with open(self.h.dir / "tracker.md", "a") as f:
            f.write("\nA new rule line.\n")
        self.assertEqual(self.h.check(), 1)
        self.assertIn("'rules'", self.h.log())

    def test_failed_check_change_is_held_to_one_cycle_each_failed_check_gap(self):
        self.h.check()
        self.h.write("checks.txt", "1 build\n")
        self.assertEqual(self.h.check(), 1)
        self.assertIn("reasons=failed-check", self.h.log())
        self.h.write("checks.txt", "1 build test\n")
        self.assertEqual(self.h.check(), 0)
        self.assertIn("DEFER failed Check", self.h.log())
        self.assertEqual(self.h.check(minutes=30), 1)

    def test_failed_check_read_going_empty_is_a_normal_change(self):
        self.h.write("checks.txt", "1 build\n")
        self.h.check()
        self.h.write("checks.txt", "")
        self.assertEqual(self.h.check(), 1)
        self.assertIn("reasons=changed", self.h.log())

    def test_failed_check_and_another_change_is_a_normal_change(self):
        self.h.check()
        self.h.write("checks.txt", "1 build\n")
        self.h.write("prs.txt", "prs v2\n")
        self.assertEqual(self.h.check(), 1)
        self.assertIn("reasons=changed", self.h.log())


class SuccessAndFailureTest(ChangeCheckCase):
    def test_marker_is_promoted_only_on_exit_0(self):
        self.h.write("exit_code", "1")
        self.h.check()
        self.assertNotIn("last", self.h.state())
        self.h.write("exit_code", "0")
        self.assertEqual(self.h.check(minutes=30), 1)  # after the Retry gap, the same marker again
        self.assertIn("last", self.h.state())
        self.assertEqual(self.h.check(), 0)

    def test_repeat_limit_holds_failed_cycles_until_a_change(self):
        self.h.write("exit_code", "1")
        cycles = sum(self.h.check() for _ in range(72))  # 6 hours of Change checks
        # First Cycle, 2 retries after the Retry gap, then the Repeat limit; the Safety Cycle releases one more.
        self.assertEqual(cycles, 4)
        self.assertIn("HOLD Repeat limit", self.h.log())
        alerts = [s for s in self.h.sent() if s.startswith("system_alert") and "Repeat limit on" in s]
        self.assertEqual(len(alerts), 1)
        self.h.write("tasks.txt", "tasks v2\n")
        self.assertEqual(self.h.check(minutes=30), 1)
        self.assertIn("release:changed", self.h.log())
        self.h.write("exit_code", "0")
        self.h.write("tasks.txt", "tasks v3\n")
        self.assertEqual(self.h.check(minutes=30), 1)
        self.assertTrue(any(s.startswith("system_recovered") for s in self.h.sent()))
        self.assertNotIn("fail_streak", self.h.state())

    def test_retry_gap_holds_a_change_after_a_failed_cycle(self):
        self.h.write("exit_code", "1")
        self.h.check()
        self.h.write("tasks.txt", "tasks v2\n")
        self.assertEqual(self.h.check(), 0)
        self.assertIn("HOLD Retry gap", self.h.log())
        self.assertEqual(self.h.check(minutes=30), 1)

    def test_a_lost_cycle_counts_as_failed(self):
        self.h.check()
        st = self.h.state()
        st["pending"] = {"marker": "x", "reads": {}, "rules": "r", "started": self.h.t, "reasons": ["changed"]}
        (self.h.dir / "change-check.json").write_text(json.dumps(st))
        self.h.check()
        self.assertIn("FAILED Cycle lost", self.h.log())
        self.assertEqual(self.h.state()["fail_streak"], 1)
        self.assertNotEqual(self.h.state()["last"]["marker"], "x")

    def test_no_cycle_starts_when_an_auth_probe_fails(self):
        # The reads still work (they do not need the login here), but a Cycle would stop early.
        os.remove(self.h.dir / "auth_ok")
        self.assertEqual(self.h.check(), 0)
        self.assertIn("AUTH (no Cycle) Auth probe fails: Review System, Tracker", self.h.log())
        self.assertEqual(len([s for s in self.h.sent() if s.startswith("system_alert")]), 1)
        self.assertEqual(self.h.state()["incidents"]["AUTH"]["slots"], ["Review System", "Tracker"])
        self.assertEqual(self.h.check(), 0)
        self.assertIn("AUTH hold", self.h.log())
        self.h.write("auth_ok", "")
        self.assertEqual(self.h.check(), 1)

    def test_a_failed_cycle_with_a_failing_auth_probe_is_auth(self):
        self.h.write("exit_code", "1")
        self.h.write("cycle_breaks_auth", "")
        self.assertEqual(self.h.check(), 1)
        self.assertIn("AUTH, no Repeat limit count", self.h.log())
        self.assertNotIn("fail_streak", self.h.state())
        self.assertEqual(self.h.check(), 0)
        self.assertIn("AUTH hold", self.h.log())

    def test_an_error_cycle_that_fails_counts_to_the_repeat_limit(self):
        self.h.check()
        self.h.write("exit_code", "1")
        self.h.set("Tracker", slot({"tasks": ("echo 'jq: error' >&2; exit 1", False)}, "test -e auth_ok"))
        cycles = sum(self.h.check(minutes=30) for _ in range(6))  # 3 hours: one error Cycle each Error gap
        self.assertEqual(cycles, 3)
        self.assertIn("HOLD Repeat limit: 3 failed Cycles", self.h.log())

    def test_defer_does_not_delay_a_due_safety_cycle(self):
        self.h.check()
        st = self.h.state()  # a failed-check Cycle 5 minutes ago; the last success 4 hours ago
        st["last_check_cycle"], st["last_success"] = self.h.t, self.h.t + 5 * MIN - 4 * HOUR
        (self.h.dir / "change-check.json").write_text(json.dumps(st))
        self.h.write("checks.txt", "1 build\n")
        self.assertEqual(self.h.check(), 1)
        self.assertIn("reasons=failed-check,safety", self.h.log())


class ErrorClassTest(ChangeCheckCase):
    def break_read(self, message):
        self.h.set("Tracker", slot({"tasks": (f"echo '{message}' >&2; exit 1", False)}, "test -e auth_ok"))

    def test_auth_hold_for_9_hours_then_one_full_check(self):
        self.h.check()
        os.remove(self.h.dir / "auth_ok")
        self.break_read("HTTP 401: Bad credentials")
        cycles = sum(self.h.check() for _ in range(108))  # 9 hours
        self.assertEqual(cycles, 0)
        sent = self.h.sent()
        self.assertEqual(len([s for s in sent if s.startswith("system_alert") and "Auth probe" in s]), 1)
        self.assertEqual(len([s for s in sent if "Reminder" in s]), 2)  # at 4 h and at 8 h
        # The login comes back; a change was made while it was down.
        self.h.write("auth_ok", "")
        self.h.set("Tracker", slot({"tasks": ("cat tasks.txt", False)}, "test -e auth_ok"))
        self.h.write("tasks.txt", "tasks v2\n")
        self.assertEqual(self.h.check(), 1)
        self.assertIn("AUTH probe passes: one full check", self.h.log())
        self.assertTrue(any(s.startswith("system_recovered") for s in self.h.sent()))

    def test_a_safety_cycle_due_during_a_long_auth_problem_runs_at_recovery(self):
        self.h.check()
        os.remove(self.h.dir / "auth_ok")
        self.break_read("HTTP 401")
        self.assertEqual(sum(self.h.check() for _ in range(60)), 0)  # 5 hours: past the Safety Cycle
        self.h.write("auth_ok", "")
        self.h.set("Tracker", slot({"tasks": ("cat tasks.txt", False)}, "test -e auth_ok"))
        self.assertEqual(self.h.check(), 1)
        self.assertIn("reasons=safety", self.h.log())

    def test_a_short_auth_blip_right_before_the_safety_time_does_not_delay_the_safety_cycle(self):
        self.h.check()
        self.assertEqual(sum(self.h.check() for _ in range(47)), 0)  # 3 h 55 min with no change
        os.remove(self.h.dir / "auth_ok")
        self.assertEqual(self.h.check(), 0)  # 4 h: the Safety Cycle is due, but an Auth probe fails
        self.assertIn("AUTH (no Cycle)", self.h.log())
        self.h.write("auth_ok", "")
        self.assertEqual(self.h.check(), 1)  # the first check after recovery, not 4 h later
        self.assertIn("reasons=safety", self.h.log())

    def test_transient_error_waits_then_one_cycle_each_error_gap(self):
        self.h.check()
        self.break_read("connection reset by peer")
        starts = [self.h.check() for _ in range(12)]  # 1 hour
        self.assertEqual(starts[:2], [0, 0])
        self.assertEqual(starts[2], 1)
        self.assertEqual(sum(starts), 2)  # at 15 minutes and at 45 minutes
        self.assertEqual(len([s for s in self.h.sent() if "3 Change checks in a row" in s]), 1)

    def test_unknown_error_starts_one_cycle_each_error_gap(self):
        self.h.check()
        self.break_read("jq: error: syntax")
        starts = [self.h.check() for _ in range(12)]
        self.assertEqual(starts[0], 1)
        self.assertEqual(sum(starts), 2)
        self.assertIn("reasons=error", self.h.log())
        self.assertEqual(len([s for s in self.h.sent() if s.startswith("system_alert")]), 1)

    def test_a_read_timeout_is_transient(self):
        self.h.set("Settings", SETTINGS.replace("Read timeout: 10 seconds", "Read timeout: 1 seconds"))
        self.h.set("Tracker", slot({"tasks": ("sleep 5", False)}))
        self.h.check()
        self.assertIn("TRANSIENT 1/2", self.h.log())

    def test_error_cycle_success_does_not_promote_a_marker(self):
        self.h.check()
        last = self.h.state()["last"]
        self.break_read("jq: error")
        self.h.check()
        self.assertEqual(self.h.state()["last"], last)


class RunnerTest(ChangeCheckCase):
    def test_busy_lock_starts_nothing(self):
        import fcntl
        with open(self.h.dir / "change-check.lock", "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.h.check(), 0)
        self.assertIn("BUSY", self.h.log())

    def test_a_process_that_the_cycle_leaves_running_does_not_block_the_next_cycle(self):
        # The background process inherits every file descriptor that the Cycle has.
        self.h.cycle = ["sh", "-c", f"cd {self.h.dir}; sleep 30 & echo $! > bg.pid; exit 0"]
        self.h.check()
        try:
            self.h.write("tasks.txt", "tasks v2\n")
            self.h.cycle = ["sh", "-c", f"echo cycle >> {self.h.dir}/cycles.log"]
            self.assertEqual(self.h.check(), 1)
            self.assertNotIn("BUSY", self.h.log())
        finally:
            os.kill(int((self.h.dir / "bg.pid").read_text()), signal.SIGKILL)

    def test_a_running_cycle_process_blocks_a_second_cycle_and_alerts_after_the_safety_cycle(self):
        self.h.check()
        proc = subprocess.Popen(["sleep", "60"])
        try:
            st = self.h.state()
            st["pending"] = {"marker": "x", "reads": {}, "rules": "r", "started": self.h.t, "reasons": ["changed"],
                             "pid": proc.pid}
            (self.h.dir / "change-check.json").write_text(json.dumps(st))
            self.h.write("tasks.txt", "tasks v2\n")
            self.assertEqual(self.h.check(), 0)
            self.assertIn(f"BUSY a Cycle runs (process {proc.pid})", self.h.log())
            self.assertEqual(self.h.sent(), [])
            self.assertEqual(self.h.check(minutes=240), 0)
            self.assertEqual(self.h.check(), 0)
            alerts = [s for s in self.h.sent() if s.startswith("system_alert")]
            self.assertEqual(len(alerts), 1)
            self.assertIn("runs longer than the Safety Cycle", alerts[0])
        finally:
            proc.kill()
            proc.wait()
        self.assertEqual(self.h.check(), 0)  # the process is gone: a lost Cycle, then the Retry gap
        self.assertIn("FAILED Cycle lost", self.h.log())
        self.assertEqual(self.h.check(minutes=30), 1)
        self.assertTrue(any(s.startswith("system_recovered") and "BUSY" in s for s in self.h.sent()))

    def test_a_config_file_that_is_not_utf8_is_a_config_error(self):
        (self.h.dir / "change-check.md").write_bytes(b"\xff\xfe")
        self.assertEqual(self.h.check(), 1)
        self.assertIn("CONFIG error", self.h.log())

    def test_config_error_fails_open_once_each_6_checks_with_one_alert(self):
        self.h.set("Settings", SETTINGS.replace("Safety Cycle: 240 minutes", "Safety Cycle: 4 h"))
        starts = [self.h.check() for _ in range(12)]
        self.assertEqual(starts, [1, 0, 0, 0, 0, 0] * 2)
        self.assertIn("CONFIG error ('Safety Cycle' needs seconds, minutes or hours)", self.h.log())
        alerts = [s for s in self.h.sent() if s.startswith("system_alert")]
        self.assertEqual(alerts, ["system_alert ⚠️ Change check config is bad: 'Safety Cycle' needs seconds, minutes "
                                  "or hours. One Cycle each 6 Change checks until it is fixed."])
        self.h.set("Settings", SETTINGS)
        self.assertEqual(self.h.check(), 1)
        self.assertTrue(any(s.startswith("system_recovered") and "CONFIG" in s for s in self.h.sent()))
        self.assertNotIn("CONFIG", self.h.state().get("incidents", {}))

    def test_a_missing_config_file_is_a_config_error(self):
        os.remove(self.h.dir / "change-check.md")
        self.assertEqual(self.h.check(), 1)
        self.assertIn("CONFIG error (no change-check.md in the home directory)", self.h.log())
        self.assertEqual(self.h.check(), 0)

    def test_two_reads_with_the_same_id_are_a_config_error(self):
        self.h.set("Review System", slot({"prs": ("cat prs.txt", False)}) + "\n### Read: prs\n\n```sh\ntrue\n```\n")
        with self.assertRaises(cc.ConfigError):
            cc.load_config(self.h.dir)

    def test_no_send_command_logs_the_alert(self):
        self.h.close()
        self.h = Home(send=False)
        self.h.check()
        self.h.set("Tracker", slot({"tasks": ("exit 1", False)}))
        self.h.check()
        self.assertIn("NOTIFY system_alert (no Send command)", self.h.log())
        self.assertEqual(self.h.sent(), [])

    def test_a_failed_send_is_logged(self):
        self.h.set("Notifier", "### Send\n\n```sh\necho 'no route' >&2; exit 1\n```\n")
        self.h.check()
        self.h.set("Tracker", slot({"tasks": ("exit 1", False)}))
        self.h.check()
        self.assertIn("NOTIFY_FAILED system_alert (no route)", self.h.log())

    def test_scrub_hides_tokens(self):
        text = cc.scrub("Authorization: Bearer abc123 token=xyz password=pw1 api_key: k2 Basic dXNlcg== " + "a" * 40)
        for secret in ("abc123", "xyz", "pw1", "k2", "dXNlcg==", "a" * 40):
            self.assertNotIn(secret, text)

    def test_a_secret_in_stderr_does_not_reach_the_state_or_the_log(self):
        self.h.check()
        self.h.set("Tracker", slot({"tasks": ("echo 'denied for token=s3cr3t' >&2; exit 1", False)}))
        self.h.check()
        self.assertNotIn("s3cr3t", (self.h.dir / "change-check.json").read_text())
        self.assertNotIn("s3cr3t", self.h.log())

    def test_runner_writes_only_its_own_files(self):
        before = set(os.listdir(self.h.dir))
        self.h.check()
        added = set(os.listdir(self.h.dir)) - before
        self.assertEqual(added, {"change-check.json", "change-check.log", "change-check.lock", "cycles.log"})

    def test_test_command_reports_stable_and_unstable(self):
        with mock.patch.object(cc.time, "sleep", lambda s: None):
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(cc.test(self.h.dir, 3), 0)
            self.assertIn("tracker.tasks: stable", out.getvalue())
            self.h.set("Tracker", slot({"tasks": ("date +%s%N", False)}))
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(cc.test(self.h.dir, 3), 1)
            self.assertIn("tracker.tasks: NOT STABLE", out.getvalue())

    def test_command_line(self):
        p = subprocess.run([sys.executable, str(REPO / "core" / "change-check.py"), "check", "--home",
                            str(self.h.dir), "--", *self.h.cycle], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.h.cycles(), 1)


SECTION = {"tracker": "## Tracker", "review": "## Review System", "runtime": "## Runtime", "notifier": "## Notifier", "host": "## Settings"}


def part(slot, example):
    """The section of an example part that setup copies into change-check.md."""
    text = (REPO / "adapters" / slot / f"{example}.change-check.md").read_text()
    return cc.section(text, SECTION[slot])


class ExamplePartsTest(unittest.TestCase):
    """The example parts of change-check.md parse when assembled, and the offline reads work."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_every_assembled_change_check_file_parses(self):
        for tracker in ("github-issues", "markdown"):
            for review in ("github-pr", "local-branch"):
                for runtime in ("herdr-core", "herdr", "tmux"):
                    for host in ("cron-claude", "cron-codex"):
                        parts = [("host", host), ("tracker", tracker), ("review", review), ("runtime", runtime),
                                 ("notifier", "log-file")]
                        (self.dir / "change-check.md").write_text("# change-check.md\n\n" + "".join(
                            f"{SECTION[s]}\n{part(s, e)}\n" for s, e in parts))
                        cfg = cc.load_config(self.dir)
                        self.assertTrue(cfg["send"])
                        self.assertEqual(cfg["settings"]["repeat_limit"], 3)
                        self.assertEqual({r["slot"] for r in cfg["reads"]}, {"Tracker", "Review System", "Runtime"})

    def test_each_example_notes_file_has_its_part_and_no_change_check_section(self):
        for notes in sorted((REPO / "adapters").glob("*/*.md")):
            if notes.name == "README.md" or notes.name.endswith(".change-check.md"):
                continue
            self.assertNotIn("Change check", notes.read_text(), notes)
            self.assertTrue(notes.with_name(notes.stem + ".change-check.md").exists(), notes)

    def test_the_orchestrator_never_reads_change_check_md(self):
        self.assertNotIn("change-check", (REPO / "core" / "orchestrator.md").read_text())
        self.assertNotIn("change-check", (REPO / "core" / "worker-rules.md").read_text())

    def test_kirocrew_and_openclaw_say_not_available(self):
        for host in ("kirocrew", "openclaw"):
            text = (REPO / "adapters" / "host" / f"{host}.change-check.md").read_text()
            self.assertIn("Run one Cycle and return its result: not available", text)
            self.assertNotIn("## Settings", text)

    def test_markdown_read_sees_a_signal_and_ignores_backlog(self):
        tasks = self.dir / "tasks"
        tasks.mkdir()
        (tasks / "a.md").write_text("---\nstate: Ready\n---\nBody\n")
        command = self.read("tracker", "markdown", "tasks").replace("{{TRACKER_DIR}}", str(tasks))
        first = self.run_sh(command)
        (tasks / "b.md").write_text("---\nstate: Backlog\n---\nIdea\n")
        self.assertEqual(self.run_sh(command), first)
        (tasks / "a.md").write_text("---\nstate: Ready\n---\nBody\n\n## Comments\n\nc1: Owner: go\n")
        self.assertNotEqual(self.run_sh(command), first)
        shutil.rmtree(tasks)
        self.assertNotEqual(cc.run_sh(command, self.dir, 10)[0], 0)

    def test_local_branch_read_sees_a_new_commit(self):
        repo = self.dir / "repo"
        git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com"]
        subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
        subprocess.run(git + ["commit", "-q", "--allow-empty", "-m", "a"], check=True)
        command = self.read("review", "local-branch", "branches").replace("{{PROJECT_REPO}}", str(repo))
        first = self.run_sh(command)
        subprocess.run(git + ["branch", "ol-x"], check=True)
        second = self.run_sh(command)
        self.assertNotEqual(second, first)
        subprocess.run(git + ["checkout", "-q", "ol-x"], check=True)
        subprocess.run(git + ["commit", "-q", "--allow-empty", "-m", "b"], check=True)
        self.assertNotEqual(self.run_sh(command), second)

    def test_herdr_core_read_with_no_core_fails_and_starts_no_core(self):
        bin_dir = self.dir / "bin"
        bin_dir.mkdir()
        hc = bin_dir / "hc"
        hc.write_text(f"#!/bin/sh\necho called >> {self.dir}/hc-called\nexit 0\n")
        hc.chmod(0o755)
        env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", HC_SOCKET=str(self.dir / "none.sock"))
        command = self.read("runtime", "herdr-core", "workers")
        code, _, _, _ = cc.run_sh(command, self.dir, 10, env)
        self.assertNotEqual(code, 0)
        self.assertFalse((self.dir / "hc-called").exists())

    @unittest.skipUnless(shutil.which("tmux"), "tmux is not installed")
    def test_tmux_read_on_a_private_server(self):
        tmp = self.dir / "t"
        tmp.mkdir()
        env = dict(os.environ, TMUX_TMPDIR=str(tmp))
        env.pop("TMUX", None)
        command = self.read("runtime", "tmux", "workers")
        self.assertNotEqual(cc.run_sh(command, self.dir, 10, env)[0], 0)  # no server
        subprocess.run(["tmux", "new-session", "-d", "-s", "ol-x", "sh", "-c", "echo hello; sleep 30"],
                       env=env, check=True)
        try:
            code, out, _, _ = cc.run_sh(command, self.dir, 10, env)
            self.assertEqual(code, 0)
            self.assertIn(b"== ol-x", out)
        finally:
            subprocess.run(["tmux", "kill-server"], env=env)

    def test_cron_change_check_line_runs_the_same_cycle_command(self):
        for host in ("cron-claude.md", "cron-codex.md"):
            text = (REPO / "adapters" / "host" / host).read_text()
            plain = re.search(r"```sh\n(.*?)\n```", cc.section(text, "## How a Cycle starts"), re.S).group(1)
            host_part = (REPO / "adapters" / "host" / host.replace(".md", ".change-check.md")).read_text()
            check = re.search(r"```\n(\*/5 .*?)\n```", cc.section(host_part, "## Host"), re.S).group(1)
            cycle = re.search(r"timeout \S+ (.*?) >> ", plain).group(1)
            self.assertIn("change-check.py check --home {{HOME_DIR}} -- ", check)
            self.assertIn(cycle, check, host)

    def test_log_file_send_writes_the_event_and_the_text(self):
        log = self.dir / "notifications.log"
        command = cc.sh_block(cc.section(part("notifier", "log-file"), "### Send"))
        command = command.replace("{{NOTIFIER_LOG}}", str(log))
        env = dict(os.environ, OL_EVENT="system_alert", OL_MESSAGE="it's down")
        self.assertEqual(cc.run_sh(command, self.dir, 10, env)[0], 0)
        self.assertIn("system_alert it's down", log.read_text())

    def read(self, slot, example, rid):
        return cc.sh_block(cc.section(part(slot, example), f"### Read: {rid}"))

    def run_sh(self, command):
        code, out, err, _ = cc.run_sh(command, self.dir, 10)
        self.assertEqual(code, 0, err)
        return out


if __name__ == "__main__":
    unittest.main()
