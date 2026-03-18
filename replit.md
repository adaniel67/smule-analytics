# Workspace

## Overview

pnpm workspace monorepo using TypeScript (for the scaffolded API server and mockup sandbox),
plus a standalone **Python learning project** for Smule analytics in `smule_analytics/`.

---

## Python — Smule Analytics Tool

**GitHub repo:** https://github.com/adaniel67/smule-analytics  
**Target account:** `cacophonoussound` (configured in `main.py`)

### Run it
```bash
python main.py
```

### File structure

| File | Purpose |
|------|---------|
| `main.py` | Entry point — orchestrates all steps |
| `smule_analytics/api.py` | HTTP calls to Smule (requests + pagination + dedup) |
| `smule_analytics/analytics.py` | Stats computation (Counter, sort, classify by type) |
| `smule_analytics/display.py` | Terminal output via the `rich` library |
| `requirements.txt` | Python dependencies (requests, rich) |

### Python concepts taught in each file

- **api.py**: `def`, `try/except`, `f-strings`, `dict.get()`, `set` for dedup, `while` loop
- **analytics.py**: list comprehensions, `Counter`, `sorted()` + `lambda`, `datetime.fromisoformat()`
- **display.py**: `rich` tables/panels, `:,` number formatting, `enumerate()`
- **main.py**: module imports, `if __name__ == "__main__"`, separation of concerns

### Known API limitation

Smule's public endpoint (`/s/profile/performance/{username}`) currently returns only ~25
recent/featured performances per user. The tool detects and deduplicates these automatically
and stops fetching when no new data appears. This is a Smule-side restriction, not a bug.

---

## TypeScript (scaffolded — not yet developed)

### Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)

### Structure

```text
artifacts-monorepo/
├── artifacts/              # Deployable applications
│   └── api-server/         # Express API server
├── lib/                    # Shared libraries
│   ├── api-spec/           # OpenAPI spec + Orval codegen config
│   ├── api-client-react/   # Generated React Query hooks
│   ├── api-zod/            # Generated Zod schemas from OpenAPI
│   └── db/                 # Drizzle ORM schema + DB connection
├── scripts/                # Utility scripts
├── smule_analytics/        # Python analytics package
├── main.py                 # Python entry point
└── requirements.txt        # Python dependencies
```
