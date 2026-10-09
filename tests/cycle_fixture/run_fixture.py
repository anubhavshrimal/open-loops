#!/usr/bin/env python3
"""Cycle fixture: run real Open Loops Cycles against sandboxes with the local fallbacks.

Each scenario builds its own sandbox, sets up Task files (and, where a scenario starts
mid-loop, the branch, Workspace and state.json that earlier Cycles would have left), runs
Cycles, acts as the Owner between Cycles where the scenario says so, and checks the results:

1. build: the sample Build Task (examples/) reaches In Review on a branch, and its Worker is closed.
2. exploration: the sample Exploration Task (examples/) is spawned under the Exploration
   Worker agent and reaches In Review with a results file and the experiments comparator.
3. gated: a Gated Task stays Ready with no Worker until its upstream Task is Done, then spawns.
4. parent: a parent Task with two child Tasks: only the children spawn, and the gap-fill
   prompt fills the dependent Spec before the first child's completion is accepted.
5. follow-up: a Follow-up comment on an In Review Task causes a Respawn in the same Workspace.
6. merge: a Cycle with nothing to do sends nothing; after the Owner merges the Task branch
   into main, the next Cycle moves the Task to Done.
7. backlog: a Task in Backlog is never touched.
8. blocked: a Blocked Task stays silent while its blocker is there; once it clears, the Task
   goes back to Ready with an `unblocked` message.
9. tool-failure: an unreadable Tracker gives one `system_alert` and no state change, no
   second alert on the next Cycle, and `system_recovered` once it is readable again.

A sandbox is a temp directory with a project repo and its local bare origin, a Markdown
Tracker directory, a Spec directory, and a home directory with the five example notes files
filled in for the sandbox. Each Cycle runs the command in the "How a Cycle starts" block of
the example host.md.

The fixture uses a real agent and costs tokens. Run it on demand, not on each commit.
It checks only files, git refs and the Runtime's Worker list, never the agent's wording.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EXAMPLES = REPO / "examples"
CHECK_SH = HERE / "fixtures" / "check.sh"
sys.path.insert(0, str(HERE))

from schema_check import schema_errors  # noqa: E402

NOTES_FILES = {
    "tracker.md": REPO / "adapters/tracker/markdown.md",
    "host.md": REPO / "adapters/host/cron-claude.md",
    "runtime.md": REPO / "adapters/runtime/tmux.md",
    "notifier.md": REPO / "adapters/notifier/log-file.md",
    "review.md": REPO / "adapters/review/local-branch.md",
}

RUNTIMES = ("tmux", "herdr")
HERDR_SESSION = "openloops-fixture"


def notes_files(runtime):
    return {**NOTES_FILES, "runtime.md": REPO / f"adapters/runtime/{runtime}.md"}


@dataclass
class Sandbox:
    root: Path
    origin: Path
    project: Path
    tracker: Path
    specs: Path
    home: Path
    notifier_log: Path
    values: dict

    def task_file(self, task_id):
        return self.tracker / f"{task_id}.md"

    def spec_file(self, slug):
        return self.specs / f"{slug}.md"

    def worktree(self, slug):
        return self.project / ".openloops" / "worktrees" / slug

    def state_path(self, slug):
        return self.project / ".openloops" / slug

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


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def build_sandbox(root, orchestrator_model, worker_model, permission_mode, runtime="tmux", project_files=(CHECK_SH,),
                  home=None, notes=True, remote=True):
    """A sandbox with the project repo, its origin, the notes files and the core agents, and no Tasks yet.
    notes=False leaves the home directory empty, for setup to fill (the setup dry run).
    remote=False makes a project repo with no remote and no origin."""
    home = home or root / "home"
    sb = Sandbox(
        root=root,
        origin=root / "origin.git",
        project=root / "project",
        tracker=root / "tracker",
        specs=root / "specs",
        home=home,
        notifier_log=home / "notifications.log",
        values={},
    )
    for d in (sb.project, sb.tracker, sb.specs, sb.home):
        d.mkdir(parents=True)

    git("init", "-q", "-b", "main", cwd=sb.project)
    git("config", "--local", "user.name", "Open Loops Fixture", cwd=sb.project)
    git("config", "--local", "user.email", "fixture@example.invalid", cwd=sb.project)
    (sb.project / "README.md").write_text("# Fixture project\n\nA sandbox repo for the Open Loops Cycle fixture.\n")
    (sb.project / ".gitignore").write_text(".openloops/\n")
    for path in project_files:
        shutil.copy(path, sb.project / path.name)
    git("add", ".", cwd=sb.project)
    git("commit", "-q", "-m", "Initial commit", cwd=sb.project)
    if remote:
        git("clone", "-q", "--bare", str(sb.project), str(sb.origin))
        git("remote", "add", "origin", str(sb.origin), cwd=sb.project)
        git("fetch", "-q", "origin", cwd=sb.project)
        git("branch", "-q", "--set-upstream-to=origin/main", "main", cwd=sb.project)

    sb.values.update({
        "TRACKER_DIR": str(sb.tracker),
        "SPEC_DIR": str(sb.specs),
        "HOME_DIR": str(sb.home),
        "CORE_DIR": str(REPO / "core"),
        "GARDENER_DIR": str(REPO / "modules/wiki/gardener"),
        "WIKI_DIR": str(root / "wiki"),
        "NOTIFIER_LOG": str(sb.notifier_log),
        "WORKER_MODEL": worker_model,
        "ORCHESTRATOR_MODEL": orchestrator_model,
        "PERMISSION_MODE": permission_mode,
        "CRON_PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PROJECT_REPO": str(sb.project),
        "BUILD_TEST_COMMAND": "sh check.sh",
        "EXTRA_DIRS": f"--add-dir {sb.tracker} --add-dir {sb.home} --add-dir {sb.specs}",
    })
    if not notes:
        return sb
    for name, source in notes_files(runtime).items():
        (sb.home / name).write_text(render(source.read_text(), sb.values))
    # Setup step: install the core agents where the Worker's --add-dir of the home directory finds them.
    agents = sb.home / ".claude" / "agents"
    agents.mkdir(parents=True)
    for agent in sorted((REPO / "core/agents").glob("*.md")):
        shutil.copy(agent, agents / agent.name)
    return sb


def write_spec(sb, slug, title, what, acceptance, depends_on=(), spec_status="ready"):
    """A small Build Spec made from fixtures/build.spec.md."""
    values = dict(
        sb.values,
        TITLE=title,
        TASK_ID=slug,
        WHAT=what,
        ACCEPTANCE=acceptance,
        DEPENDS_ON=", ".join(f'"{d}"' for d in depends_on),
        SPEC_STATUS=spec_status,
    )
    sb.spec_file(slug).write_text(render((HERE / "fixtures/build.spec.md").read_text(), values))
    return sb.spec_file(slug)


def write_example(sb, slug):
    """The sample Spec and Markdown Task examples/specs/<slug>.md and examples/tasks/<slug>.md, filled in."""
    sb.spec_file(slug).write_text(render((EXAMPLES / "specs" / f"{slug}.md").read_text(), sb.values))
    sb.task_file(slug).write_text(render((EXAMPLES / "tasks" / f"{slug}.md").read_text(), sb.values))


def write_task(sb, task_id, title, state, spec=True, parent="", depends_on=(), body="", comments=()):
    """A Markdown Tracker Task file. comments: (author, text) pairs, numbered c1, c2, ..."""
    deps = "[" + ", ".join(depends_on) + "]"
    lines = ["---", f"id: {task_id}", f"title: {title}", f"state: {state}", f'parent: "{parent}"', f"depends_on: {deps}", "---", ""]
    if spec:
        lines += [f"Spec: {sb.spec_file(task_id)}", ""]
    if body:
        lines += [body, ""]
    lines.append("## Comments")
    for number, (author, text) in enumerate(comments, 1):
        lines += ["", f"### c{number} | {now()} | {author}", text]
    sb.task_file(task_id).write_text("\n".join(lines) + "\n")


def set_task_state(sb, task_id, state):
    """The Owner moves a Task: edit its state: line, as tracker.md says."""
    path = sb.task_file(task_id)
    path.write_text(re.sub(r"^state: .*$", f"state: {state}", path.read_text(), count=1, flags=re.M))


def make_task_branch(sb, slug, filename, line):
    """The Workspace and branch that a Worker leaves at In Review: a worktree on ol-<slug> with one commit."""
    wt = sb.worktree(slug)
    git("worktree", "add", "-q", "-b", f"ol-{slug}", str(wt), "main", cwd=sb.project)
    git("branch", "-q", "--set-upstream-to=origin/main", cwd=wt)
    (wt / filename).write_text(line + "\n")
    git("add", filename, cwd=wt)
    git("commit", "-q", "-m", f"Add {filename}", cwd=wt)
    sb.state_path(slug).mkdir(parents=True, exist_ok=True)
    (sb.state_path(slug) / "implementation-notes.html").write_text(f"<html><body><p>Added {filename}.</p></body></html>\n")
    return git("rev-parse", "HEAD", cwd=wt).stdout.strip()


def pr_comment(slug, sha, summary):
    return f"{summary}\n\nBranch: ol-{slug}\nCommit: {sha}\nChecks: pass"


def worktrees_and_branches(sb):
    """The project's worktrees (path and branch, not HEAD: a Worker's commits move it) and its branches."""
    out = git("worktree", "list", "--porcelain", cwd=sb.project).stdout
    trees = sorted(line for line in out.splitlines() if line.startswith(("worktree ", "branch ")))
    branches = git("branch", "--format=%(refname:short)", cwd=sb.project).stdout.split()
    return trees, sorted(branches)


def write_state(sb, state):
    sb.state_file.write_text(json.dumps(state, indent=2) + "\n")


def worker_record(sb, slug, status, **extra):
    return {
        "task_id": slug,
        "spec": str(sb.spec_file(slug)),
        "workspace": str(sb.worktree(slug)),
        "started": now(),
        "status": status,
        **extra,
    }


def cycle_command(host_md):
    """The first sh block under "## How a Cycle starts" in host.md, as one shell line."""
    section = host_md.split("## How a Cycle starts", 1)[1]
    block = re.search(r"```sh\n(.*?)```", section, re.S).group(1)
    return " ".join(line.rstrip("\\").strip() for line in block.strip().splitlines())


def task_frontmatter(sb, task_id):
    text = sb.task_file(task_id).read_text()
    head = text.split("---", 2)[1]
    fields = {}
    for line in head.strip().splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"')
    return fields


def task_state(sb, task_id):
    return task_frontmatter(sb, task_id).get("state", "")


def task_comments(sb, task_id):
    text = sb.task_file(task_id).read_text()
    if "## Comments" not in text:
        return []
    body = text.split("## Comments", 1)[1]
    return [c.strip() for c in re.split(r"^### ", body, flags=re.M)[1:]]


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tmux_sessions():
    out = subprocess.run(["tmux", "list-sessions", "-F", "#{session_name}"], capture_output=True, text=True)
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


def herdr_agent(worker):
    return (herdr_json("agent", "get", worker) or {}).get("agent", {})


def pane_command(runtime, worker):
    """The command line that started the Worker's agent."""
    if runtime == "herdr":
        pane = herdr_agent(worker).get("pane_id", "")
        info = herdr_json("pane", "process-info", "--pane", pane) or {}
        return " ".join(p.get("cmdline", "") for p in info.get("process_info", {}).get("foreground_processes", []))
    out = subprocess.run(["tmux", "list-panes", "-t", worker, "-F", "#{pane_start_command}"], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else ""


def worker_directory(runtime, worker):
    """The directory the Worker's agent started in."""
    if runtime == "herdr":
        return herdr_agent(worker).get("cwd", "")
    out = subprocess.run(["tmux", "display-message", "-p", "-t", worker, "#{session_path}"], capture_output=True, text=True)
    return out.stdout.strip()


def stop_workers(runtime, names):
    for name in names:
        if runtime == "herdr":
            workspace = herdr_agent(name).get("workspace_id")
            if workspace:
                subprocess.run(["herdr", "workspace", "close", workspace], capture_output=True)
        else:
            subprocess.run(["tmux", "kill-session", "-t", name], capture_output=True)


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


def stop_hint(runtime):
    return f"herdr session stop {HERDR_SESSION}" if runtime == "herdr" else "tmux kill-session -t <name>"


def attach_hint(runtime):
    return f"herdr session attach {HERDR_SESSION}" if runtime == "herdr" else "tmux attach -t <name>"


def read_state(sb):
    """state.json as a dict; {} if it does not exist."""
    return json.loads(sb.state_file.read_text()) if sb.state_file.exists() else {}


def state_errors(sb):
    if not sb.state_file.exists():
        return ["state.json does not exist"]
    schema = json.loads((REPO / "core/state.schema.json").read_text())
    return schema_errors(read_state(sb), schema)


def notifications(sb):
    """The Notifier log as (timestamp, event) pairs, oldest first."""
    if not sb.notifier_log.exists():
        return []
    return [tuple(line.split(" ", 2)[:2]) for line in sb.notifier_log.read_text().splitlines() if " " in line]


def events(sb):
    return [event for _, event in notifications(sb)]


def first_event_time(sb, event):
    """When the first `event` line was written, as epoch seconds, or None."""
    stamp = next((ts for ts, e in notifications(sb) if e == event), None)
    return datetime.fromisoformat(stamp).timestamp() if stamp else None


def cycle_log_entries(sb):
    log = sb.home / "orchestrator.log"
    return len(re.findall(r"^## ", log.read_text(), re.M)) if log.exists() else 0


def results_rows(sb, slug):
    """Data rows of results.tsv in the state path, or None if the file has no tab-separated header."""
    path = sb.state_path(slug) / "results.tsv"
    if not path.exists():
        return None
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    if not lines or "\t" not in lines[0] or "experiment_id" not in lines[0]:
        return None
    return lines[1:]


class Checks:
    def __init__(self, label):
        self.label = label
        self.results = []

    def check(self, name, ok, detail=""):
        self.results.append((name, bool(ok), detail))
        mark = "PASS" if ok else "FAIL"
        print(f"[fixture] {self.label}: {mark}: {name}{' (' + str(detail) + ')' if detail and not ok else ''}")

    @property
    def passed(self):
        return bool(self.results) and all(ok for _, ok, _ in self.results)


def wait_for(predicate, seconds, poll=10, observe=None):
    deadline = time.time() + seconds
    while time.time() < deadline:
        if observe:
            observe()
        if predicate():
            return True
        time.sleep(poll)
    if observe:
        observe()
    return predicate()


class Scenario:
    """One scenario in its own sandbox: its Cycle command, its Worker names and its checks."""

    def __init__(self, number, name, args, slugs, project_files=(CHECK_SH,), sb=None, remote=True):
        """sb: run in this sandbox (its notes files already written) instead of a new one.
        remote=False: the project repo has no origin remote."""
        self.number = number
        self.args = args
        self.runtime = args.runtime
        self.workers = [f"ol-{slug}" for slug in slugs]
        if sb is None:
            root = Path(tempfile.mkdtemp(prefix=f"openloops-fixture-s{number}-"))
            sb = build_sandbox(root, args.orchestrator_model, args.worker_model, args.permission_mode,
                               self.runtime, project_files, remote=remote)
        self.sb = sb
        self.command = cycle_command((self.sb.home / "host.md").read_text())
        self.checks = Checks(f"scenario {number}")
        self.check = self.checks.check
        self.cycles = 0
        print(f"[fixture] === Scenario {number} ({name})")
        print(f"[fixture] sandbox: {self.sb.root}")

    def live(self):
        return workers(self.runtime)

    def cycle(self):
        """Run one Cycle and check that it ended cleanly, so a crashed Cycle never passes as a quiet one."""
        self.cycles += 1
        label = f"scenario {self.number}: Cycle {self.cycles}"
        print(f"[fixture] {label}: start")
        started, entries = time.time(), cycle_log_entries(self.sb)
        try:
            code = subprocess.run(
                self.command, shell=True, cwd=self.sb.home, timeout=self.args.cycle_timeout_minutes * 60
            ).returncode
        except subprocess.TimeoutExpired:
            code = "timeout"
        print(f"[fixture] {label}: exit {code} after {time.time() - started:.0f}s")
        self.check(f"Cycle {self.cycles} exited 0 and added a Cycle log entry",
                   code == 0 and cycle_log_entries(self.sb) > entries, f"exit {code}")

    def quiet_cycle(self, what):
        """Run one Cycle in which nothing changes, and check that it sends no message."""
        before = notifications(self.sb)
        self.cycle()
        after = notifications(self.sb)
        self.check(f"no Notifier message on a Cycle where nothing changed ({what})", after == before, after[len(before):])

    def cycles_until(self, done, observe=None):
        """Wait for the Workers and run Cycles until done() or the scenario's time is up."""
        deadline = time.time() + self.args.timeout_minutes * 60
        while time.time() < deadline and not done():
            wait_for(done, min(self.args.interval_seconds, max(0, deadline - time.time())), observe=observe)
            if time.time() >= deadline:
                break
            self.cycle()
            if observe:
                observe()

    def state_valid(self):
        errors = state_errors(self.sb)
        self.check("state.json validates against core/state.schema.json", not errors, "; ".join(errors))

    def finish(self):
        stop_workers(self.runtime, self.workers)
        verdict = "PASSED" if self.checks.passed else "FAILED"
        print(f"[fixture] scenario {self.number}: Cycles: {self.cycles}")
        print(f"[fixture] SCENARIO {self.number} {verdict}")
        if not self.checks.passed:
            print(f"[fixture] inspect: {self.sb.root}")
        return self.checks.passed


def reach_in_review(s, slug, agent=""):
    """Scenarios 1 and 2: Cycle 1 spawns the Worker; later Cycles see it reach In Review and close it."""
    sb, check, worker = s.sb, s.check, f"ol-{slug}"
    s.cycle()
    live = s.live()
    check(f"{s.runtime} Worker {worker} exists after Cycle 1", worker in live, live)
    check(f"state.json has a record for {worker}", worker in read_state(sb), list(read_state(sb)))
    if agent:
        command = pane_command(s.runtime, worker)
        check(f"Worker {worker} started with --agent {agent}", f"--agent {agent}" in command, command[:200])
    s.state_valid()
    check("Task is Working (or already In Review)", task_state(sb, slug) in ("Working", "In Review"), task_state(sb, slug))
    check("Notifier log has a spawned line", "spawned" in events(sb), events(sb))

    s.cycles_until(lambda: task_state(sb, slug) == "In Review" and worker not in s.live())

    check("Task is In Review", task_state(sb, slug) == "In Review", task_state(sb, slug))
    comments = task_comments(sb, slug)
    check(f"a Tracker comment names the branch {worker}", any(worker in c for c in comments), f"{len(comments)} comments")
    branch_log = git("log", "--oneline", f"main..{worker}", cwd=sb.project, check=False).stdout.strip()
    check(f"branch {worker} has a commit that is not in main", branch_log, "no commits")
    check(f"Worker {worker} is closed", worker not in s.live(), s.live())
    s.state_valid()


def scenario_build(args, sb=None):
    slug = "hello-file"
    s = Scenario(1, "build: the sample Build Task reaches In Review", args, [slug], sb=sb)
    write_example(s.sb, slug)
    reach_in_review(s, slug)
    hello = git("show", f"ol-{slug}:hello.txt", cwd=s.sb.project, check=False).stdout
    s.check("hello.txt on the branch has the one line", hello == "Hello from Open Loops.\n", repr(hello))
    return s.finish()


def scenario_exploration(args):
    slug = "shorten-fib"
    s = Scenario(2, "exploration: the sample Exploration Task reaches In Review", args, [slug],
                 project_files=(CHECK_SH, EXAMPLES / "files/fib.py", EXAMPLES / "files/measure.sh"))
    write_example(s.sb, slug)
    reach_in_review(s, slug, agent="auto-researcher")
    rows = results_rows(s.sb, slug)
    s.check("the state path has results.tsv with a header and at least one experiment row", rows,
            "missing or no header" if rows is None else "no rows")
    for name in ("experiments-comparator.html", "report.html"):
        path = s.sb.state_path(slug) / name
        s.check(f"the state path has {name}", path.exists() and "<" in path.read_text(), str(path))
    return s.finish()


def scenario_gated(args):
    up, down = "gate-up", "gate-down"
    s = Scenario(3, "gated: a Gated Task stays Ready until its upstream Task is Done", args, [up, down])
    sb, check = s.sb, s.check
    write_spec(sb, up, "Add up.txt", "Add a file `up.txt` with one line: `Up.`", "`up.txt` has one line, `Up.`")
    write_spec(sb, down, "Add down.txt", "Add a file `down.txt` with one line: `Down.`", "`down.txt` has one line, `Down.`",
               depends_on=[up])
    sha = make_task_branch(sb, up, "up.txt", "Up.")
    write_task(sb, up, "Add up.txt", "In Review", comments=[("worker", pr_comment(up, sha, "Added up.txt."))])
    write_task(sb, down, "Add down.txt", "Ready", depends_on=[up])
    write_state(sb, {f"ol-{up}": worker_record(sb, up, "in_review")})

    s.quiet_cycle("upstream Task In Review")
    check(f"no Worker ol-{down} while {up} is In Review", f"ol-{down}" not in s.live(), s.live())
    check(f"{down} stays Ready", task_state(sb, down) == "Ready", task_state(sb, down))
    check(f"state.json has no record for ol-{down}", f"ol-{down}" not in read_state(sb), list(read_state(sb)))

    # The Owner accepts the upstream Task.
    git("merge", "-q", "--no-ff", "-m", f"Merge ol-{up}", f"ol-{up}", cwd=sb.project)
    set_task_state(sb, up, "Done")

    s.cycle()
    # A trivial Spec can be spawned, finished and closed in one Cycle, so the record is the evidence.
    check(f"state.json has a record for ol-{down} after {up} is Done", f"ol-{down}" in read_state(sb), list(read_state(sb)))
    check(f"{down} is Working (or already In Review)", task_state(sb, down) in ("Working", "In Review"), task_state(sb, down))
    check("Notifier log has a spawned line", "spawned" in events(sb), events(sb))
    s.state_valid()
    return s.finish()


def scenario_parent(args):
    parent, a, b = "family", "fam-a", "fam-b"
    s = Scenario(4, "parent: a parent Task with two child Tasks and a gap-fill prompt", args, [parent, a, b])
    sb, check = s.sb, s.check
    alpha = "Alpha line."
    write_spec(sb, a, "Add alpha.txt", f"Add a file `alpha.txt` with one line: `{alpha}`", f"`alpha.txt` has one line, `{alpha}`")
    write_spec(sb, b, "Add beta.txt",
               "Add a file `beta.txt` with one line: the same line as in `alpha.txt`, which is "
               "{TBD: the exact line that the Task fam-a writes to alpha.txt}.",
               "`beta.txt` has the same one line as `alpha.txt`.", depends_on=[a], spec_status="draft")
    write_task(sb, parent, "Add alpha.txt and beta.txt", "Ready", spec=False,
               body="Parent Task. The work is in the child Tasks fam-a and fam-b; each has its own Spec.")
    write_task(sb, a, "Add alpha.txt", "Ready", parent=parent)
    write_task(sb, b, "Add beta.txt", "Ready", parent=parent, depends_on=[a])

    seen = {"parent_spawned": False, "b_early": False}

    def observe():
        live = s.live()
        seen["parent_spawned"] |= f"ol-{parent}" in live or f"ol-{parent}" in read_state(sb)
        if task_state(sb, a) != "Done":
            seen["b_early"] |= f"ol-{b}" in live or f"ol-{b}" in read_state(sb)

    s.cycle()
    observe()
    check(f"Worker ol-{a} exists after Cycle 1", f"ol-{a}" in s.live(), s.live())
    check(f"{b} is Gated (Ready, no Worker)", task_state(sb, b) == "Ready" and f"ol-{b}" not in s.live(), task_state(sb, b))

    s.cycles_until(lambda: f"ol-{a}" not in s.live() and task_state(sb, a) == "In Review", observe=observe)

    record = read_state(sb).get(f"ol-{a}", {})
    check("gap_fill_done is true when completion is accepted", record.get("gap_fill_done") is True, record)
    check(f"Worker ol-{a} is closed and {a} is In Review",
          f"ol-{a}" not in s.live() and task_state(sb, a) == "In Review", task_state(sb, a))
    spec_b = sb.spec_file(b)
    check(f"the gap in the dependent Spec {b} is filled", "{TBD" not in spec_b.read_text() and alpha in spec_b.read_text(),
          spec_b.read_text().split("## What", 1)[-1][:200])
    accepted = first_event_time(sb, "in_review")
    check(f"the gap was filled before the completion of {a} was accepted",
          accepted is not None and spec_b.stat().st_mtime <= accepted + 1, f"Spec {spec_b.stat().st_mtime}, in_review {accepted}")

    # The Owner accepts fam-a; the next Cycle releases fam-b.
    set_task_state(sb, a, "Done")
    s.cycle()
    observe()
    # A trivial Spec can be spawned, finished and closed in one Cycle, so the record is the evidence.
    check(f"ol-{b} was spawned after {a} is Done",
          f"ol-{b}" in read_state(sb) and task_state(sb, b) in ("Working", "In Review"), task_state(sb, b))
    check(f"no Worker or record for ol-{b} before {a} was Done", not seen["b_early"])
    check(f"the parent never spawned (no ol-{parent}, no record, still Ready)",
          not seen["parent_spawned"] and task_state(sb, parent) == "Ready", task_state(sb, parent))
    s.state_valid()
    return s.finish()


def scenario_follow_up(args):
    slug = "followup-file"
    s = Scenario(5, "follow-up: a Follow-up causes a Respawn, and its fulfilment keeps the Task In Review", args, [slug])
    sb, check, worker = s.sb, s.check, f"ol-{slug}"
    write_spec(sb, slug, "Add followup.txt", "Add a file `followup.txt` with one line: `First line.`",
               "`followup.txt` has one line, `First line.`")
    sha = make_task_branch(sb, slug, "followup.txt", "First line.")
    write_task(sb, slug, "Add followup.txt", "In Review", comments=[
        ("worker", pr_comment(slug, sha, "Added followup.txt.")),
        ("owner", "ACTION: add a second line `Second line.` to followup.txt."),
    ])
    write_state(sb, {worker: worker_record(sb, slug, "in_review")})
    before = worktrees_and_branches(sb)

    s.cycle()
    check(f"Worker {worker} exists after Cycle 1", worker in s.live(), s.live())
    where = worker_directory(s.runtime, worker)
    check("the Worker runs in the same Workspace", where and os.path.realpath(where) == os.path.realpath(sb.worktree(slug)), where)
    check("no new Workspace or branch was made", worktrees_and_branches(sb) == before, worktrees_and_branches(sb))
    check("Notifier log has a respawned line", "respawned" in events(sb), events(sb))
    # A fast Worker can be back In Review already; the Task state and the record must agree.
    record = read_state(sb).get(worker, {})
    check("the Task is Working with a working record (or back In Review)",
          (task_state(sb, slug), record.get("status")) in (("Working", "working"), ("In Review", "working"), ("In Review", "in_review")),
          (task_state(sb, slug), record.get("status")))
    s.state_valid()

    # The Worker finishes the Follow-up. A fulfilled Follow-up never gives Done while the branch is not merged.
    s.cycles_until(lambda: task_state(sb, slug) == "In Review" and worker not in s.live())
    check("the Task is back In Review after the Follow-up", task_state(sb, slug) == "In Review", task_state(sb, slug))
    s.quiet_cycle("fulfilled Follow-up, branch not merged")
    check("the Task stays In Review (a fulfilled Follow-up is not Done)", task_state(sb, slug) == "In Review", task_state(sb, slug))
    check("Notifier log has no done line", "done" not in events(sb), events(sb))
    s.state_valid()
    return s.finish()


def scenario_merge(args):
    slug = "merge-file"
    s = Scenario(6, "merge: a merged Task branch moves the Task to Done", args, [slug])
    sb, check, worker = s.sb, s.check, f"ol-{slug}"
    write_spec(sb, slug, "Add merge.txt", "Add a file `merge.txt` with one line: `Merge me.`", "`merge.txt` has one line, `Merge me.`")
    sha = make_task_branch(sb, slug, "merge.txt", "Merge me.")
    write_task(sb, slug, "Add merge.txt", "In Review", comments=[("worker", pr_comment(slug, sha, "Added merge.txt."))])
    write_state(sb, {worker: worker_record(sb, slug, "in_review")})

    s.quiet_cycle("open PR, no Review comments")
    check("the Task stays In Review while the branch is not merged", task_state(sb, slug) == "In Review", task_state(sb, slug))
    check("no Worker was spawned", worker not in s.live(), s.live())

    # The Owner merges the Task branch into main.
    git("merge", "-q", "--no-ff", "-m", f"Merge {worker}", worker, cwd=sb.project)
    s.cycle()
    check("the Task is Done", task_state(sb, slug) == "Done", task_state(sb, slug))
    check("Notifier log has a done line", "done" in events(sb), events(sb))
    check("the state.json record is removed", worker not in read_state(sb), list(read_state(sb)))
    check("no Worker was spawned", worker not in s.live(), s.live())
    s.state_valid()
    return s.finish()


def scenario_backlog(args):
    slug = "backlog-file"
    s = Scenario(7, "backlog: a Task in Backlog is never touched", args, [slug])
    sb, check, worker = s.sb, s.check, f"ol-{slug}"
    write_spec(sb, slug, "Add backlog.txt", "Add a file `backlog.txt` with one line: `Not yet.`", "`backlog.txt` has one line, `Not yet.`")
    write_task(sb, slug, "Add backlog.txt", "Backlog", comments=[("owner", "ACTION: start this now.")])
    digest = file_digest(sb.task_file(slug))

    s.quiet_cycle("only a Backlog Task")
    check("the Backlog Task file is unchanged", file_digest(sb.task_file(slug)) == digest)
    check("no Worker was spawned", worker not in s.live(), s.live())
    check("state.json has no record for it", worker not in read_state(sb), list(read_state(sb)))
    check("no branch or Workspace was made",
          not git("branch", "--list", worker, cwd=sb.project).stdout.strip() and not sb.worktree(slug).exists())
    return s.finish()


def scenario_blocked(args):
    slug = "blocked-file"
    s = Scenario(8, "blocked: a Blocked Task whose blocker cleared goes back to Ready", args, [slug])
    sb, check, worker = s.sb, s.check, f"ol-{slug}"
    data = sb.project / "data" / "input.txt"
    write_spec(sb, slug, "Copy data/input.txt to copy.txt",
               "Copy the file `data/input.txt` (the Owner adds it) to a new file `copy.txt`.",
               "`copy.txt` has the same content as `data/input.txt`.")
    write_task(sb, slug, "Copy data/input.txt to copy.txt", "Blocked", comments=[
        ("worker", f"The file {data} does not exist, so there is nothing to copy. "
                   f"I need the Owner to add {data} to main. BLOCKED — {data} is missing."),
    ])
    write_state(sb, {worker: worker_record(sb, slug, "blocked", blocked_notified=True)})

    s.quiet_cycle("blocker still there, Owner already told")
    check("the Task stays Blocked", task_state(sb, slug) == "Blocked", task_state(sb, slug))

    # The Owner clears the blocker.
    data.parent.mkdir()
    data.write_text("Input data.\n")
    git("add", "data/input.txt", cwd=sb.project)
    git("commit", "-q", "-m", "Add data/input.txt", cwd=sb.project)

    s.cycle()
    check("the Task is back in Ready (or already Working)", task_state(sb, slug) in ("Ready", "Working"), task_state(sb, slug))
    check("Notifier log has an unblocked line", "unblocked" in events(sb), events(sb))
    check("Notifier log has no blocked line", "blocked" not in events(sb), events(sb))
    record = read_state(sb).get(worker)
    check("the record is kept, with blocked_notified cleared", record is not None and record.get("blocked_notified") is not True, record)
    s.state_valid()
    return s.finish()


def scenario_tool_failure(args):
    slug = "alert-file"
    s = Scenario(9, "tool-failure: an unreadable Tracker gives one alert, then a recovery message", args, [slug])
    sb, check, worker = s.sb, s.check, f"ol-{slug}"
    write_spec(sb, slug, "Add alert.txt", "Add a file `alert.txt` with one line: `Alert.`", "`alert.txt` has one line, `Alert.`")
    write_task(sb, slug, "Add alert.txt", "Ready")
    digest = file_digest(sb.task_file(slug))

    sb.tracker.chmod(0o000)
    try:
        check("the Tracker directory is unreadable for this user", not os.access(sb.tracker, os.R_OK))
        s.cycle()
        check("one system_alert after the first failed Cycle", events(sb) == ["system_alert"], events(sb))
        state = read_state(sb)
        check("state.json has a Tracker alert", "tracker" in state.get("alerts", {}), state.get("alerts"))
        check("no other state.json entry", set(state) <= {"alerts"}, list(state))
        check("no Worker was spawned during the outage", worker not in s.live(), s.live())
        check("the Tracker directory is still unreadable (the Orchestrator did not change it)",
              (sb.tracker.stat().st_mode & 0o777) == 0, oct(sb.tracker.stat().st_mode & 0o777))
        s.quiet_cycle("Tracker still unreadable, Owner already told")
    finally:
        sb.tracker.chmod(0o755)

    check("the Ready Task file is unchanged after the outage", file_digest(sb.task_file(slug)) == digest)
    s.cycle()
    check("system_recovered after the Tracker is readable again", events(sb)[:2] == ["system_alert", "system_recovered"], events(sb))
    check("no second system_alert", events(sb).count("system_alert") == 1, events(sb))
    check("the Tracker alert is removed", "tracker" not in read_state(sb).get("alerts", {}), read_state(sb))
    check("the Cycle went on after recovery: the Ready Task was spawned",
          worker in read_state(sb) and task_state(sb, slug) in ("Working", "In Review"), task_state(sb, slug))
    s.state_valid()
    return s.finish()


def scenario_crash(args):
    none, done = "crash-none", "crash-done"
    s = Scenario(10, "crash: an exited Worker goes to Blocked with no result, to In Review with one", args, [none, done])
    sb, check = s.sb, s.check
    # Both Workers were Working and are now gone from the Runtime (crashed, or the machine restarted).
    write_spec(sb, none, "Add none.txt", "Add a file `none.txt` with one line: `None.`", "`none.txt` has one line, `None.`")
    git("worktree", "add", "-q", "-b", f"ol-{none}", str(sb.worktree(none)), "main", cwd=sb.project)
    write_task(sb, none, "Add none.txt", "Working")
    write_spec(sb, done, "Add done.txt", "Add a file `done.txt` with one line: `Done.`", "`done.txt` has one line, `Done.`")
    sha = make_task_branch(sb, done, "done.txt", "Done.")
    write_task(sb, done, "Add done.txt", "Working", comments=[("worker", pr_comment(done, sha, "Added done.txt."))])
    write_state(sb, {f"ol-{none}": worker_record(sb, none, "working"), f"ol-{done}": worker_record(sb, done, "working")})

    s.cycle()
    log = sb.notifier_log.read_text() if sb.notifier_log.exists() else ""
    check("the Task with no result is Blocked", task_state(sb, none) == "Blocked", task_state(sb, none))
    record = read_state(sb).get(f"ol-{none}", {})
    check("its record is blocked, with blocked_notified", (record.get("status"), record.get("blocked_notified")) == ("blocked", True), record)
    blocked = [line for line in log.splitlines() if " blocked " in line]
    check("one blocked line that says the Worker exited without a result",
          len(blocked) == 1 and "exited without a result" in blocked[0], blocked)
    check("the Task with a result is In Review", task_state(sb, done) == "In Review", task_state(sb, done))
    check("its record is in_review", read_state(sb).get(f"ol-{done}", {}).get("status") == "in_review", read_state(sb).get(f"ol-{done}"))
    check("Notifier log has an in_review line", "in_review" in events(sb), events(sb))
    check("no done line", "done" not in events(sb), events(sb))
    check("no Worker was spawned", not set(s.workers) & set(s.live()), s.live())
    s.state_valid()
    return s.finish()


def scenario_no_remote(args):
    slug = "noremote-file"
    s = Scenario(11, "no-remote: the Local branch path works in a repo with no origin", args, [slug], remote=False)
    sb, check = s.sb, s.check
    check("the project repo has no remote", not git("remote", cwd=sb.project).stdout.strip())
    write_spec(sb, slug, "Add noremote.txt", "Add a file `noremote.txt` with one line: `No remote.`",
               "`noremote.txt` has one line, `No remote.`")
    write_task(sb, slug, "Add noremote.txt", "Ready")
    reach_in_review(s, slug)
    comments = task_comments(sb, slug)
    check("a Tracker comment has a Checks: line", any("Checks:" in c for c in comments), f"{len(comments)} comments")
    check("the project repo still has no remote", not git("remote", cwd=sb.project).stdout.strip())
    return s.finish()


# name -> (scenario function, the slugs of the Workers it can spawn)
SCENARIOS = {
    "build": (scenario_build, ["hello-file"]),
    "exploration": (scenario_exploration, ["shorten-fib"]),
    "gated": (scenario_gated, ["gate-up", "gate-down"]),
    "parent": (scenario_parent, ["family", "fam-a", "fam-b"]),
    "follow-up": (scenario_follow_up, ["followup-file"]),
    "merge": (scenario_merge, ["merge-file"]),
    "backlog": (scenario_backlog, ["backlog-file"]),
    "blocked": (scenario_blocked, ["blocked-file"]),
    "tool-failure": (scenario_tool_failure, ["alert-file"]),
    "crash": (scenario_crash, ["crash-none", "crash-done"]),
    "no-remote": (scenario_no_remote, ["noremote-file"]),
}


def add_agent_options(parser):
    """The options for the agents and the timing of the Cycles, shared with setup_dry_run.py."""
    parser.add_argument("--orchestrator-model", default="sonnet")
    parser.add_argument("--worker-model", default="sonnet")
    parser.add_argument("--permission-mode", default="auto", help="Claude Code permission mode for both agents")
    parser.add_argument("--timeout-minutes", type=float, default=45, help="time for the Worker phase of one scenario")
    parser.add_argument("--interval-seconds", type=float, default=120, help="longest wait for a Worker between Cycles")
    parser.add_argument("--cycle-timeout-minutes", type=float, default=26, help="kill one Cycle after this time")


def start_tmux_helper():
    """Workers start from the tmux server's environment, so the server must run outside any agent
    sandbox. If no server runs, start one from here with a helper session; return its name or None."""
    if tmux_sessions():
        return None
    helper = "openloops-fixture-server"
    subprocess.run(["tmux", "new-session", "-d", "-s", helper], check=True)
    return helper


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--scenario", action="append", choices=list(SCENARIOS),
                        help="run only this scenario (repeat for more); default: all")
    parser.add_argument("--runtime", choices=RUNTIMES, default="tmux", help="example runtime.md to use")
    parser.add_argument("--setup-only", action="store_true", help="build one sandbox, print its paths, run no Cycle")
    add_agent_options(parser)
    args = parser.parse_args()

    for tool in ("git", args.runtime, "timeout") + (() if args.setup_only else ("claude",)):
        if shutil.which(tool) is None:
            sys.exit(f"[fixture] missing tool: {tool}")

    if args.setup_only:
        sb = build_sandbox(Path(tempfile.mkdtemp(prefix="openloops-fixture-")),
                           args.orchestrator_model, args.worker_model, args.permission_mode, args.runtime)
        print(f"[fixture] sandbox: {sb.root}")
        print(f"[fixture] Cycle command: {cycle_command((sb.home / 'host.md').read_text())}")
        return 0
    if args.runtime == "herdr":
        error = start_herdr_session()
        if error:
            sys.exit(f"[fixture] {error}")
    chosen = [name for name in SCENARIOS if name in (args.scenario or SCENARIOS)]
    names = [f"ol-{slug}" for name in chosen for slug in SCENARIOS[name][1]]
    leftover = [n for n in names if n in workers(args.runtime)]
    if leftover:
        sys.exit(f"[fixture] Workers {leftover} already exist; stop them first: {stop_hint(args.runtime)}")
    # For tmux, stop only the helper session at the end. For Herdr, the fixture's own session
    # (started above) is stopped at the end if all scenarios pass.
    helper = start_tmux_helper() if args.runtime == "tmux" else None
    print(f"[fixture] Runtime: {args.runtime}; watch a Worker: {attach_hint(args.runtime)}")

    results = {}
    try:
        for name in chosen:
            results[name] = SCENARIOS[name][0](args)
    finally:
        stop_workers(args.runtime, names)
        if helper:
            subprocess.run(["tmux", "kill-session", "-t", helper], capture_output=True)

    passed = len(results) == len(chosen) and all(results.values())
    if args.runtime == "herdr" and passed:
        subprocess.run(["herdr", "session", "stop", HERDR_SESSION], capture_output=True)
    print("[fixture] === Summary")
    for name, ok in results.items():
        print(f"[fixture] {name}: {'PASSED' if ok else 'FAILED'}")
    print(f"[fixture] {f'ALL {len(chosen)} SCENARIOS PASSED' if passed else 'SOME SCENARIOS FAILED'} (Runtime: {args.runtime})")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
