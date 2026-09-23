# NyayaMitra — Production Operations & Incident Runbook

> **Purpose:** Operational guide for engineers, administrators, and DevOps teams running, maintaining, and recovering the NyayaMitra platform in production environments.

---

## 1. System Architecture & Observability Endpoints

### Health Probes & Monitoring URLs
- **Liveness Probe (Kubernetes):** `GET /api/v1/health/live` (Returns `200 {"status": "alive"}`)
- **Readiness Probe (Kubernetes):** `GET /api/v1/health/readiness` (Validates DB connectivity, cache readiness, and statutory baseline indexing)
- **Source Health Dashboard:** `GET /api/v1/health/sources` (Reports health, tier, publisher, and circuit breaker status for India Code, NALSA, eCourts, Tele-Law)
- **Model Tiers & Pricing:** `GET /api/v1/health/models` (Reports active providers, fallback status, latency, and telemetry)
- **Real-Time Telemetry:** `GET /api/v1/health/metrics` (Live requests per minute, status code distributions, latency p50/p90/p95, cache hit ratios)

---

## 2. Incident Classification & Severity Matrix

| Severity | Definition | Target Response (SLA) | Primary Action |
|:---|:---|:---|:---|
| **P0 (Critical)** | Core intake or rights engine offline; 5xx rate > 5%; fabricated citation detected in production. | **< 15 minutes** | Immediate rollback / circuit breaker failover to deterministic seed baseline. |
| **P1 (High)** | Upstream official source (India Code/NALSA) unreachable; primary LLM provider timing out; OCR pipeline degraded. | **< 30 minutes** | Trigger model router fallback / seed corpus cache fallback. |
| **P2 (Medium)** | Non-blocking document formatting bug; rate limiting false positives on specific IP; latency p95 > 250ms. | **< 2 hours** | Inspect LRU cache eviction and rate limiter sliding windows. |

---

## 3. Upstream Outage Playbooks

### Playbook A: India Code / Legislative Department Outage
- **Symptoms:** `GET /api/v1/health/sources` reports `INDIA_CODE` circuit breaker `OPEN`.
- **System Behavior:** `IndiaCodeAdapter` immediately serves pre-verified offline seed corpus (`BNS_2023`, `BNSS_2023`, `BSA_2023`, `CPA_2019`, `RTI_2005`, `TPA_1882`, `NI_1881`, `LSAA_1987`).
- **Action:** No emergency restart required. Monitor upstream recovery. Circuit breaker automatically probes upstream via half-open state every 60 seconds.

### Playbook B: AI / LLM Provider Outage (Gemini / Anthropic / OpenAI)
- **Symptoms:** Inbound LLM calls return `503 Service Unavailable` or exceed 3.0s timeout.
- **System Behavior:** `ModelRouterService` automatically shifts traffic from primary provider to secondary fallback provider within the same tier. If all external providers fail, the router activates the `DETERMINISTIC_FALLBACK` baseline without raising 500 errors to citizens.
- **Action:**
  1. Check provider status dashboards (Google Cloud Status / Anthropic Status).
  2. If a specific provider remains unstable, update `.env` `PRIMARY_LLM_PROVIDER` and trigger rolling pod restart.

### Playbook C: eCourts / NJDG Outage
- **Symptoms:** eCourts case search queries time out.
- **System Behavior:** System gracefully notifies the user that live court synchronization is temporarily unreachable and provides direct official links to `https://services.ecourts.gov.in`.

---

## 4. Secret & API Key Rotation Checklist

1. **FastAPI Secret Key / JWT Key:**
   - Generate new random key: `python -c "import secrets; print(secrets.token_hex(32))"`
   - Update `SECRET_KEY` in environment manager / Kubernetes secrets.
   - Trigger zero-downtime rolling restart.
2. **AI Provider Keys (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`):**
   - Generate new key in provider console.
   - Update secret store.
   - Test model health via `GET /api/v1/health/models`.
   - Decommission old key in provider console.

---

## 5. User Data Deletion & Privacy Lifecycle

- **Data Minimization Standard:** NyayaMitra does not persist raw citizen PII beyond the active intake session.
- **Temporary Upload Deletion:** Uploaded documents (FIRs, Notices) are stored in temporary memory/disk storage and automatically purged after extraction or session termination.
- **Ad-Hoc Data Purge Command:**
  ```bash
  python -c "from app.services.cache_service import global_cache; global_cache.clear()"
  ```

---

## 6. Database Rollback Procedures

```bash
# Check current migration revision
alembic current

# Roll back 1 revision
alembic downgrade -1

# Roll back to specific baseline
alembic downgrade <revision_id>
```
