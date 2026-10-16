# AgriTrust — Comprehensive Software Quality Assurance & Security Audit Report
**Audited By:** Senior Principal QA Engineer & Security Auditor (15+ Years Experience)  
**Project:** AgriTrust (Python 3.12 / Flask 3.0 / SQLAlchemy / OpenCV)  
**Date:** October 12, 2026  
**Status:** Audit Complete — Action Required Prior to Production Release  

---

## 1. Executive Summary

As part of a full-scope Quality Assurance and penetration evaluation of the AgriTrust platform, all architectural layers—including **Role-Based Access Control (RBAC)**, **Financial & Transaction Integrity**, **Produce Traceability Ledger**, **Computer Vision Pipelines**, **Agronomic Decision Engines**, and **Data Consistency**—were subjected to static code analysis, negative testing, boundary-value evaluation, and security vulnerability probing.

While the core functionality and test suites demonstrate sound foundational architecture, **18 distinct defects and architectural risks** were identified:
- **1 Critical Security Flaw:** Public self-registration of administrative accounts (Privilege Escalation).
- **5 High-Severity Logic & Security Bugs:** Insecure Direct Object References (IDOR), Open Redirect, and Inventory/Stock Leaks on order cancellations.
- **7 Medium-Severity Runtime & Validation Defects:** Chatbot substring collision bug, unhandled `ValueError` 500 crashes, negative pricing/quantity bypasses, and chronological date inversions.
- **5 Low-Severity & Maintenance Risks:** Deprecated SQLAlchemy `Query.get()` calls, Python 3.12 `datetime.utcnow()` deprecation, and audit trail bypasses.

---

## 2. Defect Severity Matrix

| Defect ID | Severity | Category | Affected File(s) | Impact Summary |
|---|---|---|---|---|
| **SEC-01** | **CRITICAL** | Broken Access Control (CWE-269) | `routes/auth.py`, `templates/register.html` | Public self-registration permits arbitrary creation of `ADMIN` accounts. |
| **SEC-02** | **HIGH** | Open Redirect (CWE-601) | `routes/auth.py` | Protocol-relative URL (`//evil.com`) bypasses login redirection checks. |
| **SEC-03** | **HIGH** | IDOR / Object Ownership (CWE-639) | `routes/crops.py` | Farmers can associate crops with arbitrary farm IDs owned by others. |
| **SEC-04** | **HIGH** | IDOR / Traceability (CWE-639) | `routes/traceability.py`, `routes/marketplace.py` | Batches and produce listings can link to arbitrary crops and farms. |
| **LOG-01** | **HIGH** | Business Logic / Inventory Leak | `routes/orders.py`, `services/marketplace_service.py` | Cancelling an order never restores deducted product inventory. |
| **LOG-02** | **HIGH** | Resource Lockout / State Machine | `routes/reservations.py`, `services/marketplace_service.py` | Reservations cannot be cancelled, locking farmer quotas permanently. |
| **SEC-05** | **MEDIUM** | Admin Self-Lockout (CWE-284) | `routes/admin.py` | Admin can demote themselves without checking for remaining active admins. |
| **RUN-01** | **MEDIUM** | Natural Language Processing Bug | `services/chatbot_service.py` | Substring match on `'hi'` triggers greeting on words like `"whitefly"` or `"this"`. |
| **VAL-01** | **MEDIUM** | Input Validation / 500 Crash | `routes/recommendations.py`, `ai/crop_recommendation.py` | Non-numeric land size throws unhandled `ValueError` 500 server crash. |
| **VAL-02** | **MEDIUM** | Input Validation / 500 Crash | `routes/orders.py`, `routes/reservations.py`, `routes/analytics.py` | Non-numeric IDs or discount values cause unhandled 500 server errors. |
| **VAL-03** | **MEDIUM** | Negative Value Injection | `routes/farms.py`, `routes/general.py`, `routes/dashboard.py` | Negative acreage, pricing, and quantities are permitted on update forms. |
| **VAL-04** | **MEDIUM** | Chronological Inversion | `routes/crops.py`, `routes/reservations.py`, `routes/general.py` | Harvest date earlier than planting date; past dates in future reservations. |
| **RUN-02** | **MEDIUM** | Null Reference Exception | `routes/orders.py`, `routes/analytics.py` | Order status and analytics crash with 500 if associated product is null. |
| **RUN-03** | **MEDIUM** | External API Crash Vulnerability | `routes/weather.py` | Weather route crashes on empty API weather payload or missing dict keys. |
| **LOG-03** | **MEDIUM** | Audit Trail Bypass | `routes/traceability.py` | Updating batch lifecycle stage in traceability route bypasses audit logging. |
| **PER-01** | **LOW** | Performance Bottleneck | `routes/traceability.py` | `import qrcode` imported inside request handler on every QR code fetch. |
| **DEP-01** | **LOW** | SQLAlchemy 2.0 Deprecation | Multiple route files & models | Legacy `Model.query.get()` triggers deprecation warnings in SQLAlchemy 2.0. |
| **DEP-02** | **LOW** | Python 3.12 Deprecation | Multiple models & routes | `datetime.utcnow()` is deprecated in Python 3.12 and scheduled for removal. |

