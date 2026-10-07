#!/usr/bin/env python3
"""Cycle fixture: run real Open Loops Cycles against a sandbox with the local fallbacks.

Scenario 1 (`build`): a Ready Task with a trivial Build Spec is spawned as the tmux
Worker `ol-hello-file` (a Herdr Worker with --runtime herdr), gets a state.json record and a `spawned` Notifier line, reaches
In Review with a commit on its branch and a Tracker comment that names the branch,
and its Worker is closed.

Scenario 2 (`exploration`): a Ready Task with a tiny Exploration Spec (10-minute time
budget) is spawned as `ol-shorten-fib` under the Exploration Worker agent, and reaches
In Review with a results file and the experiments comparator in its state path.

The sandbox is a temp directory with a project repo and its local bare origin, a
Markdown Tracker directory, a Spec directory, and a home directory with the five
example notes files filled in for the sandbox. Each Cycle runs the command in the
"How a Cycle starts" block of the example host.md.

The fixture uses a real agent and costs tokens. Run it on demand, not on each commit.
It checks only files, git refs and tmux sessions, never the agent's wording.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

from schema_check import schema_errors  # noqa: E402

HELLO_LINE = "Hello from Open Loops."

NOTES_FILES = {
    "tracker.md": REPO / "adapters/tracker/markdown.md",
    "host.md": REPO / "adapters/host/cron-claude.md",
    "runtime.md": REPO / "adapters/runtime/tmux.md",
    "notifier.md": REPO / "adapters/notifier/log-file.md",
    "review.md": REPO / "adapters/review/local-branch.md",
}


@dataclass
class Scenario:
    number: int
    slug: str
    project_files: tuple  # fixture files copied into the project repo before the first commit
    result_checks: Callable  # (sandbox, checks): the scenario's own end checks
    agent: str = ""  # the Spec's agent: field; the Worker must start with --agent <agent>

    @property
    def worker(self):
        return f"ol-{self.slug}"


@dataclass
class Sandbox:
    scenario: Scenario
    root: Path
    origin: Path
    project: Path
    tracker: Path
    specs: Path
    home: Path
    notifier_log: Path

    @property
    def task_file(self):
        return self.tracker / f"{self.scenario.slug}.md"

    @property
    def state_path(self):
        return self.project / ".openloops" / self.scenario.slug

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


RUNTIMES = ("tmux", "herdr")
HERDR_SESSION = "openloops-fixture"


def notes_files(runtime):
    return {**NOTES_FILES, "runtime.md": REPO / f"adapters/runtime/{runtime}.md"}


def build_sandbox(root, orchestrator_model, worker_model, permission_mode, scenario=None, runtime="tmux"):
    scenario = scenario or SCENARIOS["build"]
    sb = Sandbox(
        scenario=scenario,
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
    for name in scenario.project_files:
        shutil.copy(HERE / "fixtures" / name, sb.project / name)
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
    for name, source in notes_files(runtime).items():
        (sb.home / name).write_text(render(source.read_text(), values))
    # Setup step: install the core agents where the Worker's --add-dir of the home directory finds them.
    agents = sb.home / ".claude" / "agents"
    agents.mkdir(parents=True)
    for agent in sorted((REPO / "core/agents").glob("*.md")):
        shutil.copy(agent, agents / agent.name)
    slug = scenario.slug
    sb.task_file.write_text(render((HERE / f"fixtures/{slug}.task.md").read_text(), values))
    (sb.specs / f"{slug}.md").write_text(render((HERE / f"fixtures/{slug}.spec.md").read_text(), values))
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


def tmux_sessions():
    out = subprocess.run(
        ["tmux", "list-sessions", "-F", "#{session_name}"], capture_output=True, text=True
    )
    return out.stdout.split() if out.returncode == 0 else []


def herdr_json(*args):
    out = subprocess.run(["herdr", *args], capture_output=True, text=True)
    try:
        return json.loads(out.stdout)["result"]
    except (ValueError, KeyError, TypeError):
        return None


def herdr_agents():
    """Agent names in `herdr agent list`, or None if the Herdr server does not answer."""
    result = herdr_json("agent", "list")
    return None if result is None else [a["name"] for a in result["agents"] if a.get("name")]


def workers(runtime):
    """Names that the Runtime lists (tmux sessions or Herdr agents). Fails if Herdr does not answer,
    so that a dead server never passes as "the Worker is closed"."""
    if runtime == "herdr":
        names = herdr_agents()
        if names is None:
            raise RuntimeError(f"the Herdr session {HERDR_SESSION} does not answer `herdr agent list`")
        return names
    return tmux_sessions()


def pane_command(runtime, worker):
    """The command line that started the Worker's agent."""
    if runtime == "herdr":
        agent = herdr_json("agent", "get", worker) or {}
        pane = agent.get("agent", {}).get("pane_id", "")
        info = herdr_json("pane", "process-info", "--pane", pane) or {}
        return " ".join(p.get("cmdline", "") for p in info.get("process_info", {}).get("foreground_processes", []))
    out = subprocess.run(
        ["tmux", "list-panes", "-t", worker, "-F", "#{pane_start_command}"], capture_output=True, text=True
    )
    return out.stdout.strip() if out.returncode == 0 else ""


