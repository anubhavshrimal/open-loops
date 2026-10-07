"""Offline checks for setup: the examples, the third-party data file and its installer.

Run with the other offline checks: `python3 -m unittest discover -s tests/cycle_fixture`.
The installer tests use stub `claude` and `npx` programs, so they need no network and no agent.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

import run_fixture  # noqa: E402

INSTALLER = REPO / "install-third-party.sh"
SOURCES = json.loads((REPO / "third-party.json").read_text())["sources"]

# Stubs that keep their "installed" state in files under $HOME and log every call.
STUB_CLAUDE = """#!/bin/sh
echo "claude $*" >> "$HOME/calls.log"
state="$HOME/plugins.txt"; touch "$state"
case "$*" in
  "plugin list --json") printf '['; sep=''; while read -r id; do printf '%s{"id": "%s"}' "$sep" "$id"; sep=','; done < "$state"; echo ']' ;;
  "plugin marketplace add "*) ;;
  "plugin install "*) echo "$3" >> "$state" ;;
  *) exit 1 ;;
esac
"""
STUB_NPX = """#!/bin/sh
echo "npx $*" >> "$HOME/calls.log"
state="$HOME/skills.txt"; touch "$state"
[ "$1" = --yes ] && shift
[ "$1" = skills ] || exit 1
shift
case "$1" in
  ls) printf '['; sep=''; while read -r name source; do printf '%s{"name": "%s", "source": "%s"}' "$sep" "$name" "$source"; sep=','; done < "$state"; echo ']' ;;
  add) source="$2"; shift 2
       while [ $# -gt 0 ]; do [ "$1" = --skill ] && { echo "$2 $source" >> "$state"; shift; }; shift; done ;;
  *) exit 1 ;;