---

## 3. Detailed Defect Analysis & Reproduction Steps

### Defect SEC-01: Critical Administrative Privilege Escalation via Public Registration
- **Location:** `routes/auth.py` (Line 59) and `templates/register.html` (Lines 35–41)
- **Vulnerability:** CWE-269 (Improper Privilege Management), OWASP A01:2021 (Broken Access Control)
- **Description:**  
  The registration template includes a radio button option for `ADMIN / Inspector`. On the backend, `routes/auth.py` evaluates:
  ```python
  if role not in ['FARMER', 'BUYER', 'ADMIN']:
      role = 'FARMER'
  ```
  This explicitly permits any visitor on the public internet to register directly as an Administrator.
- **Steps to Reproduce:**
  1. Open `/register` in an incognito window.
  2. Select the "Admin / Inspector" radio button or send a `POST /register` with `role=ADMIN`.
  3. Submit the registration.
  4. The user is logged in with `session['role'] = 'ADMIN'` and has full access to `/admin`.
- **Expected Behavior:**  
  Public registration should strictly be restricted to `FARMER` and `BUYER`. `ADMIN` accounts must only be provisioned by existing administrators or CLI seed scripts.

---

### Defect SEC-02: Open Redirect via Protocol-Relative URLs
- **Location:** `routes/auth.py` (Lines 120–122)
- **Vulnerability:** CWE-601 (URL Redirection to Untrusted Site)
- **Description:**  
  The login handler redirects to `next_url` if `next_url.startswith('/')`. In web browsers, URLs starting with `//` (protocol-relative URLs like `//attacker.com`) are treated as external links.
- **Steps to Reproduce:**
  1. Access `http://localhost:5000/login?next=//google.com`.
  2. Enter valid credentials (`farmer1` / `Farmer@123`).
  3. Click "Log In".
  4. The browser redirects off-site to `https://google.com`.
- **Expected Behavior:**  
  `next_url` must be validated to ensure it starts with `/` and does NOT start with `//` or `/\\`.

---

### Defect SEC-03 & SEC-04: Insecure Direct Object References (IDOR) on Farm & Crop Links
- **Location:** `routes/crops.py` (Line 25), `routes/traceability.py` (Lines 89–90), `routes/marketplace.py` (Line 97)
- **Vulnerability:** CWE-639 (Insecure Direct Object References)
- **Description:**  
  When adding crops, batches, or product listings, the server takes `farm_id` and `crop_id` directly from form inputs and assigns them to the new record without checking whether the specified `Farm` or `Crop` actually belongs to the authenticated `session['user_id']`.
- **Steps to Reproduce:**
  1. Log in as `farmer1`.
  2. Inspect `/crops/add` form in DevTools and tamper the hidden `farm_id` input to an ID owned by another user.
  3. The crop is successfully attached to a farm owned by someone else.
- **Expected Behavior:**  
  The backend must query `Farm.query.filter_by(id=farm_id, user_id=session['user_id']).first()` before assigning.

---

### Defect LOG-01: Inventory Leak on Order Cancellation
- **Location:** `routes/orders.py` (Lines 64–86), `services/marketplace_service.py` (Lines 59–63)
- **Vulnerability:** Business Logic Flaw / Data Inconsistency
- **Description:**  
  When a buyer places an order for 50 kg of tomatoes, `product.quantity` is immediately decremented from 100 kg to 50 kg. If the order is subsequently marked as `Cancelled` in `/orders/<id>/status`, the 50 kg is never added back to `product.quantity`, causing permanent stock loss.
- **Steps to Reproduce:**
  1. Note available quantity of a product (e.g. 100 kg).
  2. Place an order for 40 kg as a buyer. Remaining stock is now 60 kg.
  3. As farmer/admin, change order status to `Cancelled`.
  4. Check product stock — it remains 60 kg instead of reverting to 100 kg.
