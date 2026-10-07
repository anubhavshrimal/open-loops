#!/usr/bin/env python3
"""Setup dry run: a fresh agent session follows SETUP.md in a temp HOME, then the Cycle fixture runs on its notes files.

1. Build a fixture sandbox with an empty Open Loops home directory at the default place,
   <temp HOME>/.openloops/.
2. Start a new `claude -p` session with HOME set to the temp HOME. Its prompt is the setup
   prompt of the README plus the Owner's answers: all local fallbacks (Markdown Tracker,
   cron + `claude -p` Host, tmux Runtime, log-file Notifier, Local branch Review System), no
   optional modules, third-party installs skipped. It stops before "Start the Host": it never
   changes the crontab.
3. Check the result on disk: the five notes files exist, no placeholder is left, each names the
   sandbox's values, the core agents are installed, and nothing outside the home directory changed.
4. Run the fixture's `build` scenario in the same sandbox, with the notes files that setup wrote:
   the sample Build Task must reach In Review.

It uses a real agent and costs tokens. Run it on demand, from a normal shell (see README.md).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_fixture  # noqa: E402
from run_fixture import REPO, Checks, build_sandbox, cycle_command  # noqa: E402

PROMPT = """Set up Open Loops from {repo}. It is a local clone of the repo: use it in place, do not clone it again. Follow {repo}/SETUP.md.

This is an unattended dry run: there is no Owner to ask. Where SETUP.md says to ask the Owner, take the answer below; where no answer is given, take the recommended default. Where SETUP.md says to ask before a change outside the home directory, the answer is no.

The Owner's answers:
- Home directory: the default, ~/.openloops/ ({home}).
- Tracker: Markdown files. Task directory: {tracker} (it exists).
- Host: cron + `claude -p`. Orchestrator model: {orchestrator_model}. Interval: the default.
- Permission mode: auto, for the Orchestrator and for the Workers. I accept the risk.
- Runtime: tmux, with Claude Code Workers. Worker model: {worker_model}. Cap: the default. The Specs are in {specs}.
- Notifier: the log file, at the default path.
- Review System: Local branch.
- Project repo: {project}. Build and test command: `sh check.sh`. Follow-up prefix: the default.
- Optional modules: no to each.
- Third-party skills: run the installer as step 7 says (OPENLOOPS_SKIP_THIRD_PARTY=1 is set here).
- Step 8 (Start the Host) and step 9 (Verify): skip both in this dry run. Do not change the crontab and do not start a Cycle. Stop after step 7.

