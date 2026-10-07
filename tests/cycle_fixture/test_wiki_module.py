"""Offline checks for the optional wiki module in modules/wiki/.

Run with the other offline checks: `python3 -m unittest discover -s tests/cycle_fixture`.
"""

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MODULE = REPO / "modules/wiki"
SCAFFOLD = MODULE / "scaffold"
EXAMPLE = MODULE / "example/wiki"
PAGE_TEMPLATES = ("source-summary", "entity", "concept", "comparison", "synthesis")
SPEC_TEMPLATES = ("build-spec", "exploration-spec")
WIKILINK = re.compile(r"\[\[([^\]|#]+)")
INLINE_CODE = re.compile(r"`[^`]*`")


def wikilinks(text):
    return set(WIKILINK.findall(INLINE_CODE.sub("", text)))


def frontmatter(text):
    head = text.split("---", 2)[1]
    return {line.split(":", 1)[0].strip(): line.split(":", 1)[1].strip() for line in head.strip().splitlines() if ":" in line and not line.startswith(" ")}


def wiki_setup_section():
    text = (REPO / "SETUP.md").read_text()
    return text[text.index("### wiki"):text.index("## 6. Write the notes files")]


def wiki_setup_commands(wiki):
    """The shell block of the wiki question in SETUP.md, with its placeholders filled."""
    block = re.search(r"```sh\n(.*?)```", wiki_setup_section(), re.S).group(1)
    return block.replace("<wiki>", str(wiki)).replace("<clone>", str(REPO)).replace("<core>", str(REPO / "core"))


class ManualTest(unittest.TestCase):
    def test_manual_keeps_every_workflow(self):
        manual = (SCAFFOLD / "AGENTS.md").read_text()
        for heading in ("## 2. Session Protocol", "### 6a. Ingest", "### 6b. Ingest", "### 6c. Query", "### 6d. Lint",
                        "## 8. Conventions", "## 11. Shared Vocabulary", "## 12. Idea Forge Pipeline",
                        "### Stage 1: Capture", "### Stage 2: Refine", "### Stage 3: Track", "### Stage 4: Execute"):
            self.assertIn(heading, manual)

    def test_manual_links_the_example_and_credits_the_pattern(self):
        manual = (SCAFFOLD / "AGENTS.md").read_text()
        self.assertIn("](../example/wiki/index.md)", manual)
        self.assertTrue((SCAFFOLD / "../example/wiki/index.md").exists())
        for text in (manual, (MODULE / "README.md").read_text()):
            self.assertIn("Karpathy", text)

    def test_claude_md_points_to_the_manual(self):
        self.assertIn("`AGENTS.md`", (SCAFFOLD / "CLAUDE.md").read_text())

    def test_every_page_template_is_present(self):
        for name in PAGE_TEMPLATES:
            self.assertEqual(frontmatter((SCAFFOLD / f"wiki/.templates/{name}.md").read_text())["type"], name)


class ExampleWikiTest(unittest.TestCase):
    def pages(self):
        return sorted(p for p in EXAMPLE.rglob("*.md") if p.name not in ("index.md", "log.md", "GLOSSARY.md"))

    def test_has_one_hub_one_entity_glossary_index_and_log(self):
        self.assertEqual([p.relative_to(EXAMPLE).as_posix() for p in self.pages()],
                         ["projects/hubs/recipe-scaler.md", "research/entities/pint.md"])
        for name in ("index.md", "log.md", "GLOSSARY.md"):
            self.assertTrue((EXAMPLE / name).exists(), name)

    def test_pages_have_the_required_frontmatter(self):
        for page in self.pages():
            fields = frontmatter(page.read_text())
            for field in ("title", "type", "section", "tags", "created", "updated"):
                self.assertIn(field, fields, page)

    def test_every_wikilink_resolves_and_links_go_both_ways(self):
        names = {p.stem for p in self.pages()}
        links = {p.stem: wikilinks(p.read_text()) for p in self.pages()}
        for page, targets in links.items():
            self.assertLessEqual(targets, names, page)
            for target in targets:
                self.assertIn(page, links[target], f"{target} does not link back to {page}")
        self.assertEqual(wikilinks((EXAMPLE / "index.md").read_text()), names)

    def test_log_entries_use_the_log_format(self):
        entries = [line for line in (EXAMPLE / "log.md").read_text().splitlines() if line.startswith("## ")]
        self.assertTrue(entries)
        for line in entries:
            self.assertRegex(line, r"^## \[\d{4}-\d{2}-\d{2}\] (ingest|query|lint|init|update) \| .+")


class SetupTest(unittest.TestCase):
    def test_setup_asks_one_yes_no_question_with_default_no_and_states_the_spec_rule(self):
        section = wiki_setup_section()
        self.assertIn("(yes/no, default no)", section)
        self.assertIn("`Spec:` line may point to a wiki page", section)
        self.assertIn("--add-dir <wiki>", section)

    def test_setup_commands_make_a_wiki_and_never_overwrite_one(self):
        with tempfile.TemporaryDirectory(prefix="openloops-wiki-") as tmp:
            wiki = Path(tmp) / "llm-wiki"
            subprocess.run(["sh", "-ec", wiki_setup_commands(wiki)], check=True)
            for name in PAGE_TEMPLATES + SPEC_TEMPLATES:
                self.assertTrue((wiki / f"wiki/.templates/{name}.md").exists(), name)
            for path in ("AGENTS.md", "CLAUDE.md", ".gitignore", "wiki/index.md", "wiki/log.md", "wiki/GLOSSARY.md",
                         "raw", "wiki/projects/hubs", "wiki/projects/sources"):
                self.assertTrue((wiki / path).exists(), path)
            self.assertFalse((wiki / "projects").exists())

            (wiki / "AGENTS.md").write_text("the Owner's own manual\n")
            (wiki / "wiki/log.md").write_text("the Owner's log\n")
            subprocess.run(["sh", "-ec", wiki_setup_commands(wiki)], check=True)
            self.assertEqual((wiki / "AGENTS.md").read_text(), "the Owner's own manual\n")
            self.assertEqual((wiki / "wiki/log.md").read_text(), "the Owner's log\n")


if __name__ == "__main__":
    unittest.main()
