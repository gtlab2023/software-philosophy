# Host adapters

The shared core is built into two host-specific directories by `scripts/build_release.py`:

- `dist/codex/`: contains `.codex-plugin/plugin.json`;
- `dist/claude/`: contains `.claude-plugin/plugin.json`.

The source tree intentionally keeps host metadata separate from shared Skills, Packs and validators.
