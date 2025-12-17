# Route Mismatch Analysis - December 16, 2025

## Problem

The Playwright tests are failing because they're trying to access routes that **don't exist** in the Django application.

## Actual Django Routes

Based on `DjangoEcommerceApp/adminurls.py` and `DjangoEcommerce/urls.py`:

### Admin Routes (Actual)
- `/admin/` - Admin login page
- `/admin_login_process` - Admin login processing
- `/admin_logout_process` - Admin logout
- `/admindashboard/` - Admin dashboard (includes product routes)

### Product Routes (Actual)
- `/admindashboard/product_list` - Product list
- `/admindashboard/product_edit/<product_id>` - Product edit
- `/admindashboard/product_create` - Product creation

## Test Routes (Expected but Missing)

The tests are trying to access:

### Authentication Routes (DO NOT EXIST)
- ❌ `/auth/login/` - **Does not exist**
- ❌ `/auth/register/` - **Does not exist**
- ❌ `/auth/password-reset/` - **Does not exist**

### API Routes (DO NOT EXIST)
- ❌ `/api/auth/login/` - **Does not exist** (returns 404)
- ❌ `/api/auth/register/` - **Does not exist**

## Root Cause

The Playwright tests (`test_django_auth.py`) were written for a **different Django application structure** that has:
- REST API endpoints under `/api/auth/`
- User-facing auth pages under `/auth/`

But this Django Amazon Clone app uses:
- Admin-only authentication
- No REST API layer
- Different URL structure

## Solutions

### Option 1: Update Tests to Match Actual Routes (Recommended)
Update `test_django_auth.py` to test the actual admin routes:
- Change `/auth/login/` → `/admin/`
- Change `/auth/register/` → Remove (no registration in this app)
- Change `/api/auth/login/` → Remove (no API in this app)

### Option 2: Add Missing Routes to Django App
Add the routes the tests expect:
- Create `/auth/login/` view
- Create `/api/auth/login/` API endpoint
- Create registration and password reset routes

### Option 3: Skip/Remove Incompatible Tests
Mark tests as skipped if they test features not present in this app.

## Recommendation

**Option 1** is recommended because:
1. Tests should match the actual application behavior
2. This app is admin-only, not a public-facing e-commerce site
3. No API layer exists, so API tests are invalid

## Next Steps

1. ✅ Fix event loop issue in `conftest.py` (DONE)
2. ⏳ Update `test_django_auth.py` to use actual routes OR mark as skipped
3. ⏳ Update `test_product_edit.py` to use correct product edit route (`/admindashboard/product_edit/1`)
4. ⏳ Remove or skip API rate limit tests (no API exists)


