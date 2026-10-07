#!/usr/bin/env python3
"""Cycle fixture: run real Open Loops Cycles against a sandbox with the local fallbacks.

Scenario 1: a Ready Task with a trivial Build Spec is spawned as the tmux Worker
`ol-hello-file`, gets a state.json record and a `spawned` Notifier line, reaches
In Review with a commit on its branch and a Tracker comment that names the branch,
and its Worker is closed.

The sandbox is a temp directory with a project repo and its local bare origin, a
Markdown Tracker directory, a Spec directory, and a home directory with the five
example notes files filled in for the sandbox. Each Cycle runs the command in the
"How a Cycle starts" block of the example host.md.

The fixture uses a real agent and costs tokens. Run it on demand, not on each commit.
It checks only files, git refs and tmux sessions, never the agent's wording.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

from schema_check import schema_errors  # noqa: E402

SLUG = "hello-file"
WORKER = f"ol-{SLUG}"
HELLO_LINE = "Hello from Open Loops."

NOTES_FILES = {
    "tracker.md": REPO / "adapters/tracker/markdown.md",
    "host.md": REPO / "adapters/host/cron-claude.md",
    "runtime.md": REPO / "adapters/runtime/tmux.md",
    "notifier.md": REPO / "adapters/notifier/log-file.md",
    "review.md": REPO / "adapters/review/local-branch.md",
}


@dataclass
class Sandbox:
    root: Path
    origin: Path
    project: Path
    tracker: Path
    specs: Path
    home: Path
    notifier_log: Path

    @property
    def task_file(self):
        return self.tracker / f"{SLUG}.md"

    @property
    def state_file(self):
        return self.home / "state.json"


def render(text, values):
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    left = re.findall(r"\{\{[A-Z_]+\}\}", text)
    if left:
        raise ValueError(f"unfilled placeholders: {sorted(set(left))}")
    return text


def git(*args, cwd=None, check=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)


def build_sandbox(root, orchestrator_model, worker_model, permission_mode):
    sb = Sandbox(
        root=root,
        origin=root / "origin.git",
        project=root / "project",
        tracker=root / "tracker",
        specs=root / "specs",
        home=root / "home",
        notifier_log=root / "home" / "notifications.log",
    )
    for d in (sb.project, sb.tracker, sb.specs, sb.home):
        d.mkdir(parents=True)

    git("init", "-q", "-b", "main", cwd=sb.project)
    git("config", "--local", "user.name", "Open Loops Fixture", cwd=sb.project)
    git("config", "--local", "user.email", "fixture@example.invalid", cwd=sb.project)
    (sb.project / "README.md").write_text("# Fixture project\n\nA sandbox repo for the Open Loops Cycle fixture.\n")
    (sb.project / ".gitignore").write_text(".openloops/\n")
    shutil.copy(HERE / "fixtures/check.sh", sb.project / "check.sh")
    git("add", ".", cwd=sb.project)
    git("commit", "-q", "-m", "Initial commit", cwd=sb.project)
    git("clone", "-q", "--bare", str(sb.project), str(sb.origin))
    git("remote", "add", "origin", str(sb.origin), cwd=sb.project)
    git("fetch", "-q", "origin", cwd=sb.project)
    git("branch", "-q", "--set-upstream-to=origin/main", "main", cwd=sb.project)

    values = {
        "TRACKER_DIR": str(sb.tracker),
        "SPEC_DIR": str(sb.specs),
        "HOME_DIR": str(sb.home),
        "CORE_DIR": str(REPO / "core"),
        "NOTIFIER_LOG": str(sb.notifier_log),
        "WORKER_MODEL": worker_model,
        "ORCHESTRATOR_MODEL": orchestrator_model,
        "PERMISSION_MODE": permission_mode,
        "PROJECT_REPO": str(sb.project),
        "BUILD_TEST_COMMAND": "sh check.sh",
        "EXTRA_DIRS": f"--add-dir {sb.tracker} --add-dir {sb.home} --add-dir {sb.specs}",
    }
    for name, source in NOTES_FILES.items():
        (sb.home / name).write_text(render(source.read_text(), values))
    sb.task_file.write_text(render((HERE / "fixtures/hello-file.task.md").read_text(), values))
    (sb.specs / f"{SLUG}.md").write_text(render((HERE / "fixtures/hello-file.spec.md").read_text(), values))
    return sb


def cycle_command(host_md):
    """The first sh block under "## How a Cycle starts" in host.md, as one shell line."""
    section = host_md.split("## How a Cycle starts", 1)[1]
    block = re.search(r"```sh\n(.*?)```", section, re.S).group(1)
    return " ".join(line.rstrip("\\").strip() for line in block.strip().splitlines())


def task_frontmatter(sb):
    text = sb.task_file.read_text()
    head = text.split("---", 2)[1]
    fields = {}
    for line in head.strip().splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"')
    return fields


def task_state(sb):
    return task_frontmatter(sb).get("state", "")


def task_comments(sb):
    text = sb.task_file.read_text()
    if "## Comments" not in text:
        return []
    body = text.split("## Comments", 1)[1]
    return [c.strip() for c in re.split(r"^### ", body, flags=re.M)[1:]]


def tmux_sessions(sb=None):
    out = subprocess.run(
        ["tmux", "list-sessions", "-F", "#{session_name}"], capture_output=True, text=True
    )
    return out.stdout.split() if out.returncode == 0 else []


def read_state(sb):
    if not sb.state_file.exists():
        return None
    return json.loads(sb.state_file.read_text())


def state_errors(sb):
    state = read_state(sb)
    if state is None:
        return ["state.json does not exist"]
    schema = json.loads((REPO / "core/state.schema.json").read_text())
    return schema_errors(state, schema)


def run_cycle(sb, number, command, cycle_timeout):
    print(f"[fixture] Cycle {number}: start")
    started = time.time()
    try:
        code = subprocess.run(command, shell=True, cwd=sb.home, timeout=cycle_timeout).returncode
    except subprocess.TimeoutExpired:
        code = "timeout"
    print(f"[fixture] Cycle {number}: exit {code} after {time.time() - started:.0f}s")


class Checks:
    def __init__(self):
        self.results = []

    def check(self, name, ok, detail=""):
        self.results.append((name, bool(ok), detail))
        print(f"[fixture] {'PASS' if ok else 'FAIL'}: {name}{' (' + detail + ')' if detail and not ok else ''}")

    @property
    def passed(self):
        return all(ok for _, ok, _ in self.results)


def spawn_checks(sb, checks):
    state = read_state(sb) or {}
    checks.check(f"tmux Worker {WORKER} exists after Cycle 1", WORKER in tmux_sessions(sb), str(tmux_sessions(sb)))
    checks.check(f"state.json has a record for {WORKER}", WORKER in state, str(list(state)))
    errors = state_errors(sb)
    checks.check("state.json validates against core/state.schema.json", not errors, "; ".join(errors))
    checks.check(
        "Task is Working (or already In Review)", task_state(sb) in ("Working", "In Review"), task_state(sb)
    )
    log = sb.notifier_log.read_text() if sb.notifier_log.exists() else ""
    checks.check(
        "Notifier log has a spawned line",
        re.search(r"^\S+ spawned ", log, re.M),
        log.strip()[-200:],
    )


def final_checks(sb, checks):
    checks.check("Task is In Review", task_state(sb) == "In Review", task_state(sb))
    comments = task_comments(sb)
    checks.check(
        f"a Tracker comment names the branch {WORKER}", any(WORKER in c for c in comments), f"{len(comments)} comments"
    )
    branch_log = git("log", "--oneline", f"main..{WORKER}", cwd=sb.project, check=False).stdout.strip()
    checks.check(f"branch {WORKER} has a commit that is not in main", branch_log, "no commits")
    hello = git("show", f"{WORKER}:hello.txt", cwd=sb.project, check=False).stdout
    checks.check("hello.txt on the branch has the one line", hello == HELLO_LINE + "\n", repr(hello))
    checks.check(f"Worker {WORKER} is closed", WORKER not in tmux_sessions(sb), str(tmux_sessions(sb)))
    errors = state_errors(sb)
    checks.check("state.json still validates", not errors, "; ".join(errors))
    log = (sb.home / "orchestrator.log").read_text() if (sb.home / "orchestrator.log").exists() else ""
    checks.check("the Cycle log has entries", log.count("\n## ") + log.startswith("## ") >= 2)


def wait_for(predicate, seconds, poll=10):
    deadline = time.time() + seconds
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(poll)
    return predicate()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--setup-only", action="store_true", help="build the sandbox, print its paths, run no Cycle")
    parser.add_argument("--orchestrator-model", default="sonnet")
    parser.add_argument("--worker-model", default="sonnet")
    parser.add_argument(
        "--permission-mode",
        default="bypassPermissions",
        help="Claude Code permission mode for both agents (auto mode can deny the Orchestrator's key sends to Workers)",
    )
    parser.add_argument("--timeout-minutes", type=float, default=45, help="total time for the scenario")
    parser.add_argument("--interval-seconds", type=float, default=120, help="time between Cycles")
    parser.add_argument("--cycle-timeout-minutes", type=float, default=26, help="kill one Cycle after this time")
    args = parser.parse_args()

    for tool in ("git", "tmux", "timeout") + (() if args.setup_only else ("claude",)):
        if shutil.which(tool) is None:
            sys.exit(f"[fixture] missing tool: {tool}")

    root = Path(tempfile.mkdtemp(prefix="openloops-fixture-"))
    sb = build_sandbox(root, args.orchestrator_model, args.worker_model, args.permission_mode)
    command = cycle_command((sb.home / "host.md").read_text())
    print(f"[fixture] sandbox: {sb.root}")
    print(f"[fixture] attach to the Worker: tmux attach -t {WORKER}")
    print(f"[fixture] Cycle command: {command}")
    if args.setup_only:
        return 0
    if WORKER in tmux_sessions():
        sys.exit(f"[fixture] a tmux session {WORKER} already exists; stop it first: tmux kill-session -t {WORKER}")
    # Workers start from the tmux server's environment, so the server must run outside any agent
    # sandbox. Start it from here if it is not running, and stop only that helper session at the end.
    helper = None
    if not tmux_sessions():
        helper = "openloops-fixture-server"
        subprocess.run(["tmux", "new-session", "-d", "-s", helper], check=True)

    checks = Checks()
    deadline = time.time() + args.timeout_minutes * 60
    cycle_timeout = args.cycle_timeout_minutes * 60

    run_cycle(sb, 1, command, cycle_timeout)
    spawn_checks(sb, checks)

    cycle = 1
    while time.time() < deadline:
        # Wait for the Worker to finish its turn, then let the next Cycle close it.
        wait_for(lambda: task_state(sb) == "In Review", min(args.interval_seconds, max(0, deadline - time.time())))
        if time.time() >= deadline:
            break
        cycle += 1
        run_cycle(sb, cycle, command, cycle_timeout)
        if task_state(sb) == "In Review" and WORKER not in tmux_sessions(sb):
            break

    final_checks(sb, checks)
    print(f"[fixture] Cycles run: {cycle}")
    print(f"[fixture] {'SCENARIO 1 PASSED' if checks.passed else 'SCENARIO 1 FAILED'}")
    if helper:
        subprocess.run(["tmux", "kill-session", "-t", helper], capture_output=True)
    if not checks.passed:
        print(f"[fixture] inspect: {sb.root}; stop a leftover Worker: tmux kill-session -t {WORKER}")
    return 0 if checks.passed else 1


if __name__ == "__main__":
    sys.exit(main())
