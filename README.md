# ☣️ toxic

A friendly front-end for [mutagen](https://mutagen.io) sync sessions. One file, zero dependencies.

## 🚀 Install

```sh
curl -sL https://raw.githubusercontent.com/bobuk/toxic/main/toxic | python3
```

Installs `toxic` into `~/.local/bin`. Needs `mutagen` (`brew install mutagen-io/mutagen/mutagen`)
and, for the interactive bits, `fzf`.

## ✨ Use

```sh
toxic                            # list every session and its state
toxic .                          # show sync status for the current directory
toxic path/to/project            # show sync status for a specific path
toxic add . oranges.team:/tmp    # sync this folder to /tmp/<folder> over there
toxic ignore build/              # stop syncing a path
toxic resolve                    # walk through conflicts, pick a winner
toxic doctor                     # find problems in every session, fix them one by one
toxic rm                         # pick sessions to terminate
toxic pause / resume / flush     # the usual, with -a for all sessions
toxic status                     # conflicts, problems, sizes, ignores
toxic gui                        # live status in a native macOS window
toxic gui .                      # same, filtered to the current directory
```

## 🖥️ GUI

`toxic gui` opens a compact native macOS status window with every Mutagen session, its local and
remote paths, health, conflicts, problems, and successful cycle count. A green lamp means the
session is healthy; a red lamp means it needs attention (hover to see its state). The view refreshes
every second; use `⌘R` to refresh immediately and `⌘Q` or `Esc` to quit. Pass a path to focus on the
session that covers it: `toxic gui path/to/project`.

Like `bl gui`, the AppKit app is embedded in the single `toxic` script, written to a temporary
Swift file on launch, and requires the Xcode Command Line Tools (`xcode-select --install`).

## 📛 Names

`toxic add . oranges.team:/tmp` creates `/tmp/toxic` on the far side and calls the session
`toxic-oranges` — folder name, then host. Override with `-n`, keep the remote path verbatim with `-x`. Write the two endpoints in
either order — the local one is always the local one. Nothing else to remember.

## ⚔️ Conflicts

`toxic resolve` collects every conflict across every session, offers them in `fzf`, then shows
both sides — what changed, how big, how old — and asks:

```
  keep [l]ocal / [r]emote / [s]kip / [q]uit?
```

Mutagen has no resolve verb, so the losing copy is deleted (locally or over `ssh`) and the
session flushed, which lets the surviving side propagate. `--local` / `--remote` resolve
everything one way; `-N` shows what would be removed and removes nothing.

## 🩺 Doctor

`toxic doctor` checks every sync session — conflicts, scan/transfer problems,
excluded paths, halted and offline endpoints — and walks you through the fixes
one by one: pick a side for a conflict, ignore a path or reset the session
(full re-scan) for a problem, recreate a halted session once its root is back.
Healthy sessions are skipped silently. Pass `-N` (or run it from a script,
where there's no terminal) to just list what's wrong and what would be offered.

## 🙈 Ignores

`toxic ignore node_modules` adds a pattern; a real path inside the synced tree becomes anchored
(`build/` → `/build/`). Mutagen can't edit a live session, so `toxic` rebuilds it: the full
`sync create` command is reconstructed from the session's own settings — mode, labels, symlink
and permissions modes, compression, watch config, everything — the session is terminated and
recreated under the same name. No files are touched, but history resets and one full re-scan
follows. Run `toxic ignore` with no arguments to just see the list, `toxic unignore` to drop one.

## ⚙️ Config

Optional, `~/.config/toxic/config.json`:

```json
{
  "ignore": [".venv", "__pycache__", "*.pyc"],
  "ignore_vcs": true,
  "mode": "two-way-safe",
  "hosts": { "orange": "oranges.team" }
}
```

`hosts` are shorthands, so `toxic add . orange:/tmp` goes where you think it goes.

## 🤝 Why

Because `mutagen sync create --name … --ignore … --ignore … --ignore …` is a lot of typing
for "keep this folder over there". 🧑‍💻

---

Two-way sync and no backups: what could possibly go wrong, twice? 😅
