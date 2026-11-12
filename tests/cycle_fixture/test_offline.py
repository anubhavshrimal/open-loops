"""Offline checks that need no agent: run with `python3 -m unittest discover tests/cycle_fixture`."""

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

import run_fixture  # noqa: E402
from schema_check import schema_errors  # noqa: E402

SCHEMA = json.loads((REPO / "core/state.schema.json").read_text())

GOOD_STATE = {
    "ol-hello-file": {
        "task_id": "hello-file",
        "spec": "/tmp/specs/hello-file.md",
        "workspace": "/tmp/project/.openloops/worktrees/hello-file",
        "runtime_ids": {"tmux_session": "ol-hello-file"},
        "started": "2026-10-06T22:31:04-07:00",
        "status": "working",
        "review_state": {"last_comment_id": None},
        "pending_prompt": None,
        "gap_fill_done": "pending",
        "blocked_notified": False,
    },
    "chain_stalled_notified": {"child-b": "child-a"},
    "alerts": {"tracker": {"since": "2026-10-06T22:31:04-07:00", "message": "directory unreadable"}},
}


class StateSchemaTest(unittest.TestCase):
    def test_accepts_a_full_state(self):
        self.assertEqual(schema_errors(GOOD_STATE, SCHEMA), [])

    def test_accepts_an_empty_state(self):
        self.assertEqual(schema_errors({}, SCHEMA), [])

    def test_rejects_a_record_without_task_id(self):
        state = json.loads(json.dumps(GOOD_STATE))
        del state["ol-hello-file"]["task_id"]
        self.assertTrue(schema_errors(state, SCHEMA))

    def test_rejects_an_unknown_status(self):
        state = json.loads(json.dumps(GOOD_STATE))
        state["ol-hello-file"]["status"] = "done"
        self.assertTrue(schema_errors(state, SCHEMA))

    def test_rejects_an_unknown_top_level_key(self):
        self.assertTrue(schema_errors({"sessions": {}}, SCHEMA))

    def test_rejects_an_alert_for_an_unknown_slot(self):
        self.assertTrue(schema_errors({"alerts": {"wiki": {"since": "x"}}}, SCHEMA))

    def test_gap_fill_done_accepts_only_true_or_pending(self):
        state = json.loads(json.dumps(GOOD_STATE))
        state["ol-hello-file"]["gap_fill_done"] = False
        self.assertTrue(schema_errors(state, SCHEMA))


class SandboxTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="openloops-offline-")
        self.sb = run_fixture.build_sandbox(Path(self.tmp.name), "sonnet", "sonnet", "auto")
        run_fixture.write_spec(self.sb, "hello-file", "Add hello.txt", "Add `hello.txt`.", "`hello.txt` exists.")
        run_fixture.write_task(self.sb, "hello-file", "Add hello.txt", "Ready", comments=[("owner", "ACTION: go.")])

    def tearDown(self):
        self.tmp.cleanup()

    def test_home_has_the_five_notes_files_with_no_placeholders(self):
        for name in run_fixture.NOTES_FILES:
            text = (self.sb.home / name).read_text()
            self.assertNotRegex(text, r"\{\{[A-Z_]+\}\}", name)
        self.assertIn(str(self.sb.tracker), (self.sb.home / "tracker.md").read_text())
        self.assertIn("hc run --bg --json --name ol-<slug>", (self.sb.home / "runtime.md").read_text())

    def test_cycle_command_runs_the_core_prompt_under_timeout(self):
        command = run_fixture.cycle_command((self.sb.home / "host.md").read_text())
        self.assertIn("timeout 25m claude -p", command)
        self.assertIn(str(REPO / "core/orchestrator.md"), command)
        self.assertIn(f"Home directory: {self.sb.home}", command)

    def test_task_file_round_trips_state_spec_and_comments(self):
        self.assertEqual(run_fixture.task_state(self.sb, "hello-file"), "Ready")
        self.assertIn(f"Spec: {self.sb.specs}/hello-file.md", self.sb.task_file("hello-file").read_text())
        comments = run_fixture.task_comments(self.sb, "hello-file")
        self.assertEqual(len(comments), 1)
        self.assertRegex(comments[0], r"^c1 \| .+ \| owner\nACTION: go\.$")

    def test_spec_has_no_placeholders_and_lists_dependencies(self):
        spec = run_fixture.write_spec(self.sb, "b", "B", "Add b.", "b exists.", depends_on=["a"], spec_status="draft")
        text = spec.read_text()
        self.assertIn('depends_on: ["a"]', text)
        self.assertIn('spec_status: "draft"', text)
        self.assertNotRegex(text, r"\{\{[A-Z_]+\}\}")

    def test_task_branch_is_a_worktree_with_one_commit(self):
        sha = run_fixture.make_task_branch(self.sb, "hello-file", "hello.txt", "Hi.")
        log = run_fixture.git("log", "--format=%H", "main..ol-hello-file", cwd=self.sb.project).stdout.split()
        self.assertEqual(log, [sha])
        self.assertTrue((self.sb.worktree("hello-file") / "hello.txt").exists())

    def test_state_written_for_a_mid_loop_scenario_validates(self):
        record = run_fixture.worker_record(self.sb, "hello-file", "blocked", blocked_notified=True)
        run_fixture.write_state(self.sb, {"ol-hello-file": record})
        self.assertEqual(run_fixture.state_errors(self.sb), [])

    def test_owner_moves_a_task(self):
        run_fixture.set_task_state(self.sb, "hello-file", "Done")
        self.assertEqual(run_fixture.task_state(self.sb, "hello-file"), "Done")
        self.assertEqual(len(run_fixture.task_comments(self.sb, "hello-file")), 1)

    def test_every_scenario_has_unique_worker_slugs(self):
        slugs = [slug for _, names in run_fixture.SCENARIOS.values() for slug in names]
        self.assertEqual(len(slugs), len(set(slugs)))
        # 13 scenarios for every Runtime, plus the ones that only one Runtime has.
        self.assertEqual(len(run_fixture.SCENARIOS), 13 + len(run_fixture.RUNTIME_SCENARIOS))

    def test_notifications_parse_event_names(self):
        self.sb.notifier_log.write_text("2026-10-06T22:31:04-07:00 spawned Picked up\n2026-10-06T22:32:04-07:00 done Done\n")
        self.assertEqual(run_fixture.events(self.sb), ["spawned", "done"])

    def test_project_main_matches_the_local_origin(self):
        local = run_fixture.git("rev-parse", "main", cwd=self.sb.project).stdout
        remote = run_fixture.git("--git-dir", str(self.sb.origin), "rev-parse", "main").stdout
        self.assertEqual(local, remote)

    def test_build_and_test_command_passes_on_main(self):
        result = subprocess.run(["sh", "check.sh"], cwd=self.sb.project, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)


class ExplorationSandboxTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="openloops-offline-")
        files = (run_fixture.CHECK_SH, REPO / "examples/files/fib.py", REPO / "examples/files/measure.sh")
        self.sb = run_fixture.build_sandbox(Path(self.tmp.name), "sonnet", "sonnet", "auto", project_files=files)
        run_fixture.write_example(self.sb, "shorten-fib")

    def tearDown(self):
        self.tmp.cleanup()

    def test_home_has_the_exploration_worker_agent(self):
        installed = self.sb.home / ".claude/agents/auto-researcher.md"
        self.assertEqual(installed.read_text(), (REPO / "core/agents/auto-researcher.md").read_text())
        self.assertIn("--agent auto-researcher", (self.sb.home / "runtime.md").read_text())
        self.assertIn(f"--add-dir {self.sb.home}", (self.sb.home / "runtime.md").read_text())

    def test_task_starts_ready_and_names_an_exploration_spec(self):
        self.assertEqual(run_fixture.task_state(self.sb, "shorten-fib"), "Ready")
        spec = (self.sb.specs / "shorten-fib.md").read_text()
        self.assertIn(f"Spec: {self.sb.specs}/shorten-fib.md", self.sb.task_file("shorten-fib").read_text())
        self.assertIn("## Hypothesis", spec)
        self.assertIn('agent: "auto-researcher"', spec)
        self.assertIn("10 minutes", spec)

    def test_run_command_gives_the_baseline_metric(self):
        result = subprocess.run(["sh", "measure.sh"], cwd=self.sb.project, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertRegex(result.stdout, r"^lines: [0-9]+$")

    def test_results_rows_needs_a_tab_separated_header(self):
        self.sb.state_path("shorten-fib").mkdir(parents=True)
        self.assertIsNone(run_fixture.results_rows(self.sb, "shorten-fib"))
        (self.sb.state_path("shorten-fib") / "results.tsv").write_text("experiment_id\tmetric_value\n001\t21\n")
        self.assertEqual(run_fixture.results_rows(self.sb, "shorten-fib"), ["001\t21"])


class SpecTemplatesTest(unittest.TestCase):
    def frontmatter_keys(self, name):
        head = (REPO / "core/templates" / name).read_text().split("---", 2)[1]
        return {line.split(":", 1)[0] for line in head.strip().splitlines()}

    def test_both_templates_have_the_generic_fields(self):
        for name in ("build-spec.md", "exploration-spec.md"):
            keys = self.frontmatter_keys(name)
            for field in ("tracker_id", "report", "workspace", "branch", "depends_on", "spec_status"):
                self.assertIn(field, keys, f"{name}: {field}")

    def test_exploration_template_names_its_agent(self):
        self.assertIn("agent", self.frontmatter_keys("exploration-spec.md"))
        self.assertTrue((REPO / "core/agents/auto-researcher.md").exists())


class RuntimeSandboxTest(unittest.TestCase):
    def test_the_default_runtime_is_herdr_core(self):
        self.assertEqual(run_fixture.NOTES_FILES["runtime.md"], REPO / "adapters/runtime/herdr-core.md")

    def test_tmux_runtime_fills_the_tmux_notes_file(self):
        with tempfile.TemporaryDirectory(prefix="openloops-offline-") as tmp:
            sb = run_fixture.build_sandbox(Path(tmp), "sonnet", "sonnet", "auto", runtime="tmux")
            runtime_md = (sb.home / "runtime.md").read_text()
        self.assertNotRegex(runtime_md, r"\{\{[A-Z_]+\}\}")
        self.assertIn("tmux new-session -d -s ol-<slug>", runtime_md)

    def test_herdr_runtime_fills_the_herdr_notes_file(self):
        with tempfile.TemporaryDirectory(prefix="openloops-offline-") as tmp:
            sb = run_fixture.build_sandbox(Path(tmp), "sonnet", "sonnet", "auto", runtime="herdr")
            runtime_md = (sb.home / "runtime.md").read_text()
        self.assertNotRegex(runtime_md, r"\{\{[A-Z_]+\}\}")
        self.assertIn("herdr agent start ol-<slug> --kind claude", runtime_md)
        self.assertIn(f"--add-dir {sb.tracker}", runtime_md)

    def test_herdr_core_runtime_fills_the_herdr_core_notes_file(self):
        with tempfile.TemporaryDirectory(prefix="openloops-offline-") as tmp:
            sb = run_fixture.build_sandbox(Path(tmp), "sonnet", "sonnet", "auto", runtime="herdr-core")
            runtime_md = (sb.home / "runtime.md").read_text()
        self.assertNotRegex(runtime_md, r"\{\{[A-Z_]+\}\}")
        self.assertIn("hc run --bg --json --name ol-<slug>", runtime_md)
        self.assertIn('"$(command -v claude)" --model sonnet --permission-mode auto', runtime_md)
        self.assertIn(f"--add-dir {sb.tracker}", runtime_md)

    def test_the_no_core_scenario_runs_only_with_herdr_core(self):
        self.assertEqual(run_fixture.RUNTIME_SCENARIOS, {"no-core": "herdr-core"})
        self.assertEqual(set(run_fixture.RUNTIME_TOOLS), set(run_fixture.RUNTIMES))



class HerdrCoreCommandsTest(unittest.TestCase):
    """Run the shell commands of herdr-core.md against a stub `hc` and temp sockets: the core check
    must start no core, and a failed `hc read` must not pass as empty output."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="openloops-offline-")
        root = Path(self.tmp.name)
        self.marker = root / "hc-was-called"
        self.bin = root / "bin"
        self.bin.mkdir()
        stub = self.bin / "hc"
        stub.write_text(f"#!/bin/sh\ntouch {self.marker}\necho '{{\"error\":{{}}}}' >&2\nexit 3\n")
        stub.chmod(0o755)
        self.notes = (REPO / "adapters/runtime/herdr-core.md").read_text()

    def tearDown(self):
        self.tmp.cleanup()

    def block_after(self, heading):
        return re.search(r"```sh\n(.*?)```", self.notes.split(heading, 1)[1], re.S).group(1).strip()

    def run_sh(self, command, **env):
        full = {"PATH": f"{self.bin}:/usr/bin:/bin", "HOME": self.tmp.name, **env}
        return subprocess.run(["sh", "-c", command], env=full, capture_output=True, text=True)

    def test_core_check_fails_with_no_core_and_starts_none(self):
        check = self.block_after("Core check, once per Cycle")
        result = self.run_sh(check, XDG_RUNTIME_DIR=self.tmp.name, HC_SESSION="nocore")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.marker.exists(), "the core check ran hc")

    def test_core_check_passes_when_the_core_socket_answers(self):
        import socket
        check = self.block_after("Core check, once per Cycle")
        sock_dir = Path(self.tmp.name) / "herdr-core"
        sock_dir.mkdir()
        server = socket.socket(socket.AF_UNIX)
        server.bind(str(sock_dir / "fixture.sock"))
        server.listen(1)
        try:
            result = self.run_sh(check, XDG_RUNTIME_DIR=self.tmp.name, HC_SESSION="fixture")
        finally:
            server.close()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.marker.exists(), "the core check ran hc")

    def test_a_failed_read_exits_with_an_error(self):
        read = self.block_after("## Read recent output").replace("<address>", "t9")
        result = self.run_sh(read)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


    def test_name_check_takes_29_slug_characters_and_no_more(self):
        check = self.block_after("Name check, before the core makes the Workspace")
        for slug, ok in (("a" * 29, True), ("a" * 30, False), ("Paper-plan", False), ("paper.plan", False), ("hello-file", True)):
            result = self.run_sh(check.replace("<slug>", slug))
            self.assertEqual(result.returncode == 0, ok, slug)

    def test_every_fixture_worker_name_passes_the_name_check(self):
        check = self.block_after("Name check, before the core makes the Workspace")
        for _, slugs in run_fixture.SCENARIOS.values():
            for slug in slugs:
                self.assertEqual(self.run_sh(check.replace("<slug>", slug)).returncode, 0, slug)


class FixtureCoreIsolationTest(unittest.TestCase):
    """The fixture starts its own hc core: Owner hc variables in the environment never reach it."""

    def test_start_hc_core_drops_the_owner_variables_and_selects_its_own_session(self):
        import os
        from unittest import mock
        with tempfile.TemporaryDirectory(prefix="openloops-offline-") as tmp:
            stub_dir = Path(tmp) / "bin"
            stub_dir.mkdir()
            seen = Path(tmp) / "env.json"
            stub = stub_dir / "hc"
            stub.write_text(f"#!/bin/sh\nexec {sys.executable} -c 'import json, os; json.dump(dict(os.environ), open(\"{seen}\", \"w\"))'\n")
            stub.chmod(0o755)
            owner = {"HC_SESSION": "default", "HC_SOCKET": "/owner/default.sock", "HC_TERMINAL_ID": "t1",
                     "HC_TERMINAL_SOCKET": "/owner/t1.sock", "PATH": f"{stub_dir}:{os.environ['PATH']}"}
            with mock.patch.dict(os.environ, owner), mock.patch.dict(run_fixture.HC_DIRS, clear=True), \
                    mock.patch.object(run_fixture, "hc_core_runs", return_value=True):
                self.assertIsNone(run_fixture.start_hc_core())
                after = dict(os.environ)
                dirs = dict(run_fixture.HC_DIRS)
            core_env = json.loads(seen.read_text())
        for env in (core_env, after):
            self.assertEqual(env["HC_SESSION"], run_fixture.HC_SESSION)
            self.assertNotEqual(env["HC_SESSION"], "default")
            for key in ("HC_SOCKET", "HC_TERMINAL_ID", "HC_TERMINAL_SOCKET"):
                self.assertNotIn(key, env)
            for key, value in dirs.items():
                self.assertEqual(env[key], value)
                self.assertTrue(value.startswith(tempfile.gettempdir()), value)


class CoreIsAgentNeutralTest(unittest.TestCase):
    SLOT_PRODUCTS = re.compile(r"asana|github|herdr|tmux|slack|gitlab|linear|claude|codex|kirocrew|openclaw", re.I)

    def test_core_names_no_slot_product(self):
        for path in sorted((REPO / "core").rglob("*")):
            if path.is_file():
                for number, line in enumerate(path.read_text().splitlines(), 1):
                    self.assertIsNone(self.SLOT_PRODUCTS.search(line), f"{path.relative_to(REPO)}:{number}: {line}")


class ContractMapTest(unittest.TestCase):
    """Each row of a Contract map names a heading or quoted text that exists in the example notes file."""

    def test_every_contract_map_row_points_at_text_in_the_example(self):
        for readme in sorted((REPO / "adapters").glob("*/README.md")):
            text = readme.read_text()
            maps = re.findall(r"## Contract map: `([^`]+)`\n(.*?)(?:\n## |\Z)", text, re.S)
            self.assertTrue(maps, f"{readme} has no Contract map")
            for example_name, table in maps:
                example = (readme.parent / example_name).read_text()
                rows = [r for r in table.strip().splitlines()[2:] if r.startswith("|")]
                self.assertTrue(rows, f"{readme}: empty Contract map")
                for row in rows:
                    where = row.strip("|").split("|")[-1]
                    targets = re.findall(r'"([^"]+)"', where) + re.findall(r"`([^`]+)`", where)
                    self.assertTrue(targets, f"{readme}: row has no target: {row}")
                    for target in targets:
                        self.assertIn(target, example, f"{readme}: {target!r} not in {example_name}")


if __name__ == "__main__":
    unittest.main()
