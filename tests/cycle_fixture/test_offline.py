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

    def tearDown(self):
        self.tmp.cleanup()

    def test_home_has_the_five_notes_files_with_no_placeholders(self):
        for name in run_fixture.NOTES_FILES:
            text = (self.sb.home / name).read_text()
            self.assertNotRegex(text, r"\{\{[A-Z_]+\}\}", name)
        self.assertIn(str(self.sb.tracker), (self.sb.home / "tracker.md").read_text())
        self.assertIn("tmux new-session -d -s ol-<slug>", (self.sb.home / "runtime.md").read_text())

    def test_cycle_command_runs_the_core_prompt_under_timeout(self):
        command = run_fixture.cycle_command((self.sb.home / "host.md").read_text())
        self.assertIn("timeout 25m claude -p", command)
        self.assertIn(str(REPO / "core/orchestrator.md"), command)
        self.assertIn(f"Home directory: {self.sb.home}", command)

    def test_task_starts_ready_and_names_its_spec(self):
        self.assertEqual(run_fixture.task_state(self.sb), "Ready")
        self.assertIn(f"Spec: {self.sb.specs}/hello-file.md", self.sb.task_file.read_text())
        self.assertEqual(run_fixture.task_comments(self.sb), [])

    def test_project_main_matches_the_local_origin(self):
        local = run_fixture.git("rev-parse", "main", cwd=self.sb.project).stdout
        remote = run_fixture.git("--git-dir", str(self.sb.origin), "rev-parse", "main").stdout
        self.assertEqual(local, remote)

    def test_build_and_test_command_passes_on_main(self):
        result = subprocess.run(["sh", "check.sh"], cwd=self.sb.project, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)


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
