# Installation

Repository: `https://github.com/gtlab2023/software-philosophy`

The repository root is a marketplace for both Codex and Claude Code. Both hosts install the same generated payload under `plugins/software-philosophy/`; only their manifest files differ.

## Codex

```bash
codex plugin marketplace add gtlab2023/software-philosophy
codex plugin add software-philosophy@software-philosophy
```

Start a new Codex task after installation.

Or use the helper:

```bash
git clone https://github.com/gtlab2023/software-philosophy.git
cd software-philosophy
./scripts/install-codex.sh
```

For local development without GitHub:

```bash
./scripts/install-codex.sh /absolute/path/to/software-philosophy
```

Update:

```bash
codex plugin marketplace upgrade software-philosophy
codex plugin add software-philosophy@software-philosophy
```

Remove:

```bash
codex plugin remove software-philosophy@software-philosophy
codex plugin marketplace remove software-philosophy
```

## Claude Code

```bash
claude plugin marketplace add gtlab2023/software-philosophy
claude plugin install software-philosophy@software-philosophy --scope user
```

Restart Claude Code after installation.

Or use the helper:

```bash
git clone https://github.com/gtlab2023/software-philosophy.git
cd software-philosophy
./scripts/install-claude.sh
```

For local development:

```bash
./scripts/install-claude.sh /absolute/path/to/software-philosophy
```

Update:

```bash
claude plugin marketplace update software-philosophy
claude plugin update software-philosophy@software-philosophy --scope user
```

Remove:

```bash
claude plugin uninstall software-philosophy@software-philosophy
claude plugin marketplace remove software-philosophy --scope user
```

## Validate before publishing

```bash
python3 scripts/test_plugin.py
python3 scripts/build_release.py --clean
python3 scripts/validate_distribution.py
claude plugin validate . --strict
claude plugin validate plugins/software-philosophy --strict
```

Each release must bump both source manifests to the same semantic version and commit the regenerated `plugins/software-philosophy/` directory and marketplace manifests.
