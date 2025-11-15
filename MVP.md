# 📦 SiteLog – MVP Specification

---

## 1. System Description

SiteLog is a construction-site inventory management platform that enables building project teams to track materials entering and leaving the site. The platform ensures accountability, prevents material loss, and provides clear visibility into inventory levels.

The system supports a multi-tenant SaaS structure, meaning multiple construction teams can use the platform independently under one system. Each tenant has its own users, suppliers, warehouses, stock history, and permissions.

SiteLog’s MVP focuses on core operational workflows—materials intake, release, stock visibility, and purchase requests—while providing role-based access and attachment support (photos + signatures). No automation, AI, or advanced analytics are included in the MVP.

---

## 2. MVP Scope

### Included in MVP
- Multi-tenant system
- User roles and permissions
- Admin panel for tenant-level management
- Goods intake workflow (with photos)
- Goods release workflow (with signature + optional photos)
- Purchase request submission and list view
- Inventory and item history reports
- Attachments (photos + signatures)
- Authentication and basic access control
- Existing cross-platform UI layer (Android, macOS, and web) that can be adapted for SiteLog workflows

### Not Included in MVP
- Automation (emails, PDFs, webhooks)
- OCR or AI features
- Supplier returns workflow
- Defective goods reporting workflow
- Apartment equipment tracking
- Advanced reports or dashboards

---

## 3. Roles and Permissions

| Role | Scope | Capabilities |
|------|--------|--------------|
| **Super Admin** | System-wide | Create/manage tenants, assign admin, activate/deactivate tenants, view system metrics |
| **Admin** | Tenant-level | User management, suppliers, warehouses, contractors, item catalog, all reports |
| **Worker** | Tenant-level | Perform goods intake, goods release, submit purchase requests, view reports |
| **Viewer** | Tenant-level | Read-only access to inventory and reports |

---

## 4. Acceptance Criteria

### 4.1 Multi-Tenant System

#### AC-1.1 Tenant Creation
- When a Super Admin creates a tenant and assigns an admin email:
  - A unique `tenant_id` is generated.
  - The assigned user becomes Admin for that tenant.

#### AC-1.2 Data Isolation
- Users must never see or modify data belonging to another tenant.
- Only Super Admin can view tenant metadata (not operational data).

#### AC-1.3 Tenant Activation Status
- Inactive tenant users cannot log in and receive the message:
  > "Account inactive. Contact support."

---

### 4.2 User Management & Permissions

#### AC-2.1 User Creation
- Only tenant Admin can create or modify users within their tenant.

#### AC-2.2 Role Capabilities
- Viewer: read-only access to reports and inventory.
- Worker: operational use only (intake, release, purchase request).
- Admin: all tenant capabilities except platform-wide functions.

#### AC-2.3 Last Admin Rule
- System must prevent removing/demoting the only remaining Admin.

---

### 4.3 Goods Intake

#### AC-3.1 Required Fields
- Item
- Quantity
- Supplier
- Warehouse

#### AC-3.2 Validation
- Quantity must be > 0 numeric.

#### AC-3.3 Records & Attachments
- User may attach photos.
- A stock movement entry of type `IN` is created.
- Warehouse stock increases by the recorded quantity.

---

### 4.4 Goods Release

#### AC-4.1 Required Fields
- Item
- Quantity
- Contractor
- Warehouse

#### AC-4.2 Validation
- Quantity cannot exceed available stock.
- Error shown if validation fails:
  > "Requested quantity exceeds available stock."

#### AC-4.3 Attachments
- Signature collection required.
- Photo optional.

#### AC-4.4 Output
- Stock movement entry recorded as `OUT`.
- Warehouse stock decreases accordingly.

---

### 4.5 Purchase Requests

#### AC-5.1 Required Fields
- Free text description of requested item.

#### AC-5.2 Visibility Rules
- All users in the tenant can see the request list.
- List sorted by newest first.

---

### 4.6 Reporting

#### AC-6.1 Inventory View
- Users (Admin/Worker/Viewer) can see current inventory with:
  - Item name
  - Available quantity
  - Warehouse association

#### AC-6.2 Item Movement History
- Selecting an item shows:
  - Intake and release events
  - Current stock balance

#### AC-6.3 Permission Behavior
- Viewer/Worker: read-only
- Admin: may optionally correct/remove records (optional UX decision)

---

### 4.7 Attachments & Digital Signatures

#### AC-7.1 Storage
- Signatures and photos must be linked to a specific intake or release event.

#### AC-7.2 Viewing
- Users with appropriate access may open attachments from stock history view.

---

## 5. MVP Success Definition

The MVP is considered successful when a construction project team can:

- Track inbound and outbound stock accurately
- Maintain user-restricted access based on roles
- Submit purchase requests
- View real-time inventory and history
- Operate independently as one tenant while others do the same