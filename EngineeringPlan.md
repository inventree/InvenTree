# 🛠️ SiteLog Engineering Plan for Autonomous Agents (InvenTree-based)

## 0. Guiding Principles
- **Foundation**: Fork `inventree/InvenTree` and operate against its Django backend, REST API, stock models, attachment handling, and Android companion app. Treat upstream documentation as authoritative unless overridden here.
- **Database**: Provision PostgreSQL with tenant-scoped schemas and row-level security (RLS). Every data-manipulation instruction must confirm RLS compliance.
- **Agent Parallelization**: Steps explicitly signal when multiple agents can execute in parallel without conflict. Respect dependency notes before starting a task.
- **Definition of Done (DoD)**: 
  - **Dev-only tasks (Phase 1)**: Testable by backend team leader following README instructions and using Postman/curl to verify API responses.
  - **User-facing tasks (Phase 2+)**: Testable by product manager as user stories with clear acceptance criteria that can be validated through UI/API interactions.
  - All DoD must be verifiable without requiring code review or diff inspection.

## MVP Traceability Matrix

| MVP Area | Acceptance Criteria | Plan Coverage |
| --- | --- | --- |
| Multi-tenant system | AC-1.1 – AC-1.3 | Phase 2 (Instructions 2.1–2.5) |
| User management & permissions | AC-2.1 – AC-2.3 | Phase 2 (Instruction 2.3 + 2.6) & Phase 7.3 validation |
| Goods intake workflow | AC-3.1 – AC-3.3 | Phase 3 (Instruction Group 3A) & Phase 6.1 |
| Goods release workflow | AC-4.1 – AC-4.4 | Phase 3 (Instruction Group 3B) & Phase 6.2 |
| Purchase requests | AC-5.1 – AC-5.2 | Phase 3 (Instruction Group 3C) |
| Reporting | AC-6.1 – AC-6.3 | Phase 4 (Instructions 4.1 – 4.3) |
| Attachments & signatures | AC-7.1 – AC-7.2 | Phase 6 (Instructions 6.1 – 6.3) |

Each instruction below cites the linked acceptance criteria to maintain traceability and simplify UAT sign-off.

---

## Phase 1 – Environment & Baseline Hardening (Week 1)
Objective: establish reproducible environments and verify InvenTree still runs after the fork. Linked ACs: foundation for AC-1.1 – AC-7.2 (no direct criteria but prerequisites for every workflow).

- **Instruction 1.1 – Repo fork and environment bootstrap**: Fork upstream, configure Docker Compose (Postgres, Redis, frontend). **Agent allocation**: one backend-capable agent with DevOps privileges. **DoD (Team Lead Testable)**: Backend team leader follows `README.md` setup instructions, runs `docker compose up`, then calls `GET /api/user/` with valid credentials in Postman and receives HTTP 200 with user JSON response. No manual configuration or code changes required beyond what's documented in README.
- **Instruction 1.2 – Baseline CI harness**: Configure GitHub Actions to run lint + tests. **Agent allocation**: DevOps-oriented agent. **DoD (Team Lead Testable)**: Backend team leader creates a test PR, verifies GitHub Actions workflow runs automatically, and confirms the workflow status badge appears in README. Workflow must pass (green) for the test PR.
- **Instruction 1.3 – Secret/config template**: Produce `.env.example`, wire vault/secret manager hooks. **Agent allocation**: DevOps agent. **DoD (Team Lead Testable)**: Backend team leader copies `.env.example` to `.env`, fills in required values per `docs/config.md`, starts the application, and successfully calls `GET /api/user/` with Postman (HTTP 200). Secrets file (`.env`) is confirmed excluded from git via `git status` showing it as untracked.

Parallelization rule: Instructions 1.1–1.3 may execute simultaneously.

---

## Phase 2 – Multi-Tenant & Security Foundation (Weeks 1–2)
Objective: establish tenant entities, enforce isolation, and expose maintainer tooling. Linked ACs: AC-1.1 – AC-1.3, AC-2.1 – AC-2.3.