- **Expected Behavior:**  
  When status transitions from an active status to `Cancelled`, `product.quantity` must be restored, and if `product.availability_status == 'Sold Out'`, it must revert to `'Available'`.

---

### Defect LOG-02: Permanent Resource Lockout on Reservations
- **Location:** `routes/reservations.py`, `services/marketplace_service.py`
- **Vulnerability:** Resource State Machine Defect
- **Description:**  
  When a harvest is reserved by a buyer, `harvest.reserved_quantity` is locked. However, the system provides no cancellation mechanism for either buyer or farmer. If negotiations fail or an order cannot proceed, the reserved harvest volume remains permanently inaccessible.
- **Expected Behavior:**  
  Provide a cancellation endpoint that safely decrements `harvest.reserved_quantity` and marks the reservation as `'Cancelled'`.

---

### Defect RUN-01: Substring Greeting Collision in AI Chatbot
- **Location:** `services/chatbot_service.py` (Line 122)
- **Vulnerability:** Logic & NLP Match Defect
- **Description:**  
  The chatbot performs greeting detection with:
  ```python
  if any(g in query for g in ['hi', 'hello', 'hey', 'namaste']):
  ```
  Because `'hi'` is a 2-letter substring, common English agricultural queries like:
  - *"How do I control w**hi**tefly?"*
  - *"T**hi**s tomato plant has spots"*
  - *"W**hi**ch fertilizer should I use?"*  
  All trigger `any(...) == True`, causing the chatbot to discard the user's question and respond with the generic greeting.
- **Steps to Reproduce:**
  1. Open `/chatbot`.
  2. Type: *"What is the organic treatment for whitefly on this plant?"*
  3. The bot responds with the default greeting *"Hello! I am AgriTrust AI..."* instead of the Integrated Pest Management guidance.
- **Expected Behavior:**  
  Greetings should be matched as complete words using word boundaries (`r'\b(hi|hello|hey|namaste)\b'`).

---

### Defect VAL-01 & VAL-02: Unhandled `ValueError` 500 Server Crashes
- **Location:** `routes/recommendations.py` (Line 29), `routes/orders.py` (Line 50), `routes/reservations.py` (Line 99), `routes/analytics.py` (Line 79)
- **Vulnerability:** CWE-754 (Improper Check for Unusual Conditions)
- **Description:**  
  Direct calls to `float(...)` or `int(...)` without `try...except ValueError` blocks cause Flask to throw an unhandled exception and display a `500 Internal Server Error` page whenever non-numeric data is posted.
- **Steps to Reproduce:**
  1. Submit `/recommendations` with land size set to `"two"`.
  2. The server crashes with HTTP 500 `ValueError: could not convert string to float: 'two'`.
- **Expected Behavior:**  
  Validate numeric inputs gracefully with fallback defaults or a flash error message.

---

### Defect VAL-03: Permitting Negative Numeric Values
- **Location:** `routes/farms.py` (Line 68), `routes/general.py` (Line 149), `routes/dashboard.py` (Line 279)
- **Vulnerability:** CWE-20 (Improper Input Validation)
- **Description:**  
  While creation routes check for positive values, update routes omit checks for negative numbers. A user can update a farm to `-10` acres, a product to `-50` ₹, or a demand to `-100` kg.
- **Expected Behavior:**  
  All quantity, price, and acreage fields must enforce `>= 0` (or `> 0`).

---

### Defect VAL-04: Chronological Inversion in Date Inputs
- **Location:** `routes/crops.py` (Line 40–41), `routes/reservations.py` (Line 55), `routes/general.py` (Line 148)
- **Vulnerability:** Business Logic Validation
- **Description:**  
  - In `/crops/add`, a user can set `expected_harvest_date` before `planting_date`.
  - In `/future-harvests/create`, a user can list a harvest with `expected_harvest_date` in the past.
- **Expected Behavior:**  
  Validate that `expected_harvest_date >= planting_date` and future harvest dates are in the future.

---

### Defect LOG-03: Lifecycle Update Audit Trail Bypass
- **Location:** `routes/traceability.py` (Lines 189–209)
- **Vulnerability:** Inconsistent Audit Trail / Compliance Breach
- **Description:**  
  The endpoint `POST /batches/<id>/update-stage` updates `batch.journey_stage` but omits creating a `BatchVerificationLog` entry. In contrast, `routes/admin.py:update_lifecycle_stage` properly logs this transition.
- **Expected Behavior:**  
  All lifecycle updates must uniformly record an entry in `BatchVerificationLog`.

