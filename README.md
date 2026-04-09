<div align="center">

# InsiderPSQL Universal Migrator v1

**INSIDERTECH 2026 | Created by Muhammad Rizki Perdana Putra**

*A production-ready, fully animated tool for migrating PostgreSQL databases from version 14-17 to PostgreSQL 18.*

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL 14-18](https://img.shields.io/badge/postgresql-14--18-336791.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Interfaces](https://img.shields.io/badge/interfaces-GUI%20%7C%20CLI%20%7C%20TUI-8A2BE2.svg?style=for-the-badge)
![License MIT](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)

</div>

---

## Features

- **Dual Interfaces** -- Modern desktop GUI (CustomTkinter) and a rich interactive Terminal UI (Rich).
- **Three Migration Methods** -- `dump_restore`, `pg_upgrade`, and pure `python` row-level copy.
- **Auto-Detection** -- Detects source and target PostgreSQL versions via live connection testing.
- **Strict Validation** -- Pre-migration checks block downgrades and incompatible version jumps.
- **Real-time Tracking** -- Animated progress bars, braille spinners, live logs, and step indicators.
- **Compatibility Analysis** -- Scans for breaking changes, deprecated features, and PG18 opportunities.
- **Event-Driven Architecture** -- Internal pub/sub event bus for decoupled migration step tracking.
- **Safe Execution** -- Automatic backups before destructive operations; dry-run mode available.
- **JSON Reports** -- Export compatibility analysis results to JSON with `--report`.
- **Docker & PyInstaller** -- Ship as a container or standalone executable.

---

## Quick Start

### Launch the GUI (Recommended)

```bash
./run_gui.sh
```

### Launch the Interactive Terminal UI

```bash
./run.sh
```

Both scripts automatically create a virtual environment, install dependencies, and launch the application.

---

## Manual Installation

```bash
# Clone the repository
git clone <repo-url> && cd PSQL-DB-Migrator

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install the package in editable mode
pip install -e .
```

---

## Usage

### GUI Mode

```bash
python -m pg_migrator.main gui
```

The GUI provides three pages:

| Page | Description |
|------|-------------|
| **Connections** | Configure and test source/target database connections. Displays detected PG versions. |
| **Options** | Select migration method (`dump_restore`, `pg_upgrade`, `python`) and toggle dry-run mode. |
| **Migration** | Start migration, monitor progress, and review color-coded live logs. |

### Interactive TUI (Wizard)

```bash
python -m pg_migrator.main migrate
```

Walks through a 7-step wizard: connection setup, version detection, compatibility analysis, method selection, confirmation, migration execution, and validation.

### Headless CLI (CI/CD)

```bash
# Non-interactive migration using .env settings
pg-migrator migrate --non-interactive

# Override connection settings
pg-migrator migrate \
  --source-host localhost --source-port 5432 --source-db mydb \
  --target-host localhost --target-port 5433 --target-db mydb \
  --non-interactive

# Dry run (analysis only, no data changes)
pg-migrator migrate --dry-run --non-interactive
```

### Compatibility Check

```bash
# Check source database
pg-migrator check

# Check target database
pg-migrator check --target

# Export report to JSON
pg-migrator check --report report.json
```

---

## Migration Methods

| Method | Command | Description |
|--------|---------|-------------|
| **dump_restore** | `pg_dump` / `pg_restore` | Most reliable. Creates a full dump and restores it on the target. Requires PostgreSQL client tools installed. |
| **pg_upgrade** | `pg_upgrade` | Fast in-place upgrade between major versions. Requires both old and new PG binaries accessible. |
| **python** | Pure Python (psycopg2) | Row-level copy with no external tool dependencies. Migrates schemas, data, constraints, indexes, and sequences. |

---

## Supported Migration Paths

Upgrades and same-version migrations are supported. Downgrades are blocked.

| Source | Target Versions | Status |
|--------|-----------------|--------|
| PostgreSQL 14 | 14.x, 15, 16, 17, 18 | Supported |
| PostgreSQL 15 | 15.x, 16, 17, 18 | Supported |
| PostgreSQL 16 | 16.x, 17, 18 | Supported |
| PostgreSQL 17 | 17.x, 18 | Supported |
| PostgreSQL 18 | 18.x | Supported |

---

## Environment Configuration

Create a `.env` file from the example to pre-fill connection settings:

```bash
cp .env.example .env
```

```env
# Source Database
SOURCE_DB_HOST=localhost
SOURCE_DB_PORT=5432
SOURCE_DB_NAME=mydb
SOURCE_DB_USER=postgres
SOURCE_DB_PASSWORD=your_password

# Target Database
TARGET_DB_HOST=localhost
TARGET_DB_PORT=5433
TARGET_DB_NAME=mydb
TARGET_DB_USER=postgres
TARGET_DB_PASSWORD=your_password
```

Passwords with special characters (`@`, `:`, `#`, etc.) are handled correctly -- the GUI URL-encodes credentials before building the connection URI.

---

## Compatibility Analysis

Before migration, the tool scans your database for:

- **Breaking Changes** -- MD5 authentication deprecation, `VACUUM`/`ANALYZE` behavior changes, public schema permission changes across PG versions.
- **Extension Compatibility** -- Validates installed extensions and their versions against PG18 support.
- **Schema Statistics** -- Counts schemas, tables, rows, UUID columns, and database size.
- **Optimization Opportunities** -- Detects areas where PG18 features (Async I/O, virtual generated columns, UUIDv7) can improve performance.

Use `pg-migrator check --report output.json` to export a full JSON report.

---

## Project Structure

```
PSQL-DB-Migrator/
├── src/pg_migrator/
│   ├── main.py              # CLI entry point (Click commands)
│   ├── gui.py               # Desktop GUI (CustomTkinter, neon dark theme)
│   ├── migrator.py          # Migration engine and orchestration
│   ├── detector.py          # PostgreSQL version detection
│   ├── analyzer.py          # Compatibility analysis
│   ├── db_manager.py        # Database creation, drop, and preparation
│   ├── python_migrator.py   # Pure Python migration (schema + data + constraints)
│   ├── pg_upgrade_wrapper.py# pg_upgrade and dump/restore wrappers
│   ├── stats_collector.py   # Database statistics collection
│   ├── logger.py            # Logging with GUI queue support
│   ├── config.py            # Pydantic settings
│   ├── utils.py             # DSN builder, password masking, formatting
│   ├── events/
│   │   └── bus.py           # Event bus (pub/sub for migration events)
│   └── ui/
│       ├── theme.py         # Neon dark color palette, spinners, box chars
│       ├── components.py    # Rich components (panels, tables, progress bars, animations)
│       └── screens.py       # TUI wizard screens (connection, analysis, migration)
├── tests/
│   ├── conftest.py          # Shared fixtures (mock DB connections)
│   ├── test_utils.py        # Tests for DSN building and password masking
│   └── test_analyzer.py     # Tests for compatibility analyzer
├── pyproject.toml           # Project metadata, Ruff, Mypy, Pytest config
├── requirements.txt         # Pinned dependencies
├── Dockerfile               # Container deployment
├── build_exe.py             # PyInstaller standalone build script
├── run.sh                   # One-click CLI launcher
├── run_gui.sh               # One-click GUI launcher
├── .env.example             # Environment variable template
└── .gitignore               # Comprehensive ignore rules
```

---

## Development

### Install Dev Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v
```

### Lint

```bash
ruff check src/
```

### Type Check

```bash
mypy src/pg_migrator/ --ignore-missing-imports
```

---

## Docker

Build and run the CLI in a container:

```bash
# Build
docker build -t pg-migrator .

# Run help
docker run --rm pg-migrator

# Run migration with environment variables
docker run --rm \
  -e SOURCE_DB_HOST=host.docker.internal \
  -e SOURCE_DB_PORT=5432 \
  -e TARGET_DB_HOST=host.docker.internal \
  -e TARGET_DB_PORT=5433 \
  pg-migrator migrate --non-interactive
```

## Standalone Executable

Build a single-file executable with PyInstaller:

```bash
python build_exe.py
```

The output binary is written to `dist/pg-migrator`.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| GUI | CustomTkinter, Pillow |
| Terminal UI | Rich, pyfiglet |
| CLI | Click |
| Database | psycopg2-binary |
| Config | Pydantic, python-dotenv |
| Testing | Pytest, pytest-cov |
| Linting | Ruff, Mypy |
| Packaging | Hatchling, PyInstaller, Docker |

---

<div align="center">
  <b>INSIDERTECH 2026 | Muhammad Rizki Perdana Putra</b><br>
  <i>Building the future of database tooling.</i>
</div>
