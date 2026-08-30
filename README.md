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
toxic rm                         # pick sessions to terminate
toxic pause / resume / flush     # the usual, with -a for all sessions
toxic status                     # conflicts, problems, sizes, ignores
```

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
