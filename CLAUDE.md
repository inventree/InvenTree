# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

InvenTree is an open-source inventory management system built on:
- **Backend**: Python/Django + Django REST Framework, with async tasks via django-q2
- **Frontend**: React 19 + TypeScript, Mantine UI, TanStack Query, Zustand, React Router, Lingui i18n
- **Deployment**: Docker (Caddy/nginx reverse proxy + gunicorn), also supports bare-metal and Debian packages

Source lives in `src/backend/` (Django) and `src/frontend/` (React). All dev automation is via `invoke` (tasks defined in `tasks.py`).

---

## Key Commands

### Backend

```bash
# Run Django management commands
invoke server                          # Start dev server on 0.0.0.0:8000
invoke worker                          # Start django-q2 background task worker
invoke migrate                         # Run database migrations
invoke static                          # Collect static files

# Testing
invoke test                            # Run all backend tests
invoke test --runtest=order.test_api   # Run a specific test module
invoke test --runtest=order.tests.TestClass.test_method  # Run single test
invoke test --coverage                 # Run with coverage report
invoke test --keepdb                   # Keep test DB between runs

# Linting (backend uses ruff)
ruff check src/backend/InvenTree       # Lint
ruff format src/backend/InvenTree      # Format
ty check --python $(which python3) src/backend  # Type check
```

### Frontend

```bash
cd src/frontend

yarn install                           # Install dependencies
yarn run dev --host                    # Start Vite dev server
yarn run build                         # Production build
yarn run compile                       # Compile Lingui translations
yarn run extract                       # Extract new translation strings

# Or via invoke from repo root:
invoke int.frontend-server             # Dev server (compiles translations first)
invoke int.frontend-compile            # Full build (install + compile + build)
invoke int.frontend-test               # Run Playwright tests (UI mode)

# Linting (frontend uses Biome)
cd src/frontend && npx biome check .   # Lint + format check
cd src/frontend && npx biome lint .    # Lint only
```

### Playwright (E2E) Tests

```bash
cd src/frontend
npx playwright test                    # Run all tests headless
npx playwright test --ui               # Run with UI
npx playwright test tests/foo.spec.ts  # Run a specific test file
```

---

## Architecture

### Backend Django Apps

Each functional domain is a self-contained Django app in `src/backend/InvenTree/`:

| App | Purpose |
|-----|---------|
| `InvenTree/` | Core: settings, base models, tasks, API helpers, auth |
| `part/` | Parts catalogue, BOM, categories, pricing |
| `stock/` | Stock items, locations, tracking, serial/batch numbers |
| `build/` | Manufacturing/build orders |
| `order/` | Purchase orders, sales orders, return orders, transfer orders |
| `company/` | Suppliers, manufacturers, customers, contacts |
| `report/` | Report/label templates (Jinja2 → WeasyPrint PDF) |
| `plugin/` | Plugin registry and all mixin interfaces |
| `machine/` | Machine integrations (label printers, etc.) |
| `importer/` | CSV/spreadsheet data import sessions |
| `common/` | Settings, notifications, attachments, currency, project codes |
| `users/` | User/group management, permissions, OAuth2/SSO |
| `generic/` | Shared state machines, status codes, serializer fields |

Every app follows the same pattern: `models.py` → `serializers.py` → `api.py` (DRF viewsets) → registered in `InvenTree/urls.py`. Tests live alongside: `test_api.py`, `tests.py`, `test_migrations.py`, etc.

**Base models** (`InvenTree/models.py`): `InvenTreeModel` (MPTT-aware), `MetadataMixin`, `DiffMixin`, `InvenTreeAttachmentMixin`. Use these as base classes.

**Status codes** (`generic/states/`): Integer-backed enums with colour rendering. Each app that needs workflow states (BuildStatus, PurchaseOrderStatus, etc.) extends `StatusCode`.

**Events system**: Apps define events as `BaseEventEnum` subclasses in `events.py`. Plugins with the `EventMixin` subscribe to these string-keyed events. Background tasks and state transitions fire events via `trigger_event()`.

**Background tasks**: Scheduled and async work runs through django-q2. `InvenTree/tasks.py` contains core scheduled tasks; each app has its own `tasks.py`. `schedule_task()` is the helper to register recurring work.

**API versioning**: Increment `INVENTREE_API_VERSION` in `InvenTree/api_version.py` and add a changelog entry whenever the REST API changes.

### Plugin System

Plugins live in `src/backend/InvenTree/plugin/`. A plugin is a class inheriting `InvenTreePlugin`, optionally mixing in capability interfaces:

- `ActionMixin`, `BarcodeMixin`, `EventMixin`, `LabelPrintingMixin`, `ReportMixin`, `ScheduleMixin`, `SettingsMixin`, `NavigationMixin`, `APICallMixin`, `SupplierMixin`, `MailMixin`, `LocateMixin`, `CurrencyExchangeMixin`, `IconPackMixin`
- UI plugins (`UIFeatureMixin`) inject React components into the frontend at declared slots (panels, dashboard, etc.)

The registry (`plugin/registry.py`) discovers and loads plugins; `PluginConfig` (model) stores enabled/disabled state per plugin key.

### Frontend Architecture

**Entry point**: `src/frontend/src/main.tsx` → `App.tsx` → `router.tsx`

**Routing**: React Router v6, all routes in `router.tsx`. Pages are lazy-loaded via `Loadable()`.

**State management** (Zustand stores in `src/frontend/src/states/`):
- `UserState` — authenticated user, login/logout
- `ServerApiState` — server info (version, plugins, feature flags)
- `SettingsStates` — global + user settings fetched from API
- `GlobalStatusState` — status code enums fetched from API (used to render labels/colours)
- `LocalState` — host URL, theme, locale (persisted in localStorage)

**API layer**: A global Axios instance (`App.tsx`) is provided via `ApiContext`. Components call `useApi()` to get the instance. All server calls use CSRF cookie auth. TanStack Query manages caching/refetching.

**Forms**: `ApiForm` / `OptionsApiForm` in `components/forms/` is the standard form component. It fetches field metadata from the API `OPTIONS` endpoint and renders fields dynamically. Use `UseForm` hook to open modal forms.

**Tables**: `InvenTreeTable` (wraps mantine-datatable) in `tables/InvenTreeTable.tsx` is the standard data table. Pass a `url` and column definitions; it handles pagination, filtering, search, sorting, and row actions.

**Panels**: Detail pages (Part, Stock, Order, etc.) use `PanelGroup` from `components/panels/`. Panels are tab-based sections; plugins can inject additional panels via the `UIFeatureMixin`.

**i18n**: Lingui (`@lingui/react`). Wrap strings with `t\`...\`` or `<Trans>`. Run `yarn run extract` to find new strings, `yarn run compile` to compile catalogs. Compiled catalogs are in `src/frontend/src/locales/`.

### Deployment (contrib/)

- `contrib/container/`: Docker Compose, Dockerfile, Caddy/nginx configs, `init.sh` startup script
- `contrib/installer/`: Single-file bash installer for bare-metal
- `contrib/packager.io/`: Debian/Ubuntu package definitions

The production container runs: gunicorn (Django), django-q2 worker, and a reverse proxy (Caddy or nginx) serving the pre-built frontend static files. Frontend is built separately and bundled into `src/backend/InvenTree/web/static/web/`.

### Documentation (docs/)

Built with MkDocs + material theme. Source in `docs/docs/`. Run locally with `mkdocs serve` from the `docs/` directory.