esac
"""


def frontmatter(text):
    head = text.split("---", 2)[1]
    return {line.split(":", 1)[0].strip(): line.split(":", 1)[1].strip() for line in head.strip().splitlines() if ":" in line}


class ExamplesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="openloops-offline-")
        self.sb = run_fixture.build_sandbox(Path(self.tmp.name), "sonnet", "sonnet", "auto")

    def tearDown(self):
        self.tmp.cleanup()

    def test_each_sample_renders_into_a_ready_markdown_task_with_its_spec(self):
        for slug, heading in (("hello-file", "## Acceptance Criteria"), ("shorten-fib", "## Hypothesis")):
            run_fixture.write_example(self.sb, slug)
            task = self.sb.task_file(slug).read_text()
            self.assertEqual(frontmatter(task)["id"], slug)
            self.assertEqual(run_fixture.task_state(self.sb, slug), "Ready")
            self.assertIn(f"Spec: {self.sb.spec_file(slug)}", task)
            self.assertTrue(task.rstrip().endswith("## Comments"), slug)
            spec = self.sb.spec_file(slug).read_text()
            self.assertIn(heading, spec)
            self.assertEqual(frontmatter(spec)["workspace"].strip('"'), str(self.sb.project))

    def test_samples_have_the_frontmatter_fields_of_their_template(self):
        for slug, template in (("hello-file", "build-spec.md"), ("shorten-fib", "exploration-spec.md")):
            want = set(frontmatter((REPO / "core/templates" / template).read_text()))
            have = set(frontmatter((REPO / "examples/specs" / f"{slug}.md").read_text()))
            self.assertLessEqual(want, have, slug)


class ThirdPartyDataTest(unittest.TestCase):
    def test_every_source_has_the_fields_the_installer_and_credits_read(self):
        for s in SOURCES:
            for field in ("name", "repo", "author", "license", "copyright", "optional", "used_for", "skills", "install"):
                self.assertIn(field, s, s.get("name"))
            if s["skills"]:
                self.assertTrue(s["install"].get("npx", {}).get("source"), f"{s['name']}: a source with skills needs an npx route")

    def test_core_requires_mattpocock_and_superpowers(self):
        required = {s["name"] for s in SOURCES if not s["optional"]}
        self.assertEqual(required, {"mattpocock/skills", "obra/superpowers"})

    def test_notice_and_credits_match_the_data_file(self):
        result = subprocess.run([str(INSTALLER), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_check_fails_when_notice_drifts(self):
        with tempfile.TemporaryDirectory(prefix="openloops-offline-") as tmp:
            for name in ("install-third-party.sh", "third-party.json", "LICENSE", "NOTICE", "SETUP.md"):
                shutil.copy(REPO / name, Path(tmp) / name)
            (Path(tmp) / "NOTICE").write_text((REPO / "NOTICE").read_text().replace("MIT", "BSD", 1))
            result = subprocess.run([str(Path(tmp) / "install-third-party.sh"), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("NOTICE does not match", result.stdout)

    def test_no_third_party_skill_is_in_the_repo(self):
        names = {k for s in SOURCES for k in s["skills"]}
        tracked = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout.split()
        for path in tracked:
            parts = Path(path).parts
            self.assertFalse(names & set(parts[:-1]), f"{path} is in a third-party skill directory")


class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="openloops-offline-")
        self.home = Path(self.tmp.name)
        self.bin = self.home / "bin"
        self.bin.mkdir()
        for name, text in (("claude", STUB_CLAUDE), ("npx", STUB_NPX), ("codex", "#!/bin/sh\nexit 0\n")):
            (self.bin / name).write_text(text)
            (self.bin / name).chmod(0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def run_installer(self, **env):
        full = {"HOME": str(self.home), "PATH": f"{self.bin}:/usr/bin:/bin", **env}
        result = subprocess.run([str(INSTALLER)], capture_output=True, text=True, env=full)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def calls(self):
        log = self.home / "calls.log"
        return log.read_text().splitlines() if log.exists() else []

    def installs(self):
        return [c for c in self.calls() if re.match(r"(claude plugin (install|marketplace add)|npx --yes skills add) ", c)]

    def test_installs_one_route_per_agent_with_an_explicit_skill_list(self):
        out = self.run_installer()
        self.assertNotIn("warn", out)
        required = [s for s in SOURCES if s["skills"] and not s["optional"]]
        plugins = (self.home / "plugins.txt").read_text().split()
        self.assertEqual(sorted(plugins), sorted(s["install"]["claude"]["plugin"] for s in required))
        for s in required:
            add = next(c for c in self.installs() if c.startswith(f"npx --yes skills add {s['install']['npx']['source']} "))
            self.assertEqual(re.findall(r"--skill (\S+)", add), s["skills"])
            self.assertTrue(add.endswith("--agent codex"), add)

    def test_second_run_installs_nothing_and_prints_no_warning(self):
        self.run_installer()
        state = [(self.home / f).read_text() for f in ("plugins.txt", "skills.txt")]
        first = len(self.installs())
        out = self.run_installer()
        self.assertEqual(len(self.installs()), first, self.calls())
        self.assertEqual([(self.home / f).read_text() for f in ("plugins.txt", "skills.txt")], state)
        self.assertNotIn("warn", out)
        self.assertIn("already installed", out)

    def test_a_plugin_from_another_marketplace_counts_as_installed(self):
        names = [s["install"]["claude"]["plugin"].split("@")[0] for s in SOURCES if s["install"].get("claude")]
        (self.home / "plugins.txt").write_text("".join(f"{n}@another-marketplace\n" for n in names))
        self.run_installer(OPENLOOPS_NPX_AGENTS="")
        self.assertEqual(self.installs(), [])

    def test_a_plugin_in_a_project_scope_does_not_count(self):
        (self.bin / "claude").write_text(STUB_CLAUDE.replace(
            '"plugin list --json")', '"plugin list --json") echo \'[{"id": "superpowers@x", "scope": "project"}]\'; exit 0 ;; "never")'))
        self.run_installer(OPENLOOPS_NPX_AGENTS="")
        self.assertIn("superpowers@superpowers-marketplace", (self.home / "plugins.txt").read_text())

    def test_no_codex_and_no_npx_agents_works_on_claude_alone(self):
        (self.bin / "codex").unlink()
        out = self.run_installer()
        self.assertNotIn("warn", out)
        self.assertFalse([c for c in self.calls() if c.startswith("npx")])

    def test_a_failed_install_warns_and_goes_on(self):
        (self.bin / "claude").write_text("#!/bin/sh\n[ \"$*\" = 'plugin list --json' ] && echo '[]' && exit 0\nexit 1\n")
        out = self.run_installer(OPENLOOPS_NPX_AGENTS="")
        required = [s for s in SOURCES if s["skills"] and not s["optional"]]
        self.assertEqual(out.count("warn:"), len(required), out)

    def test_opt_out_variable_skips_everything(self):
        out = self.run_installer(OPENLOOPS_SKIP_THIRD_PARTY="1")
        self.assertIn("OPENLOOPS_SKIP_THIRD_PARTY=1", out)
        self.assertEqual(self.calls(), [])


class SetupDocTest(unittest.TestCase):
    """SETUP.md has every step of the setup order, in order."""

    STEPS = ["## 0. Get the repo", "## 1. Explore", "## 2. Present the findings", "## 3. Choose a tool for each Slot",
             "## 4. Ask about the project", "## 5. Optional modules", "## 6. Write the notes files",
             "## 7. Install the third-party skills", "## 8. Start the Host", "## 9. Verify with the sample Task",
             "## Re-run setup", "## Stop and remove"]

    def test_steps_are_present_in_order(self):
        text = (REPO / "SETUP.md").read_text()
        positions = [text.find(step) for step in self.STEPS]
        self.assertNotIn(-1, positions, [s for s, p in zip(self.STEPS, positions) if p == -1])
        self.assertEqual(positions, sorted(positions))

    def test_every_example_notes_file_it_names_exists(self):
        text = (REPO / "SETUP.md").read_text()
        for link in re.findall(r"\]\(([^)#]+)\)", text):
            if not link.startswith("http"):
                self.assertTrue((REPO / link).exists(), link)


if __name__ == "__main__":
    unittest.main()