At the end, list the files that you wrote."""


def crontab():
    out = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else ""


def repo_status():
    return subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True).stdout


def check_notes(sb, args, checks):
    check = checks.check
    written = [name for name in run_fixture.NOTES_FILES if (sb.home / name).exists()]
    for name in run_fixture.NOTES_FILES:
        check(f"setup wrote {name}", name in written, str(sb.home / name))
    if len(written) < len(run_fixture.NOTES_FILES):
        return
    text = {name: (sb.home / name).read_text() for name in run_fixture.NOTES_FILES}
    for name, body in text.items():
        left = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", body)))
        check(f"{name} has no placeholder left", not left, left)
    check("tracker.md is the Markdown Tracker with the sandbox Task directory",
          "Markdown files" in text["tracker.md"] and f"Task directory: `{sb.tracker}`" in text["tracker.md"])
    check("tracker.md has the default Follow-up prefix", "Follow-up prefix: `ACTION:`" in text["tracker.md"])
    try:
        command = cycle_command(text["host.md"])
    except (IndexError, AttributeError):
        command = ""
    check("host.md has a Cycle command with `claude -p`, the core prompt and the home directory",
          "claude -p" in command and f"{REPO}/core/orchestrator.md" in command and str(sb.home) in command, command)
    check("host.md runs the Orchestrator in auto mode with the chosen model",
          "--permission-mode auto" in command and f"--model {args.orchestrator_model}" in command, command)
    check("host.md keeps the 30-minute interval and the 25-minute timeout",
          "Interval: 30 minutes" in text["host.md"] and "*/30 * * * *" in text["host.md"] and "timeout 25m" in command)
    runtime = text["runtime.md"]
    check("runtime.md is tmux with the chosen Worker model in auto mode",
          "tmux new-session" in runtime and f"claude --model {args.worker_model}" in runtime and "--permission-mode auto" in runtime)
    check("runtime.md gives the Workers the home, Task and Spec directories",
          all(f"--add-dir {d}" in runtime for d in (sb.home, sb.tracker, sb.specs)))
    check("notifier.md is the log file at the default path", f"Log file: `{sb.notifier_log}`" in text["notifier.md"])
    check("review.md is the Local branch with the project and its build and test command",
          "Local branch" in text["review.md"] and f"| `{sb.project}` | `sh check.sh` |" in text["review.md"])
    agent = sb.home / ".claude/agents/auto-researcher.md"
    check("setup installed the core agents in the home directory",
          agent.exists() and agent.read_text() == (REPO / "core/agents/auto-researcher.md").read_text())
    check("setup made no state.json", not sb.state_file.exists())


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--setup-model", default="sonnet", help="model of the setup agent")
    parser.add_argument("--setup-timeout-minutes", type=float, default=20)
    parser.add_argument("--no-fixture", action="store_true", help="stop after the notes-file checks")
    run_fixture.add_agent_options(parser)
    args = parser.parse_args()
    args.runtime = "tmux"

    for tool in ("git", "tmux", "timeout", "claude", "crontab"):
        if shutil.which(tool) is None:
            sys.exit(f"[dry-run] missing tool: {tool}")

    root = Path(tempfile.mkdtemp(prefix="openloops-setup-dry-run-"))
    owner_home = root / "owner"
    sb = build_sandbox(root, args.orchestrator_model, args.worker_model, args.permission_mode,
                       home=owner_home / ".openloops", notes=False)
    print(f"[dry-run] sandbox: {root}")
    print(f"[dry-run] temp HOME: {owner_home}")

    prompt = PROMPT.format(repo=REPO, home=sb.home, tracker=sb.tracker, specs=sb.specs, project=sb.project,
                           orchestrator_model=args.orchestrator_model, worker_model=args.worker_model)
    env = dict(os.environ, HOME=str(owner_home), OPENLOOPS_SKIP_THIRD_PARTY="1")
    crontab_before, repo_before = crontab(), repo_status()
    log = root / "setup-session.log"
    command = ["claude", "-p", prompt, "--model", args.setup_model, "--permission-mode", args.permission_mode,
               "--add-dir", str(REPO)]
    print(f"[dry-run] setup session: claude -p <setup prompt> --model {args.setup_model} "
          f"--permission-mode {args.permission_mode}; log: {log}")
    with log.open("w") as out:
        try:
            code = subprocess.run(command, cwd=root, env=env, stdout=out, stderr=subprocess.STDOUT,
                                  timeout=args.setup_timeout_minutes * 60).returncode
        except subprocess.TimeoutExpired:
            code = "timeout"
    print(f"[dry-run] setup session exit: {code}")

    checks = Checks("setup dry run")
    checks.check("the setup session exited 0", code == 0, f"exit {code}")
    check_notes(sb, args, checks)
    checks.check("the crontab is unchanged", crontab() == crontab_before)
    repo_after = repo_status()
    checks.check("the Open Loops repo is unchanged", repo_after == repo_before, repo_after)
    print(f"[dry-run] SETUP DRY RUN {'PASSED' if checks.passed else 'FAILED'}")
    if not checks.passed or args.no_fixture:
        print(f"[dry-run] inspect: {root}")
        return 0 if checks.passed else 1

    helper = run_fixture.start_tmux_helper()
    try:
        passed = run_fixture.scenario_build(args, sb=sb)
    finally:
        run_fixture.stop_workers("tmux", ["ol-hello-file"])
        if helper:
            subprocess.run(["tmux", "kill-session", "-t", helper], capture_output=True)
    print(f"[dry-run] {'SETUP DRY RUN AND FIXTURE PASSED' if passed else 'FIXTURE FAILED'} (sandbox: {root})")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
