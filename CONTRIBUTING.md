# Contributing to InvenTree

Hi there, thank you for your interest in contributing!
Please read our contribution guidelines, before submitting your first pull request to the InvenTree codebase.

## About InvenTree

InvenTree is an open-source inventory management system designed for makers, engineers, and small manufacturers.

The codebase is split into two independently deployable layers:

**Backend — Django (Python)**
A REST API built with Django and Django REST Framework. It owns all business logic, the database schema, background task processing (Django-Q2), plugin execution, and report generation. The backend can be used standalone via the API without the frontend.

**Frontend — React (TypeScript)**
A single-page application built with React 19, Mantine 9, and Vite. It communicates exclusively through the backend REST API. It has its own build pipeline, test suite (Playwright), and i18n system (Lingui). The frontend lives entirely in `src/frontend/` and has no Django awareness.

When making changes, be clear about which layer you are working in — they have separate toolchains, test runners, and linting rules.

## Project File Structure

The InvenTree project is split into two main components: frontend and backend. This source is located in the `src` directory. All other files are used for project management, documentation, and testing.

```
InvenTree/
├─ .devops/                            # Files for Azure DevOps
├─ .github/                            # Files for GitHub
│  ├─ actions/                         # Reused actions
│  ├─ ISSUE_TEMPLATE/                  # Templates for issues and pull requests
│  ├─ workflows/                       # CI/CD flows
│  ├─ scripts/                         # CI scripts
├─ .vscode/                            # Settings for Visual Code IDE
├─ assets/                             # General project assets
├─ contrib/                            # Files needed for deployments
│  ├─ container/                       # Files related to building container images
│  ├─ installer/                       # Files needed to build single-file installer
│  ├─ packager.io/                     # Files needed for Debian/Ubuntu packages
├─ docs/                               # Directory for documentation / General helper files
│  ├─ ci/                              # CI for documentation
│  ├─ docs/                            # Source for documentation
├─ src/                                # Source for application
│  ├─ backend/                         # Directory for backend parts
│  │  ├─ InvenTree/                    # Source for backend
│  │  ├─ requirements.txt             # Dependencies for backend
│  │  ├─ package.json                  # Dependencies for backend HTML linting
│  ├─ frontend/                        # Directory for frontend parts
│  │  ├─ src/                          # Source for frontend
│  │  │  ├─ main.tsx                   # Entry point for frontend
│  │  ├─ tests/                        # Tests for frontend
│  │  ├─ netlify.toml                  # Settings for frontend previews (Netlify)
│  │  ├─ package.json                  # Dependencies for frontend
│  │  ├─ playwright.config.ts          # Settings for frontend tests
│  │  ├─ tsconfig.json                 # Settings for frontend compilation
├─ .pkgr.yml                           # Build definition for Debian/Ubuntu packages
├─ .pre-commit-config.yaml             # Code formatter/linter configuration
├─ biome.json                          # JS/TS linting and formatting config
├─ CONTRIBUTING.md                     # Contribution guidelines and overview
├─ Procfile                            # Process definition for Debian/Ubuntu packages
├─ pyproject.toml                      # Python tooling config (Ruff, pytest, coverage, djLint, ty)
├─ README.md                           # General project information and overview
├─ SECURITY.md                         # Project security policy
├─ tasks.py                            # Action definitions for development, testing and deployment
```

### Backend app domains

The following Django apps are defined in `src/backend/InvenTree/`:

| Directory | Domain |
|-----------|--------|
| `build/` | Build (manufacturing/assembly) orders |
| `common/` | Shared models, settings, utilities |
| `company/` | Suppliers, customers, manufacturers |
| `data_exporter/` | Data export functionality |
| `importer/` | Data import functionality |
| `InvenTree/` | Core configuration (settings, URLs, middleware) |
| `machine/` | Support for external machines and devices |
| `order/` | Purchase orders and sales orders |
| `part/` | Parts catalogue and categories |
| `stock/` | Stock items and locations |
| `report/` | Report templates and generation |
| `plugin/` | Plugin system |
| `users/` | User accounts and permissions |

### Frontend layout

```
src/frontend/src/
  components/   # Reusable React components
  pages/        # Page-level route components
  tables/       # Data table components
  forms/        # Form components
  hooks/        # Custom React hooks
  states/       # Zustand global state
  locales/      # i18n translation catalogues (Lingui)
```

## Development Setup