- **Instruction 2.1 – Tenant model and schema metadata** (Linked ACs: AC-1.1, AC-1.2): extend `Company`/`Site` to map tenants. **Agent allocation**: backend schema agent. **DoD (Team Lead Testable)**: Backend team leader runs database migrations, then queries `SELECT * FROM tenant_tenant;` in PostgreSQL and sees at least one tenant record. Django admin at `/admin/` shows a "Tenants" section with tenant list including columns for name, active status, and created date.
- **Instruction 2.2 – Postgres RLS policies** (Linked ACs: AC-1.2): attach per-tenant RLS rules to every table carrying tenant data. **Agent allocation**: backend DB agent plus DevOps agent for SQL deployment. **DoD (Team Lead Testable)**: Backend team leader creates two test tenants (A and B) with separate users. User from tenant A calls `GET /api/stock/` with their token in Postman and receives only stock items belonging to tenant A. Same user cannot access tenant B's stock (returns empty array or 403). Test script provided in `scripts/test_rls.sh` demonstrates this isolation.
- **Instruction 2.3 – Role matrix & last-admin guard** (Linked ACs: AC-2.2, AC-2.3): encode the MVP RBAC rules (Super Admin, Admin, Worker, Viewer) and enforce the "no demotion/removal of last tenant admin" rule. **Agent allocation**: backend auth agent. **DoD (PM Testable)**: Product manager logs in as tenant Admin, navigates to user management, attempts to demote the only Admin user to Worker role, and receives error message: "Cannot demote the last Admin. At least one Admin must remain." Product manager verifies all four roles (Super Admin, Admin, Worker, Viewer) exist in the system and can be assigned via API or UI.
- **Instruction 2.4 – Tenant activation guard** (Linked ACs: AC-1.3): block inactive tenants at login. **Agent allocation**: backend auth agent. **DoD (PM Testable)**: Product manager logs in as Super Admin, deactivates a test tenant, then attempts to log in as a user from that tenant. Login fails with message: "Account inactive. Contact support." (exact text match required). Product manager verifies this message appears in both web UI login form and API login endpoint response.
- **Instruction 2.5 – Super Admin multi-tenant console** (Linked ACs: AC-1.1, AC-1.3): build a maintainer dashboard to create tenants, assign admins, and flip activation. **Agent allocation**: backend + frontend pair. **DoD (PM Testable)**: Product manager logs in as Super Admin, navigates to "Tenant Management" page, sees a list of all tenants with columns: name, admin email, status (active/inactive), created date. Product manager creates a new tenant, assigns an admin email, and verifies the assigned user receives Admin role. Product manager toggles tenant status from active to inactive and back. Non-super-admin users attempting to access `/admin/tenants/` receive 403 Forbidden.
- **Instruction 2.6 – Tenant user lifecycle management** (Linked ACs: AC-2.1, AC-2.2): ensure only tenant Admins manage users in their tenant, including creation, role assignment, and contractor/worker onboarding flows. **Agent allocation**: backend auth agent with frontend support. **DoD (PM Testable)**: Product manager logs in as tenant Admin, navigates to "Users" page, creates a new user with Worker role, and verifies the user appears in the list. Product manager attempts to create a user while logged in as Worker role and receives 403 Forbidden. Product manager verifies Admin can assign roles (Admin, Worker, Viewer) via dropdown in user creation/edit form. Admin cannot see or modify users from other tenants.

Parallelization rule: Instructions 2.1 and 2.3 can start once shared models are drafted; instruction 2.2 waits on schema readiness; instruction 2.4 requires instruction 2.1; instruction 2.5 depends on prior instructions but UI wiring can begin once API contracts exist; instruction 2.6 begins after 2.3 permissions stabilize and may reuse UI from 2.5.

---

## Phase 3 – Core Workflows (Weeks 2–4)

