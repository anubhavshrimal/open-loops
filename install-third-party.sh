#!/usr/bin/env bash
# Install the third-party skills that Open Loops uses, from their upstream source.
#
# Reads third-party.json. Never copies a third-party file into this repo. Safe to re-run: a
# plugin or skill that is already installed is skipped, so a second run changes nothing. A
# failed install prints one warning line and the script goes on; it always exits 0 when it
# installs.
#
# One route per agent:
#   - Claude Code (`claude` on PATH): the source's Claude Code plugin marketplace. A plugin is
#     installed whole (it can hold more skills than the list). A source with no plugin goes
#     through `npx skills add` for Claude Code instead.
#   - Codex and other agents: `npx skills add` with an explicit skill list. The skills go to the
#     shared copy in ~/.agents/skills, which Codex reads.
#
# Optional sources (`"optional": true`) are credited only; the installer skips them.
#
# Usage:
#   ./install-third-party.sh                 install the required sources
#   ./install-third-party.sh --notice        print NOTICE, made from third-party.json
#   ./install-third-party.sh --credits       print the credits table, made from third-party.json
#   ./install-third-party.sh --check         check NOTICE and every credits table against third-party.json
#
# Environment:
#   OPENLOOPS_SKIP_THIRD_PARTY=1   skip every third-party install (offline or locked-down machines)
#   OPENLOOPS_NPX_AGENTS="..."     agent ids for the `npx skills add` route, for example
#                                  "codex cursor" (default: "codex" if `codex` is on PATH, else none)
set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="$REPO/third-party.json"
# The skills CLI sends anonymous usage data unless this is set.
export DISABLE_TELEMETRY=1 NPM_CONFIG_AUDIT=false NPM_CONFIG_FUND=false

ok() { echo "ok    $*"; }
warn() { echo "warn: $*"; }

# Reads third-party.json and the repo files. Subcommands: sources, plugin, missing, notice, credits, check.
read -r -d '' TP_PY <<'PY'
import json, os, re, sys

repo, cmd, args = sys.argv[1], sys.argv[2], sys.argv[3:]
sources = json.load(open(os.path.join(repo, "third-party.json")))["sources"]
START, END = "<!-- credits:start -->", "<!-- credits:end -->"


def notice():
    license_text = open(os.path.join(repo, "LICENSE")).read()
    owner = re.search(r"^Copyright .*$", license_text, re.M).group(0)
    out = ["Open Loops", owner, "Licensed under the MIT License (see LICENSE).", "",
           "This repository contains no third-party skill or program files. Setup installs the",
           "third-party software below from its upstream source, on the Owner's machine, under",
           "its own license. Each is a separate project.", ""]
    for s in sources:
        out.append(f"{s['name']} ({s['repo']})")
        if s["copyright"]:
            out.append(s["copyright"])
        out.append(f"License: {s['license']}")
        out.append(f"Use: {s['used_for']}")
        out.append("")
    return "\n".join(out)


def credits():
    out = ["| Source | Author | License | How Open Loops uses it |", "|---|---|---|---|"]
    for s in sources:
        how = s["used_for"]
        how += " Installed by setup from upstream." if s["skills"] else " Not installed by setup."
        out.append(f"| [{s['name']}]({s['repo']}) | {s['author']} | {s['license']} | {how} |")
    return "\n".join(out)


if cmd == "sources":
    # One tab-separated line per required source: name, marketplace, plugin, npx source, skills.
    for s in sources:
        if s["skills"] and not s["optional"]:
            claude, npx = s["install"].get("claude", {}), s["install"].get("npx", {})
            print("\t".join([s["name"], claude.get("marketplace", "-"), claude.get("plugin", "-"),
                             npx.get("source", "-"), " ".join(s["skills"])]))
elif cmd == "plugin":
    # args: plugin id; stdin: `claude plugin list --json`. Prints the id of the same plugin, from any
    # marketplace, installed in the user scope, so that it is never installed twice.
    name = args[0].split("@")[0]
    try:
        plugins = json.load(sys.stdin)
    except ValueError:
        plugins = []
    print(next((p["id"] for p in plugins if p["id"].split("@")[0] == name and p.get("scope", "user") == "user"), ""))
elif cmd == "missing":
    # args: npx source, skills... ; stdin: `npx skills ls -g --json`. Prints the skills not there yet.
    source, skills = args[0], args[1:]
    try:
        have = {(s["name"], s.get("source")) for s in json.load(sys.stdin)}
    except ValueError:
        have = set()
    print(" ".join(k for k in skills if (k, source) not in have))
elif cmd == "notice":
    print(notice(), end="")
elif cmd == "credits":
    print(credits())
