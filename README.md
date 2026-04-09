<div align="center">
  
# 🚀 InsiderPSQL Universal Migrator v1

**INSIDERTECH 2026 | Created by Muhammad Rizki Perdana Putra**

*A beautiful, seamless, and fully animated tool for migrating your PostgreSQL databases with absolute confidence.*

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL 14-18](https://img.shields.io/badge/postgresql-14--18-336791.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Interfaces](https://img.shields.io/badge/interfaces-GUI%20%7C%20CLI%20%7C%20TUI-8A2BE2.svg?style=for-the-badge)
![License MIT](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)

</div>

---

## ✨ Core Features

- 🖥️ **Dual Interfaces** - Choose between our newly engineered **Fully Animated GUI** or the stunning interactive Terminal UI.
- 🔍 **Universal Auto-Detection** - Smartly detects source PostgreSQL versions via active connection testing.
- ⚠️ **Strict Validation** - Pre-migration checks actively prevent dangerous downgrades or incompatible jumps.
- 📊 **Real-time Tracking** - Smooth progress bars, pulsing indicators, and real-time live logs.
- 🔄 **Safe & Secure** - Automatic backups generated before any destructive operations occur.
- ⚡ **Optimized for PG18** - Built from the ground up to prepare databases for the latest PostgreSQL standards.

---

## 🎨 The Universal GUI Experience

InsiderPSQL Universal Migrator v1 ships with a custom-engineered, modern desktop interface. 

It features:
* **Dynamic Animations:** Smooth sliding tab indicators, page-slide transitions, loading spinners, and pulsing action buttons.
* **Live Connection Testing:** Safely tests database DSNs in background threads and fetches exact PostgreSQL versions before you migrate.
* **Modern Aesthetic:** Dark-mode enabled with our signature Cyan and Indigo branding.

*(Add a screenshot of your beautiful GUI here!)*

---

## ⚡ Quick Start (One-Click Launchers)

We've made starting the application as simple as running a single script. Our launchers automatically build the virtual environment, install dependencies, and launch the application.

### 🌟 Launch the Animated GUI (Recommended)
```bash
./run_gui.sh
```
*Note for macOS users: You can double-click `run_gui.sh` directly from Finder!*

### 💻 Launch the Interactive Terminal UI
```bash
./run.sh
```

---

## 📖 Advanced Usage Guide

If you prefer to integrate InsiderPSQL into existing Python environments or scripts, you can run the module directly. First, ensure dependencies are installed via `pip install -r requirements.txt`.

### 1. GUI Mode
```bash
python -m src.pg_migrator.main gui
```

### 2. TUI Mode (Interactive Wizard)
```bash
python -m src.pg_migrator.main
```

### 3. Headless CLI (For Automation & CI/CD)
```bash
python -m src.pg_migrator.main migrate \
  --source-host localhost \
  --source-port 5432 \
  --source-db mydb \
  --target-host localhost \
  --target-port 5433 \
  --target-db mydb \
  --non-interactive
```

---

## 🎯 Supported Migration Paths

The Universal Migrator supports safe upgrades between PostgreSQL 14-18. 

**Strict Validation:** The tool will actively block attempts to downgrade (e.g., migrating from PG 16 to PG 14).

| Source Version | Target Versions | Status |
|---------------|-----------------|--------|
| PostgreSQL 14 | 14.x, 15, 16, 17, 18 | ✅ Supported |
| PostgreSQL 15 | 15.x, 16, 17, 18 | ✅ Supported |
| PostgreSQL 16 | 16.x, 17, 18 | ✅ Supported |
| PostgreSQL 17 | 17.x, 18 | ✅ Supported |
| PostgreSQL 18 | 18.x | ✅ Supported |

---

## 🔧 Environment Configuration

For headless setups or to pre-fill the GUI/TUI, create a `.env` file based on `.env.example`:

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

---

## 📋 What Gets Analyzed?

Before migrating, InsiderPSQL analyzes your schemas for safety:
- **Breaking Changes:** MD5 authentication deprecation, VACUUM/ANALYZE behavior, public schema permissions.
- **Compatibility:** Validates custom types, stored procedures, and extension compatibility.
- **Opportunities:** Detects areas for optimization in the target PG18 environment (Async I/O, Virtual generated columns).

---

<div align="center">
  <b>INSIDERTECH 2026 | Muhammad Rizki Perdana Putra</b><br>
  <i>Building the future of database tooling.</i>
</div>