### Instruction Group 3A – Goods Intake (Linked ACs: AC-3.1 – AC-3.3, AC-7.1)
- **Baseline**: InvenTree already provides stock entry forms, supplier linkage, and attachments.
- **Tasks for agents**:
  - Enforce required fields (item, quantity, supplier, warehouse) and quantity > 0 numeric validation.
  - Align copy/photo requirements with MVP; ensure attachments reference the corresponding intake record.
  - Wire tenant context so intake respects RLS and role permissions from Phase 2.
- **DoD (PM Testable)**: Product manager logs in as Worker role, navigates to "Goods Intake" form, attempts to submit without filling required fields (item, quantity, supplier, warehouse) and sees validation errors for each missing field. Product manager enters quantity as 0 or negative number and sees error: "Quantity must be greater than 0." Product manager completes form with valid data (item, quantity=10, supplier, warehouse) and optional photo attachment, submits, then navigates to inventory view and verifies stock increased by 10. Product manager views movement history for that item and sees the intake event with attached photo visible. Worker role can perform intake; Viewer role cannot access intake form (403 or hidden).

### Instruction Group 3B – Goods Release (Linked ACs: AC-4.1 – AC-4.4, AC-7.1, AC-7.2)
- **Baseline**: Stock issue transactions exist; contractors map to `Customer`/`Contact`.
- **Tasks for agents**:
  - Introduce signature requirement and optional photos.
  - Display canonical validation error copy `"Requested quantity exceeds available stock."`.
  - Ensure contractor field references tenant-scoped contacts and that signature binaries link to the `OUT` movement.
- **DoD (PM Testable)**: Product manager logs in as Worker role, navigates to "Goods Release" form, selects an item with available stock of 5, enters quantity of 6, and sees error message: "Requested quantity exceeds available stock." (exact text). Product manager enters valid quantity (3), selects contractor, attempts to submit without signature, and form prevents submission with message indicating signature is required. Product manager draws signature on canvas widget, optionally attaches photo, submits form, then verifies inventory decreased by 3. Product manager views movement history and sees release event with signature image and optional photo visible. Contractor dropdown only shows contractors belonging to the current tenant.

### Instruction Group 3C – Purchase Requests (Linked ACs: AC-5.1 – AC-5.2)
- **Baseline**: InvenTree lacks lightweight request lists; build custom `PurchaseRequest` entity + UI.
- **Tasks for agents**:
  - Implement model, API, and tenant-scoped list view storing plain-text description plus optional priority metadata.
  - Enforce newest-first sort order and tenant-wide visibility across Admin/Worker/Viewer roles.
  - Include RBAC tests ensuring Super Admin sees metadata but not operational content, in line with AC-1.2.
- **DoD (PM Testable)**: Product manager logs in as Worker role, navigates to "Purchase Requests" page, clicks "Create Request", enters text description "Need 50 bags of cement", submits, and sees the request appear at the top of the list with current timestamp. Product manager creates a second request and verifies it appears above the first (newest first). Product manager logs in as Viewer role, navigates to "Purchase Requests", and sees the same list (read-only). Product manager logs in as Admin role, sees the list, and can also create requests. Product manager logs in as user from different tenant and cannot see requests from first tenant (empty list or 403). Super Admin accessing purchase requests API receives metadata only (tenant name, count) but not request descriptions.

Parallelization rule: Instruction groups 3A and 3B share backend modules but can proceed via separate agents after common services are updated; group 3C may run once authentication and tenant context are stable.

---

## Phase 4 – Reporting & Inventory Views (Weeks 3–4)

