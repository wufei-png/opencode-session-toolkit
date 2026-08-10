# opencode-session-toolkit

`opencode-session-toolkit` is a read-only Agent Skill for discovering, searching, inspecting, diagnosing, and exporting local OpenCode SQLite sessions.

It ships English and Chinese runtime packages backed by one tested Python CLI.

## Install the latest `main` snapshot

Use [skills.sh](https://skills.sh) to choose the target coding agent and project/global scope. These commands intentionally track the mutable `main` branch:

```bash
# English
npx skills@latest add \
  https://github.com/wufei-png/opencode-session-toolkit/tree/main/opencode-session-toolkit

# 中文
npx skills@latest add \
  https://github.com/wufei-png/opencode-session-toolkit/tree/main/opencode-session-toolkit-cn
```

`skills@latest` selects the current installer CLI; `/tree/main/...` selects this repository's latest development snapshot.

For non-interactive installation, add the standard skills.sh flags, for example `-g -a codex -y`. This repository does not maintain a second target-selection system.

## Install a stable release

Stable releases provide self-contained English and Chinese archives plus `SHA256SUMS`. Replace `X.Y.Z` with a published version:

```bash
npx skills@latest add \
  https://github.com/wufei-png/opencode-session-toolkit/releases/download/vX.Y.Z/opencode-session-toolkit-en-vX.Y.Z.tar.gz

npx skills@latest add \
  https://github.com/wufei-png/opencode-session-toolkit/releases/download/vX.Y.Z/opencode-session-toolkit-cn-vX.Y.Z.tar.gz
```

For checksum verification before installation, download the chosen archive and `SHA256SUMS`, run `shasum -a 256 -c SHA256SUMS`, extract the verified archive, then pass the extracted `opencode-session-toolkit/` directory to `npx skills@latest add`. The CLI accepts archive URLs directly but treats local sources as directories.

The release workflow also publishes [English](https://clawhub.ai/wufei-png/skills/opencode-session-toolkit) and [Chinese](https://clawhub.ai/wufei-png/skills/opencode-session-toolkit-cn) ClawHub packages from the tagged commit.

## What the skill does

- Resolves the live database with `opencode db path` or an explicit `--db-path`.
- Opens SQLite with URI `mode=ro` and `PRAGMA query_only`.
- Provides `doctor`, `list`, `show`, `search`, `export`, and `schema` commands.
- Detects live schema capabilities instead of trusting a stale migration snapshot.
- Treats text filters literally, including `%` and `_`.
- Omits reasoning and complete payloads unless `--include-sensitive` is explicit.
- Previews export paths and conflicts without writes through `export --dry-run`.
- Preflights exports and refuses changed output unless `--overwrite` is explicit.

## Quick development check

```bash
python3 scripts/sync_distributions.py
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py --version "$(cat VERSION)" --output-dir ./dist
```

The runtime packages use only the Python standard library. Python 3.11 or newer is supported.

## Repository layout

```text
src/opencode_sessions.py                 canonical CLI source
VERSION                                  canonical runtime/release version
opencode-session-toolkit/                English self-contained skill
opencode-session-toolkit-cn/             Chinese self-contained skill
scripts/sync_distributions.py            regenerate runtime CLI copies
scripts/validate_repo.py                 structure and parity checks
scripts/build_release.py                 deterministic release archives
tests/                                   synthetic SQLite and repository tests
```

Do not edit the generated runtime CLI copies directly; edit `src/opencode_sessions.py` and run the sync command.