---

## 4. Antigravity Remediation Prompt

Below is the ready-to-run Antigravity prompt designed to patch all 18 defects across the AgriTrust codebase in a single automated pass:

```markdown
### MASTER ANTIGRAVITY REPAIR PROMPT: AGRITRUST QA FIXES

You are operating as a Senior Full-Stack Engineer and Security Specialist. Implement comprehensive, production-grade fixes for all 18 QA audit defects in AgriTrust:

1. **Security & Authentication (SEC-01 & SEC-02):**
   - In `routes/auth.py`, strictly forbid self-registration as `ADMIN`. In `/register`, if `role == 'ADMIN'`, reject or override to `'FARMER'`. In `templates/register.html`, remove the radio button option for Admin/Inspector registration.
   - In `routes/auth.py:login`, prevent open redirects: Ensure `next_url` starts with `/` and DOES NOT start with `//` or `/\\`.

2. **Insecure Direct Object Reference Checks (SEC-03 & SEC-04):**
   - In `routes/crops.py:add_crop`, verify that `farm_id` (if supplied) belongs to `session['user_id']`.
   - In `routes/traceability.py:create_batch` and `routes/marketplace.py:create_product`, verify that any associated `farm_id` and `crop_id` belong to `session['user_id']`. If not, set to `None` or flash an error.

3. **Admin Self-Demotion Safeguard (SEC-05):**
   - In `routes/admin.py:change_user_role`, check if `user.id == session['user_id']` and `new_role != 'ADMIN'`. Block self-demotion with a flash warning.

4. **Inventory Restoration on Order Cancellation (LOG-01):**
   - In `routes/orders.py:update_order_status`, when transitioning an order from any non-cancelled status to `'Cancelled'`, restore `order.quantity` back to `order.product.quantity`. If `order.product.availability_status == 'Sold Out'`, restore it to `'Available'`.

5. **Harvest Reservation Cancellation Support (LOG-02):**
   - In `routes/reservations.py`, add a route `/reservations/<int:id>/cancel` allowing a buyer or farmer to cancel a reservation, which decrements `harvest.reserved_quantity` and updates status to `'Cancelled'`.

6. **Fix Chatbot Substring Collision (RUN-01):**
   - In `services/chatbot_service.py:get_chatbot_response`, replace `any(g in query for g in ['hi', ...])` with exact whole-word matching using regular expression word boundaries `r'\b(hi|hello|hey|namaste)\b'` so queries containing words like 'whitefly' or 'this' match agronomy topics properly.

7. **Prevent 500 Crashes from Invalid Input (VAL-01 & VAL-02):**
   - In `routes/recommendations.py` and `ai/crop_recommendation.py`, catch `ValueError` when converting `land_size_acres` and fall back safely to `1.0`.
   - In `routes/orders.py:create_order`, `routes/reservations.py:book_reservation`, and `routes/analytics.py:apply_discount`, enclose string-to-number conversions in `try...except ValueError` with flash error messages instead of unhandled 500 errors.

8. **Enforce Non-Negative and Chronological Logic (VAL-03 & VAL-04):**
   - In `routes/farms.py:edit_farm`, validate `land_area > 0`.
   - In `routes/crops.py:add_crop` and `edit_crop`, validate `expected_harvest_date >= planting_date` and enforce non-negative values for yield, cost, and revenue.
   - In `routes/reservations.py:create_future_harvest`, ensure `expected_harvest_date >= date.today()`.
   - In `routes/general.py:create_demand`, enforce `required_quantity > 0` and `target_price > 0`.
   - In `routes/dashboard.py:edit_batch_details`, enforce `price > 0` and `qty > 0`.

9. **Null Safety & External API Resilience (RUN-02 & RUN-03):**
   - In `routes/orders.py:update_order_status` and `routes/analytics.py:analytics_view`, check `if order.product` before accessing attributes (`order.product.user_id`, `order.product.title`).
   - In `routes/weather.py`, safeguard `data['weather'][0]` with `.get('weather', [{}])[0]` and provide default fallbacks for missing keys.

10. **Audit Trail Consistency & Modernization (LOG-03, PER-01, DEP-01, DEP-02):**
    - In `routes/traceability.py:update_batch_stage`, log an entry to `BatchVerificationLog`. Move `import qrcode` to module level.
    - Replace deprecated `Model.query.get(id)` with `db.session.get(Model, id)`.
    - Update `datetime.utcnow()` references to `datetime.now(timezone.utc)`.
    - Run `pytest` to verify 100% test pass rate.
```