- **Instruction 4.1 – Inventory overview per warehouse** (Linked ACs: AC-6.1, AC-6.3): Reuse InvenTree data tables. **Agent allocation**: frontend agent coordinating with backend for filtering. **DoD (PM Testable)**: Product manager logs in as Viewer role, navigates to "Inventory" page, sees a table with columns: Item Name, Available Quantity, Warehouse. Product manager verifies the table shows only items from their tenant's warehouses. Product manager logs in as Worker role, views the same inventory table (read-only, no edit buttons visible). Product manager logs in as Admin role, sees the same table with optional edit capabilities (if implemented per MVP note). Product manager filters by warehouse dropdown and sees only items from selected warehouse.
- **Instruction 4.2 – Item movement history drill-down** (Linked ACs: AC-6.2, AC-6.3): Theme existing history views. **Agent allocation**: frontend agent. **DoD (PM Testable)**: Product manager logs in as any role (Viewer/Worker/Admin), navigates to "Inventory" page, clicks on an item name, and sees a "Movement History" page showing chronological list of intake (IN) and release (OUT) events with columns: Date, Type, Quantity, Warehouse, User. Product manager verifies the "Current Stock" balance displayed at top matches the sum of all IN minus all OUT events. Product manager sees events sorted by date (newest first or oldest first, consistent ordering).
- **Instruction 4.3 – Attachment viewer integration** (Linked ACs: AC-7.2): Embed attachment viewer. **Agent allocation**: frontend agent. **DoD (PM Testable)**: Product manager navigates to item movement history, sees an intake event with photo attachment icon, clicks the icon, and a modal or new tab opens displaying the photo. Product manager sees a release event with signature icon, clicks it, and signature image displays. Product manager logs in as Viewer role, views attachments (read-only, no delete button). Product manager logs in as Admin role, views attachments, and sees delete button (if implemented). Product manager from tenant A cannot access attachment URLs from tenant B (403 Forbidden).

Parallelization rule: start once workflow APIs from Phase 3 are stable; instructions may run concurrently.

---

## Phase 5 – Cross-Platform UI Layer (Weeks 3–6)
Goal: leverage existing web and Android surfaces, ensure parity on macOS browsers, and deliver offline/PWA capabilities. Linked ACs: AC-3.*, AC-4.*, AC-5.*, AC-6.*, AC-7.2 (platform parity requirement).

- **Instruction 5.1 – Branding and navigation uplift (web)**: Apply SiteLog theme and restructure navigation. **Agent allocation**: frontend agent. **DoD (PM Testable)**: Product manager opens web application, sees SiteLog logo and brand colors (not InvenTree branding) in header/navigation. Product manager navigates via menu/links to: Goods Intake, Goods Release, Purchase Requests, Inventory, and verifies all MVP flows are accessible. Product manager runs Lighthouse audit (Chrome DevTools), and scores meet: Performance ≥70, Accessibility ≥90, Best Practices ≥90, SEO ≥80. Scores documented in `docs/lighthouse-report.md`.
- **Instruction 5.2 – Android app fork**: Clone `inventree/inventree-app` (Flutter) and align forms with SiteLog rules. **Agent allocation**: mobile agent. **DoD (PM Testable)**: Product manager installs Android APK on test device, opens app, sees SiteLog branding (logo, colors). Product manager performs goods intake with same validation rules as web (required fields, quantity > 0), then performs goods release with signature requirement. Product manager enables airplane mode, attempts to sync data, and app displays offline message. Product manager disables airplane mode, app syncs successfully. Test script in `scripts/test_android_parity.sh` verifies form validation matches web API responses.
- **Instruction 5.3 – macOS/desktop support**: Validate responsive behavior on Safari/macOS. **Agent allocation**: frontend agent. **DoD (PM Testable)**: Product manager opens web application in Safari on macOS, verifies all pages (Intake, Release, Purchase Requests, Inventory) render correctly without horizontal scrolling at 1920x1080 and 1366x768 viewport widths. Product manager tests keyboard shortcuts documented in `docs/shortcuts.md` (e.g., Cmd+K for search, if implemented) and verifies they work. Product manager completes a full workflow (intake → view inventory → release) using only keyboard navigation.
- **Instruction 5.4 – PWA packaging**: Add service worker, manifest, offline shell. **Agent allocation**: frontend agent. **DoD (PM Testable)**: Product manager opens web application in Chrome on desktop, sees "Install SiteLog" prompt in address bar (or receives install prompt after interaction). Product manager installs PWA, verifies it appears as standalone app icon. Product manager enables offline mode (Chrome DevTools → Network → Offline), refreshes page, and sees inventory list placeholder (not blank page or error). Product manager runs Lighthouse PWA audit and scores: Installable=Yes, PWA Optimized ≥80. On Android Chrome, product manager sees "Add to Home Screen" prompt and installs successfully.