The project uses [Invoke](https://www.pyinvoketasks.com/) (`tasks.py`) as the task runner.

```bash
# One-time setup: creates venv at dev/venv/, installs deps, sets up pre-commit hooks
invoke dev.setup-dev

# Apply database migrations
invoke migrate

# Terminal 1 — Django dev server (port 8000)
invoke dev.server

# Terminal 2 — Vite dev server with HMR (port 5173)
invoke dev.frontend-server

# Terminal 3 (optional) — Background task worker
invoke worker
```

A VS Code Dev Container configuration is available at `.devcontainer/` and includes PostgreSQL 15 and Redis 7 sidecar services.

## Running Backend Tests

Always pass `--keepdb` to backend test commands. It reuses the existing test database instead of rebuilding it from scratch on every run, which is significantly faster.

```bash
# All backend tests
invoke dev.test --keepdb

# Specific test module
invoke dev.test --keepdb --runtest=company.test_api

# With coverage
invoke dev.test --keepdb --coverage

# Migration tests only (skip --keepdb here — migrations must run against a fresh DB)
invoke dev.test --migrations
```

## Running Frontend Tests

Frontend tests use [Playwright](https://playwright.dev/) and target Chromium and Firefox. The test runner automatically starts the Vite dev server (port 5173), the Django backend (port 8000), and the background worker — no manual server startup is needed.

```bash
# Open Playwright's interactive UI (recommended for local development)
invoke dev.frontend-test

# Run tests in headless mode from the frontend directory
cd src/frontend && npx playwright test

# Run a specific test file
cd src/frontend && npx playwright test tests/pui_login.spec.ts

# Run tests in a specific browser only
cd src/frontend && npx playwright test --project=chromium
```

Test files live in `src/frontend/tests/` and follow the `pui_*.spec.ts` naming convention.

Locally, tests run with a single worker (required for Vite HMR compatibility). In CI they run with multiple workers against a production build for speed.

## Code Style and Linting

All formatting and linting runs automatically on commit via pre-commit hooks. Never skip them.

### Python (Backend)

Tool: **Ruff** (replaces Black, isort, flake8, and others).

```bash
ruff check src/backend/         # Lint
ruff format src/backend/        # Format
```

- Google-style docstrings enforced
- Enabled rule sets: A, B, C, D, F, I, N, SIM, PIE, PLE, PLW, RUF, UP, W
- Type checking: `ty` (configured in `pyproject.toml`)

### Django Templates

Tool: **djLint**

```bash
djlint src/backend/ --check
```

### JavaScript / TypeScript (Frontend)

Tool: **Biome** (replaces ESLint + Prettier).

```bash
cd src/frontend
yarn biome check .      # Lint + format check
yarn biome format .     # Format only
```

- Single quotes, space indentation
- `noUnusedImports` is an error

## Making Changes

### Backend

- Each Django app has its own `models.py`, `serializers.py`, `views.py`, `urls.py`, and `filters.py`.
- API endpoints use Django REST Framework; document them with drf-spectacular decorators.
- After changing models, create a migration: `invoke dev.makemigrations`.
- Tests live in `test_*.py` files within each app directory.
- Background tasks go through Django-Q2; define them in the app's `tasks.py`.

### Frontend

- Pages register themselves in `src/frontend/src/router.tsx`.
- Server state fetching uses TanStack Query (React Query); avoid raw `useEffect` for data fetching.
- Global UI state uses Zustand stores in `states/`.
- UI components come from Mantine 9.x; use the Mantine component library before writing custom CSS.
- Add i18n strings with Lingui (`t` macro / `Trans` component); run `invoke dev.translate` to extract new strings.
- Playwright tests live in `src/frontend/tests/`.

### Migrations

- Never edit existing migration files; always generate new ones.
- Keep migrations reversible where possible.
- Migration tests run in CI under the tag `migration_test`.

## CI / CD

GitHub Actions workflows live in `.github/workflows/`. Key workflows:

| Workflow | Purpose |
|----------|---------|
| `qc_checks.yaml` | Lint, type-check, backend tests, API schema |
| `frontend.yaml` | Playwright E2E tests, frontend build |
| `docker.yaml` | Docker image builds |
| `translations.yaml` | Crowdin i18n sync |

CI uses path-based filtering — only affected jobs run per PR. Coverage tracked via Codecov; quality analysis via SonarCloud.

## Key Conventions

- **REST API versioning:** Endpoint changes must not break the published API schema. Run `invoke dev.schema` and check the diff before opening a PR.
- **Plugin safety:** The plugin system (`plugin/`) is a public extension point; avoid breaking its interfaces.
- **No hardcoded secrets:** gitleaks runs in pre-commit and CI — any credential-shaped string will block merges.
- **Database portability:** Code must work on PostgreSQL, MySQL/MariaDB, and SQLite. Avoid database-specific SQL or ORM features.
- **Frontend translations:** Every user-visible string must be wrapped in a Lingui `t` macro or `<Trans>` component.
- **Test tagging:** Tag slow or special tests (`@tag('migration_test')`, `@tag('performance_test')`) so CI can filter them selectively.

---

Refer to our [contribution guidelines](https://docs.inventree.org/en/latest/develop/contributing/) for more information!