def start_herdr_session():
    """Start the named Herdr session HERDR_SESSION as its own server, and point every herdr command
    of this process and its children (the Cycles) at it, so that the fixture never sees or touches
    the Owner's own Herdr agents. Returns an error text, or None."""
    # Delete a stopped session from an earlier run, so that no old workspace comes back.
    subprocess.run(["herdr", "session", "delete", HERDR_SESSION], capture_output=True)
    # A pane starts from the server's environment. Start the server with a clean login-like
    # environment, so that the Workers do not inherit the variables of the agent session that runs
    # this fixture (and a shell profile sees a plain terminal).
    clean_env = {k: os.environ[k] for k in ("HOME", "USER", "LOGNAME", "SHELL", "PATH", "LANG") if k in os.environ}
    subprocess.Popen(
        ["herdr", "--session", HERDR_SESSION, "server"],
        env=clean_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    socket = None
    for _ in range(20):
        time.sleep(0.5)
        rows = subprocess.run(["herdr", "session", "list"], capture_output=True, text=True).stdout.splitlines()
        row = next((r.split() for r in rows if r.split()[:2] == [HERDR_SESSION, "running"]), None)
        if row:
            socket = row[-1]
            break
    if socket is None:
        return f"the Herdr session {HERDR_SESSION} did not start"
    for key in ("HERDR_PANE_ID", "HERDR_TAB_ID", "HERDR_WORKSPACE_ID"):
        os.environ.pop(key, None)
    os.environ["HERDR_SOCKET_PATH"] = socket
    return None if herdr_agents() is not None else f"the Herdr session {HERDR_SESSION} does not answer"


def stop_hint(runtime, worker):
    return f"herdr session stop {HERDR_SESSION}" if runtime == "herdr" else f"tmux kill-session -t {worker}"


def attach_hint(runtime, worker):
    return f"herdr session attach {HERDR_SESSION}" if runtime == "herdr" else f"tmux attach -t {worker}"


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


def spawn_checks(sb, checks, runtime):
    worker = sb.scenario.worker
    state = read_state(sb) or {}
    live = workers(runtime)
    checks.check(f"{runtime} Worker {worker} exists after Cycle 1", worker in live, str(live))
    checks.check(f"state.json has a record for {worker}", worker in state, str(list(state)))
    if sb.scenario.agent:
        command = pane_command(runtime, worker)
        checks.check(
            f"Worker {worker} started with --agent {sb.scenario.agent}",
            f"--agent {sb.scenario.agent}" in command,
            command[:200],
        )
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


def results_rows(sb):
    """Data rows of results.tsv in the state path, or None if the file has no tab-separated header."""
    path = sb.state_path / "results.tsv"
    if not path.exists():
        return None
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    if not lines or "\t" not in lines[0] or "experiment_id" not in lines[0]:
        return None
    return lines[1:]


def hello_file_checks(sb, checks):
    hello = git("show", f"{sb.scenario.worker}:hello.txt", cwd=sb.project, check=False).stdout
    checks.check("hello.txt on the branch has the one line", hello == HELLO_LINE + "\n", repr(hello))


def exploration_checks(sb, checks):
    rows = results_rows(sb)
    checks.check(
        "the state path has results.tsv with a header and at least one experiment row",
        rows,
        "missing or no header" if rows is None else "no rows",
    )
    for name in ("experiments-comparator.html", "report.html"):
        path = sb.state_path / name
        checks.check(f"the state path has {name}", path.exists() and "<" in path.read_text(), str(path))


SCENARIOS = {
    "build": Scenario(1, "hello-file", ("check.sh",), hello_file_checks),
    "exploration": Scenario(
        2, "shorten-fib", ("check.sh", "fib.py", "measure.sh"), exploration_checks, agent="auto-researcher"
    ),
}


def final_checks(sb, checks, runtime):
    worker = sb.scenario.worker
    checks.check("Task is In Review", task_state(sb) == "In Review", task_state(sb))
    comments = task_comments(sb)
    checks.check(
        f"a Tracker comment names the branch {worker}", any(worker in c for c in comments), f"{len(comments)} comments"
    )
    branch_log = git("log", "--oneline", f"main..{worker}", cwd=sb.project, check=False).stdout.strip()
    checks.check(f"branch {worker} has a commit that is not in main", branch_log, "no commits")
    sb.scenario.result_checks(sb, checks)
    live = workers(runtime)
    checks.check(f"Worker {worker} is closed", worker not in live, str(live))
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
    parser.add_argument("--runtime", choices=RUNTIMES, default="tmux", help="example runtime.md to use")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="build", help="which scenario to run")
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

    for tool in ("git", args.runtime, "timeout") + (() if args.setup_only else ("claude",)):
        if shutil.which(tool) is None:
            sys.exit(f"[fixture] missing tool: {tool}")

    root = Path(tempfile.mkdtemp(prefix="openloops-fixture-"))
    scenario = SCENARIOS[args.scenario]
    worker = scenario.worker
    sb = build_sandbox(root, args.orchestrator_model, args.worker_model, args.permission_mode, scenario, args.runtime)
    command = cycle_command((sb.home / "host.md").read_text())
    print(f"[fixture] sandbox: {sb.root}")
    print(f"[fixture] Runtime: {args.runtime}; attach to the Worker: {attach_hint(args.runtime, worker)}")
    print(f"[fixture] Cycle command: {command}")
    if args.setup_only:
        return 0
    if args.runtime == "herdr":
        error = start_herdr_session()
        if error:
            sys.exit(f"[fixture] {error}")
    if worker in workers(args.runtime):
        sys.exit(f"[fixture] a Worker {worker} already exists; stop it first: {stop_hint(args.runtime, worker)}")
    # Workers start from the Runtime server's environment, so the server must run outside any agent
    # sandbox. For tmux, start it from here if it is not running, and stop only that helper session
    # at the end. For Herdr, the fixture's own session (started above) is stopped at the end if the
    # scenario passes.
    helper = None
    if args.runtime == "tmux" and not tmux_sessions():
        helper = "openloops-fixture-server"
        subprocess.run(["tmux", "new-session", "-d", "-s", helper], check=True)

    checks = Checks()
    deadline = time.time() + args.timeout_minutes * 60
    cycle_timeout = args.cycle_timeout_minutes * 60

    run_cycle(sb, 1, command, cycle_timeout)
    spawn_checks(sb, checks, args.runtime)

    cycle = 1
    while time.time() < deadline:
        # Wait for the Worker to finish its turn, then let the next Cycle close it.
        wait_for(lambda: task_state(sb) == "In Review", min(args.interval_seconds, max(0, deadline - time.time())))
        if time.time() >= deadline:
            break
        cycle += 1
        run_cycle(sb, cycle, command, cycle_timeout)
        if task_state(sb) == "In Review" and worker not in workers(args.runtime):
            break

    final_checks(sb, checks, args.runtime)
    print(f"[fixture] Cycles run: {cycle}")
    print(f"[fixture] SCENARIO {scenario.number} ({args.scenario}) {'PASSED' if checks.passed else 'FAILED'} (Runtime: {args.runtime})")
    if helper:
        subprocess.run(["tmux", "kill-session", "-t", helper], capture_output=True)
    if args.runtime == "herdr" and checks.passed:
        subprocess.run(["herdr", "session", "stop", HERDR_SESSION], capture_output=True)
    if not checks.passed:
        print(f"[fixture] inspect: {sb.root}; stop a leftover Worker: {stop_hint(args.runtime, worker)}")
    return 0 if checks.passed else 1


if __name__ == "__main__":
    sys.exit(main())