elif cmd == "check":
    problems = []
    path = os.path.join(repo, "NOTICE")
    if not os.path.exists(path) or open(path).read() != notice():
        problems.append("NOTICE does not match third-party.json (rewrite it: ./install-third-party.sh --notice > NOTICE)")
    tables = 0
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            if not name.endswith(".md"):
                continue
            path = os.path.join(root, name)
            text = open(path).read()
            if START not in text:
                continue
            tables += 1
            block = text.split(START, 1)[1].split(END, 1)[0].strip()
            if block != credits():
                problems.append(f"{os.path.relpath(path, repo)}: the credits table does not match third-party.json "
                                "(replace it with ./install-third-party.sh --credits)")
    if not tables:
        problems.append(f"no credits table ({START} ... {END}) in any .md file")
    for p in problems:
        print(f"check: {p}")
    if problems:
        sys.exit(1)
    print(f"check: NOTICE and {tables} credits table(s) match third-party.json")
PY
tp() { python3 -c "$TP_PY" "$REPO" "$@"; }

while [ $# -gt 0 ]; do
    case "$1" in
        --notice) tp notice; exit $? ;;
        --credits) tp credits; exit $? ;;
        --check) tp check; exit $? ;;
        -h|--help) sed -n '2,/^set -u/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
    esac
done

if [ "${OPENLOOPS_SKIP_THIRD_PARTY:-0}" = 1 ]; then
    echo "skip  third-party skills (OPENLOOPS_SKIP_THIRD_PARTY=1)"
    exit 0
fi
command -v python3 >/dev/null 2>&1 || { warn "python3 not found; skipping third-party skills"; exit 0; }
list="$(tp sources)" || exit 2

# A space-separated list, not an array: an empty array is "unbound" under set -u in old bash.
npx_agents=""
if [ -n "${OPENLOOPS_NPX_AGENTS+set}" ]; then
    npx_agents="$(echo $OPENLOOPS_NPX_AGENTS)"
elif command -v codex >/dev/null 2>&1; then
    npx_agents="codex"
fi
has_claude=0
command -v claude >/dev/null 2>&1 && has_claude=1
if [ "$has_claude" = 0 ] && [ -z "$npx_agents" ]; then
    warn "no agent found (claude, codex, or OPENLOOPS_NPX_AGENTS); skipping third-party skills"
    exit 0
fi

claude_plugins=""
[ "$has_claude" = 1 ] && claude_plugins="$(claude plugin list --json 2>/dev/null)"
npx_installed=""
npx_listed=0

# npx_add <source> <agents> <skills>: install the skills that are not in the shared copy yet.
npx_add() {
    local source="$1" agents="$2" skills="$3" missing args=()
    command -v npx >/dev/null 2>&1 || { warn "npx not found; skipping $source for $agents"; return; }
    if [ "$npx_listed" = 0 ]; then
        npx_installed="$(npx --yes skills ls -g --json 2>/dev/null)"
        npx_listed=1
    fi
    # shellcheck disable=SC2086  # skills is a space-separated list
    missing="$(printf '%s' "$npx_installed" | tp missing "$source" $skills)"
    if [ -z "$missing" ]; then
        ok "$source for $agents (already installed: $skills)"
        return
    fi
    for s in $missing; do args+=(--skill "$s"); done
    # shellcheck disable=SC2086  # agents is a space-separated list
    if npx --yes skills add "$source" "${args[@]}" -g -y --agent $agents >/dev/null 2>&1; then
        ok "$source for $agents ($missing)"
        npx_installed="$(npx --yes skills ls -g --json 2>/dev/null)"
    else
        warn "$source install failed for $agents; continuing"
    fi
}

# The loop reads fd 3, so that claude and npx cannot eat the list from stdin.
while IFS=$'\t' read -r -u 3 name marketplace plugin npx_source skills; do
    [ -n "$name" ] || continue
    npx_for="$npx_agents"
    if [ "$has_claude" = 1 ]; then
        if [ "$plugin" != "-" ]; then
            have="$(printf '%s' "$claude_plugins" | tp plugin "$plugin")"
            if [ -n "$have" ]; then
                ok "$name for Claude Code (plugin $have already installed)"
            elif { claude plugin marketplace add "$marketplace" && claude plugin install "$plugin"; } >/dev/null 2>&1; then
                ok "$name for Claude Code (plugin $plugin)"
            else
                warn "$name plugin $plugin install failed for Claude Code; continuing"
            fi
        else
            npx_for="claude-code${npx_for:+ $npx_for}"
        fi
    fi
    if [ -n "$npx_for" ]; then
        if [ "$npx_source" = "-" ]; then
            warn "$name has no npx route; skipping it for $npx_for"
        else
            npx_add "$npx_source" "$npx_for" "$skills"
        fi
    fi
done 3<<< "$list"
exit 0