Parallelization rule: instructions 5.2 and 5.4 can run independently once backend APIs are stable; instructions 5.1 and 5.3 can run concurrently after design assets exist.

---

## Phase 6 – Attachments & Digital Signatures Hardening (Weeks 4–5)

- **Instruction 6.1 – Attachment storage policy** (Linked ACs: AC-7.1): Configure S3/MinIO backend with tenant prefixes. **DoD (Team Lead Testable)**: Backend team leader configures S3/MinIO per `docs/config.md`, creates a goods release with signature attachment, then queries storage backend and verifies object path includes tenant ID (e.g., `tenant-123/movements/456/signature.png`). Team leader queries attachment metadata via API `GET /api/attachments/{id}/` and receives only attachments from current user's tenant. Team leader attempts to access attachment from different tenant via direct URL and receives 403 Forbidden. Storage path format documented in `docs/storage-paths.md`.
- **Instruction 6.2 – Signature capture UX (web + Android)** (Linked ACs: AC-4.3, AC-7.1, AC-7.2): Implement signature input and validation. **DoD (PM Testable)**: Product manager logs in as Worker, navigates to Goods Release form, draws signature on canvas widget (web) or touch screen (Android), and signature appears as image preview. Product manager attempts to submit release form without signature and form prevents submission with message: "Signature is required for goods release." Product manager uploads signature file larger than 2MB and sees error: "Signature file must be less than 2MB." Product manager completes signature (valid size/format), submits form, and signature image is visible in movement history. Same validation applies on both web and Android platforms.
- **Instruction 6.3 – Attachment viewer permissions** (Linked ACs: AC-7.2): Restrict viewing/deleting. **DoD (PM Testable)**: Product manager logs in as Viewer role, navigates to movement history, views attachment (photo/signature), and sees no delete button or delete option in UI. Product manager logs in as Worker role, views attachment, and also sees no delete button. Product manager logs in as Admin role, views attachment, sees delete button, clicks delete, confirms deletion, and attachment is removed. Product manager verifies deletion is logged in audit trail (visible in admin panel or API response includes audit entry). Product manager from tenant A cannot delete attachments from tenant B (403 Forbidden).

---

## Phase 7 – QA, Observability, and Release Prep (Weeks 5–6)

