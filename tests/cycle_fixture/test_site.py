"""Offline checks for the public site in site/: local links resolve in the deploy layout, GitHub links point to
files in the repo, the Slot table names real Adapters, and no internal word is in the site."""

import hashlib
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[2]
SITE = REPO / "site"
WORKFLOW = REPO / ".github" / "workflows" / "pages.yml"
REPO_URL = "https://github.com/anubhavshrimal/open-loops"
BLOB = re.compile(re.escape(REPO_URL) + r"/(?:blob|tree)/main/([^\s\"'<>#?)]+)")
INTERNAL = ["asana", "CR-", "judge", "skin=internal", "kirocrew"]
# More internal words, as the SHA-256 of the lowercase word, so that this public repo does not hold the words
# (placeholders only, AGENTS.md rule 4). The test hashes each word, and each pair of words joined by ".", of the site.
INTERNAL_SHA256 = {
    "cbc62794911ff31b2864ecd3dbbbee7ebcb7ea41c5a42e2cba377f3cfdb42811",
    "5c8f52ca28966103ff0aad98160bc8e978c9ca0285a2043a521481d11ed17506",
    "53a86d348416924bc5276ab9ebe3884977158844127ebab3e675ea992efabb16",
    "ee57234a789755f7bce13ef959119f5307803c1368cb216fa209875941ddb2bb",
}
SLOT_TABLE = re.compile(r'<table class="slots">.*?</table>', re.S)

# Each tool that the Slot table names: its notes file in adapters/<slot>/, or (for a Notifier that has no notes
# file of its own) the text in adapters/<slot>/README.md that describes it.
SLOT_DIRS = {"Tracker": "tracker", "Host": "host", "Runtime": "runtime", "Notifier": "notifier", "Review System": "review"}
NOTES_FILE = {
    "GitHub Issues": "github-issues.md", "Markdown folder": "markdown.md",
    "cron + Claude Code": "cron-claude.md", "Codex": "cron-codex.md", "KiroCrew": "kirocrew.md", "OpenClaw": "openclaw.md",
    "herdr-core": "herdr-core.md", "Herdr": "herdr.md", "tmux": "tmux.md",
    "log file": "log-file.md",
    "GitHub PR": "github-pr.md", "Local branch": "local-branch.md",
}
README_EXAMPLE = {("Notifier", "KiroCrew"): "such as KiroCrew", ("Notifier", "an MCP server"): "A messaging MCP server"}
# The word of each default that the Default column of the Slots table in README.md must hold.
README_DEFAULT = {"GitHub Issues": "GitHub Issues", "cron + Claude Code": "Claude Code", "herdr-core": "herdr-core",
                  "log file": "log file", "GitHub PR": "GitHub PR"}


class Refs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.refs.append(value)


def pages():
    return sorted(SITE.glob("*.html"))


def site_files():
    return sorted(p for p in SITE.rglob("*") if p.is_file())


def deployed(ref):
    """The repo file that a local ref of a page serves in the deploy layout: site/ at the root, assets/ at assets/."""
    path = PurePosixPath(ref.split("#", 1)[0].split("?", 1)[0])
    if path.is_absolute() or ".." in path.parts:
        return None
    if path.parts and path.parts[0] == "assets":
        return REPO.joinpath(*path.parts)
    return SITE.joinpath(*path.parts)


def slot_rows():
    table = SLOT_TABLE.search((SITE / "index.html").read_text()).group(0)
    rows = []
    for row in re.findall(r"<tr>(.*?)</tr>", table, re.S):
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td>(.*?)</td>", row, re.S)]
        if cells:
            rows.append(cells)
    return rows


class SiteLinksTest(unittest.TestCase):
    def test_the_site_has_the_home_page_and_the_tour(self):
        self.assertEqual([p.name for p in pages()], ["index.html", "tour.html"])

    def test_every_local_href_and_src_resolves_in_the_deploy_layout(self):
        for page in pages():
            parser = Refs()
            parser.feed(page.read_text())
            local = [r for r in parser.refs if not re.match(r"[a-z]+:", r) and not r.startswith("#")]
            self.assertTrue(local, page.name)
            for ref in local:
                target = deployed(ref)
                self.assertIsNotNone(target, f"{page.name}: {ref} leaves the site")
                self.assertTrue(target.is_file(), f"{page.name}: {ref}")

    def test_every_anchor_link_names_an_id_on_its_page(self):
        for page in pages():
            text = page.read_text()
            ids = set(re.findall(r'\sid="([^"]+)"', text))
            for anchor in re.findall(r'href="#([^"]*)"', text):
                self.assertIn(anchor, ids, f"{page.name}: #{anchor}")

    def test_every_github_link_points_to_a_file_in_the_repo(self):
        found = 0
        for path in site_files():
            for target in BLOB.findall(path.read_text()):
                found += 1
                self.assertTrue((REPO / target).exists(), f"{path.name}: {target}")
        self.assertGreater(found, 0)

    def test_the_workflow_deploys_site_and_assets_in_the_layout_that_this_test_checks(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("cp -R site/. _site/", workflow)
        self.assertIn("cp -R assets _site/assets", workflow)
        self.assertIn("path: _site", workflow)
        self.assertIn("python3 -m unittest discover -s tests/cycle_fixture", workflow)


class SlotTableTest(unittest.TestCase):
    def test_each_slot_appears_once(self):
        self.assertEqual([row[0] for row in slot_rows()], list(SLOT_DIRS))

    def test_each_tool_has_a_notes_file_or_is_an_example_in_the_adapter_readme(self):
        for slot, default, others in slot_rows():
            directory = REPO / "adapters" / SLOT_DIRS[slot]
            for tool in [default] + [t.strip() for t in others.split(",")]:
                if (slot, tool) in README_EXAMPLE:
                    self.assertIn(README_EXAMPLE[slot, tool], (directory / "README.md").read_text(), f"{slot}: {tool}")
                else:
                    self.assertIn(tool, NOTES_FILE, f"{slot}: {tool} has no notes file in this test")
                    self.assertTrue((directory / NOTES_FILE[tool]).is_file(), f"{slot}: {tool}")

    def test_each_default_is_the_default_that_the_readme_names(self):
        readme = (REPO / "README.md").read_text()
        for slot, default, _ in slot_rows():
            row = re.search(rf"^\| \[{slot}\]\([^)]*\) \| [^|]* \| ([^|]*) \|", readme, re.M)
            self.assertIsNotNone(row, slot)
            self.assertIn(README_DEFAULT[default], row.group(1), slot)


class SiteWordsTest(unittest.TestCase):
    def test_no_internal_word_is_in_the_site(self):
        for path in site_files():
            text = path.read_text()
            for word in INTERNAL:
                # KiroCrew is a Host example, so only the Slot table may name it.
                checked = SLOT_TABLE.sub("", text) if word == "kirocrew" else text
                self.assertNotIn(word.lower(), checked.lower(), f"{path.name}: {word}")
            words = re.findall(r"[a-z0-9]+", text.lower())
            for word in words + [a + "." + b for a, b in zip(words, words[1:])]:
                self.assertNotIn(hashlib.sha256(word.encode()).hexdigest(), INTERNAL_SHA256, f"{path.name}: {word}")

    def test_the_slot_table_names_kirocrew_only_because_it_has_a_host_notes_file(self):
        self.assertTrue((REPO / "adapters" / "host" / "kirocrew.md").is_file())


if __name__ == "__main__":
    unittest.main()
