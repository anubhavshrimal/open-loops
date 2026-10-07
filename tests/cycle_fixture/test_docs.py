"""Offline checks for the top-level docs: links resolve, and SPEC.md states the same Contracts as adapters/."""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LINKED_FROM_README = ["SPEC.md", "SETUP.md", "AGENTS.md", "GLOSSARY.md", "docs/quickstart.md", "docs/troubleshooting.md",
                      "docs/design-decisions.md"]
DOCS = ["README.md", "SPEC.md", "AGENTS.md", "CLAUDE.md"] + [d for d in LINKED_FROM_README if d.startswith("docs/")]
SLOTS = {"Tracker": "tracker", "Host": "host", "Runtime": "runtime", "Notifier": "notifier", "Review System": "review"}
LINK = re.compile(r"\]\(([^)\s]+)\)")


def section(text, heading):
    """The lines under `heading` up to the next heading of the same or a higher level."""
    depth = len(heading.split(" ", 1)[0])
    lines = text.splitlines()
    assert heading in lines, f"missing heading: {heading}"
    start = lines.index(heading) + 1
    for i in range(start, len(lines)):
        if re.match(rf"#{{1,{depth}}} ", lines[i]):
            return lines[start:i]
    return lines[start:]


def checklist(lines):
    return [line for line in lines if line.startswith("- [ ] ")]


class DocLinksTest(unittest.TestCase):
    def test_every_relative_link_resolves_to_a_file_in_the_repo(self):
        for doc in DOCS:
            path = REPO / doc
            for target in LINK.findall(path.read_text()):
                if re.match(r"[a-z]+:", target) or target.startswith("#"):
                    continue
                resolved = (path.parent / target.split("#", 1)[0]).resolve()
                self.assertTrue(resolved.exists(), f"{doc}: {target}")
                self.assertTrue(resolved.is_relative_to(REPO), f"{doc}: {target} is outside the repo")

    def test_readme_links_every_doc(self):
        readme = (REPO / "README.md").read_text()
        for doc in LINKED_FROM_README:
            self.assertIn(f"]({doc})", readme, doc)

    def test_readme_shows_install_and_verify_before_how_it_works(self):
        readme = (REPO / "README.md").read_text()
        self.assertLess(readme.index("## Quick start"), readme.index("## How it works"))
        self.assertLess(readme.index("**Verify.**"), readme.index("## How it works"))


class SpecContractsTest(unittest.TestCase):
    def test_spec_states_the_same_capabilities_as_each_adapter_readme(self):
        spec = (REPO / "SPEC.md").read_text()
        for slot, directory in SLOTS.items():
            readme = (REPO / "adapters" / directory / "README.md").read_text()
            expected = checklist(section(readme, "## Contract"))
            self.assertTrue(expected, slot)
            self.assertEqual(checklist(section(spec, f"### {slot}")), expected, slot)


class AgentsTest(unittest.TestCase):
    def test_agents_md_has_the_spec_rule_and_claude_md_points_to_it(self):
        self.assertIn("Update `SPEC.md` in the same change as a behavior change", (REPO / "AGENTS.md").read_text())
        self.assertIn("@AGENTS.md", (REPO / "CLAUDE.md").read_text())


if __name__ == "__main__":
    unittest.main()