- **Instruction 7.1 – End-to-end automation** (Linked ACs: regression coverage for AC-3.* – AC-6.*): Implement Playwright (web) and Detox (mobile) suites. **DoD (Team Lead Testable)**: Backend team leader runs `npm run test:e2e` (or equivalent command documented in README), and test suite executes the following scenarios: (1) Goods intake with photo attachment, (2) Goods release with signature, (3) Purchase request creation and listing, (4) Inventory view and movement history drill-down, (5) Attachment viewing, (6) Cross-tenant isolation (user from tenant A cannot access tenant B data). All tests pass. Team leader verifies e2e tests run automatically in CI pipeline on every PR. Test execution videos/screenshots stored in `tests/e2e/artifacts/`.
- **Instruction 7.2 – Monitoring and logging** (Linked ACs: supports AC-1.2 by auditing isolation): Integrate OpenTelemetry + Sentry. **DoD (Team Lead Testable)**: Backend team leader triggers an error (e.g., invalid API call), then opens Sentry dashboard and sees error logged with tenant ID anonymized (e.g., `tenant-***` not `tenant-123`). Team leader views OpenTelemetry traces and verifies tenant identifiers are sanitized. Team leader accesses monitoring dashboard (Grafana/Prometheus or equivalent) and sees error rate, request latency, and tenant isolation metrics. Alerting rules documented in `docs/alerts.md` with thresholds (e.g., error rate > 5% triggers alert). Dashboard URL and access instructions in `docs/monitoring.md`.
- **Instruction 7.3 – UAT sign-off** (Linked ACs: AC-1.1 – AC-7.2): Compile acceptance checklist. **DoD (PM Testable)**: Product manager opens `docs/uat/acceptance-checklist.md` and sees a table with columns: Acceptance Criteria ID (AC-1.1, AC-1.2, etc.), Description, Test Steps, Status (Pass/Fail), Notes. Product manager executes each test step manually, marks status, and documents any issues. Product manager verifies all ACs from MVP.md are covered. Completed checklist with stakeholder sign-off (PDF or digital signature) stored in `docs/uat/sign-off/`. Checklist format allows non-technical stakeholders to validate functionality.

---

## Feature Coverage Summary
- **Given by InvenTree**: stock models, suppliers, warehouses, attachments, reporting base, web UI, Android app scaffold, RBAC foundation.
- **Needs tweaking**: multi-tenant scoping, role matrix, validation messages, intake/release UX, purchase request UX, reporting layout, branding.
- **Net-new**: Postgres RLS policies, tenant activation logic, signature capture, PWA packaging, purchase request entity, attachment governance, instrumentation.

## MVP Success Validation
- **Operational parity**: Demonstrate a full tenant lifecycle from creation (AC-1.1) through user provisioning (AC-2.1) into intake/release/purchase workflows (AC-3.* – AC-5.*).
- **Visibility**: Provide screenshots or video walkthroughs of inventory and history reports (AC-6.*).
- **Security & isolation**: Supply automated test logs for RLS enforcement plus monitoring traces showing anonymized tenant identifiers (AC-1.2, AC-7.*).
- **Sign-off package**: Phase 7.3 checklist references every AC, attaches the required artifacts, and is stored under `docs/uat/`.

---

## Parallel Workstreams Overview
- **Workstream A – Environment & CI**: no dependencies; launch in week 1.
- **Workstream B – Tenant & RLS**: depends on environment bootstrap; start in week 1 after Instruction 1.1.
- **Workstream C – Intake/Release workflows**: requires tenant models from Instruction 2.1; start week 2.
- **Workstream D – Purchase Requests**: requires tenant context and auth; start week 2.
- **Workstream E – Reporting UX**: depends on workflow APIs from Phase 3; start week 3.
- **Workstream F – Mobile/Web UI polish**: same dependency as E; start week 3.
- **Workstream G – Attachments & signatures**: depends on release workflow foundation; start week 4.
- **Workstream H – QA & Observability**: depends on all prior phases; start week 5.

This structure enables up to six autonomous implementation agents plus supporting DevOps/QA agents to proceed with minimal blocking.

## Cost-Effectiveness Notes

- **Instruction 5.2 (Android app fork)**: Requires Flutter development environment and physical/test Android device. If Android development resources are limited, consider deferring to Phase 8 or validating via Android emulator initially. The DoD can be adjusted to use emulator if physical device testing is not feasible.
- **Instruction 7.1 (E2E automation)**: Setting up Playwright/Detox suites requires significant initial investment. If time-constrained, consider starting with critical path scenarios (intake, release, tenant isolation) and expanding coverage incrementally. The DoD can be met with a subset of scenarios if full coverage is not cost-effective for MVP.
- **Instruction 7.2 (Monitoring)**: Requires Sentry account and OpenTelemetry infrastructure setup. If external services are not available, consider using local logging with structured format (JSON) that can be ingested later. The DoD can be adjusted to validate log format and structure rather than full dashboard integration.

