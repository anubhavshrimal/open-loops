# Cost saver: the Change check

The Change check ([`core/change-check.py`](../core/change-check.py)) is optional. A script with no LLM runs at a short interval and starts a Cycle only when a signal changed, a read failed, or the Safety Cycle is due. Its rules, with its "Known limit", are in [`SPEC.md`](../SPEC.md) section 4, "When a Cycle starts". Its words are in [`GLOSSARY.md`](../GLOSSARY.md). The parts of `<home>/change-check.md` are next to the example notes files in [`adapters/`](../adapters/README.md), as `<example>.change-check.md`.

The steps to evaluate it for an Owner, and to switch it on, come with the optional setup question that uses them.
