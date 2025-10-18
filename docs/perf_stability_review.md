# Performance and Stability Review

## Summary
This document captures the most significant performance and stability concerns observed during the review of the backend code. Each finding includes the affected code locations, the identified risk, and suggested remediation steps. All observations assume the production deployment is backed by MySQL, which the team has confirmed is the only database that needs to be supported.

## Findings

### 1. In-memory rate limiter grows without bounds and is not thread-safe
* **Location:** `backend/routes/items.py` — lines 31-151
* **Issue:** Tooltip rate limiting stores request timestamps for each client IP in a global `defaultdict(list)` and never cleans up idle keys. Under real traffic with many unique IPs, the dictionary will retain empty lists indefinitely, slowly consuming memory. Additionally, mutating shared lists without any locking is unsafe under multi-threaded WSGI servers and can raise `RuntimeError` or lose updates.
* **Impact:** Gradual memory growth and race conditions can degrade performance or crash worker processes under load.
* **Recommendation:** Replace the custom implementation with the existing `flask-limiter` integration or a lock-protected TTL cache (e.g., `cachetools.TTLCache`) that evicts inactive entries. If a custom solution must remain, guard mutations with a threading lock and delete keys when their request list becomes empty.
* **Status:** Addressed by switching to a lock-protected `deque` that prunes expired timestamps on every request while preventing cross-thread mutations.

### 2. MySQL metadata checks lack graceful failure handling
* **Location:** Multiple routes in `backend/app.py` — e.g., lines 2733-3055
* **Issue:** Table-existence checks use `SHOW TABLES LIKE ...`, which is valid for the MySQL-only deployments we support. However, if a required table is missing or corrupted, the code bubbles the raw database error back to the caller without context, making it difficult to distinguish between configuration problems and transient failures.
* **Impact:** Operational issues (schema drift, accidental table drops) manifest as opaque 500 errors, slowing incident response and increasing time to resolution.
* **Recommendation:** Wrap metadata probes with defensive error handling that logs descriptive context and returns a structured 5xx response indicating which table is unavailable. This keeps behavior correct for MySQL while improving diagnosability when the schema is not in the expected state.
* **Status:** Addressed by adding a shared `ensure_mysql_table` helper that standardizes error handling and response payloads when metadata queries fail.

### 3. Each request creates a brand-new database connection
* **Location:** `backend/app.py` — lines 2320-2382
* **Issue:** `get_eqemu_db_connection` bypasses the connection pool and opens a raw connection for every call, even though pooled access is available via `ContentDatabaseManager`. Creating connections is expensive and scales poorly; under concurrency this pattern quickly exhausts database connection limits and increases response latency.
* **Impact:** Elevated connection churn, unnecessary authentication handshakes, and risk of hitting the database's maximum connection count under load, which leads to failed requests.
* **Recommendation:** Expose a context-managed accessor in `ContentDatabaseManager` (or reuse `safe_db_connection`) that draws from the pool and returns connections after use. Refactor routes to rely on this shared pool instead of instantiating new connections on every request.
* **Status:** Addressed by re-enabling pooled access through `ContentDatabaseManager` and returning connections to the pool via a managed proxy.

