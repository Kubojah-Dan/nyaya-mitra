# NyayaMitra Comprehensive Threat Model & Security Architecture

**Application:** NyayaMitra — AI for Legal Assistance & Access in India  
**Version:** 1.0.0  
**Status:** ACTIVE  
**Last Updated:** 2026-09-16  

---

## 1. Executive Summary & Architecture Boundaries

NyayaMitra processes unstructured public legal queries, scanned court documents, FIRs, and tenancy contracts to deliver grade 6–8 level legal explanations, deadline tracking, and controlled document drafts. Because users rely on this platform during vulnerable legal disputes, system integrity, privacy preservation, and defense against adversarial manipulation are critical.

```text
[ Citizen / Browser Client ]
         │ (HTTPS / TLS 1.3)
         ▼
[ SecurityHardeningMiddleware ] ─── (Rate Limiting, Size Checks, CSP/HSTS)
         │
[ StructuredLoggingMiddleware ] ─── (PII Redaction of Aadhaar/PAN/Phone)
         │
[ PromptGuardService ] ───────────── (Anti-Jailbreak, Override Detection)
         │
┌────────┴───────────────────────────────────────────────────────┐
│ FastAPI Application Services Layer                             │
│  ├─ Guided Intake Engine ("Samjho Mera Problem")               │
│  ├─ Rights & Timeline Engine ("Mere Adhikaar")                 │
│  ├─ Citation Verifier (Zero Hallucination Verification)        │
│  ├─ SSRF Validator (Official Government URL Allowlist)         │
│  ├─ Controlled Document Generator ("Mera Document")            │
│  └─ Human Escalation Navigator (DLSA / SLSA / Tele-Law 15100)  │
└────────┬───────────────────────────────────────────────────────┘
         │
[ Official Tier-1 Data Sources ] ─── (India Code, NALSA, eCourts, Tele-Law)
```

---

## 2. STRIDE Threat Matrix & Vector Mitigations

| Threat Vector | STRIDE Category | Risk Level | Specific Vulnerability Scenario | NyayaMitra Defense & Countermeasure |
|:---|:---|:---|:---|:---|
| **1. Prompt Injection & Jailbreaks** | Tampering / Elevation of Privilege | HIGH | Adversarial users attempt "Ignore previous instructions", DAN mode, or roleplay escapes to bypass disclaimers or generate illegal advice. | `PromptGuardService` performs signature inspection across 5 adversarial classes, sanitizing or blocking inputs before LLM ingestion. |
| **2. Malicious File & PDF Attacks** | Tampering / DoS | HIGH | Uploading disguised executables, macro-enabled files, or zip/PDF decompression bombs. | `DocumentSecurityValidator` validates magic bytes, restricts MIME types, limits file sizes to ≤10MB, and runs executable pattern scans. |
| **3. OCR & Processing Abuse** | Denial of Service | MEDIUM | Resource exhaustion attacks via repeated heavy image uploads or ReDoS regex queries. | Strict upload rate limiting (20 req/min), polynomial-free non-backtracking regex engines, and fallback memory-safe extractors. |
| **4. PII Exfiltration & Data Leakage** | Information Disclosure | HIGH | Accidental logging or storage of 12-digit Aadhaar, 10-digit PAN, or phone numbers. | Automatic PII redaction layer masks personal IDs in logs, request traces, and extracted text previews prior to persistence. |
| **5. Prompt & Instruction Leakage** | Information Disclosure | MEDIUM | Attackers querying the model to output proprietary system prompts or API keys. | `PROMPT_EXFILTRATION_ATTEMPT` heuristics detect queries probing system instructions and return sanitized responses. |
| **6. API Key & Credential Exposure** | Information Disclosure | CRITICAL | Accidental hardcoding or git tracking of environment keys. | Strict `.gitignore` policy, environment-variable injection via `pydantic-settings`, and automated secret scanning. |
| **7. Denial of Service (DoS)** | Denial of Service | HIGH | High-concurrency bot floods overwhelming backend endpoints. | `SecurityHardeningMiddleware` applies sliding-window IP rate limiting (120 req/min standard, 20 req/min upload) returning `429 Too Many Requests`. |
| **8. Source Poisoning & Stale Data** | Tampering | HIGH | Upstream outage or corrupted statutory repositories leading to inaccurate legal guidance. | `CircuitBreaker` pattern (CLOSED/OPEN/HALF-OPEN), SHA-256 snapshot hashing, and offline Tier-1 seed fallback corpus. |
| **9. Citation Spoofing & Hallucinations** | Spoofing | CRITICAL | LLM hallucinating fictitious case laws or non-existent section numbers. | `CitationVerifier` enforces that 100% of citations match ground-truth Tier-1 enactments (`VERIFIED_TIER_1`); rejects fabricated citations. |
| **10. User Impersonation & Session Hijacking** | Spoofing / Tampering | MEDIUM | Unauthorized access to session data across clients. | Ephemeral UUIDv4 tokens, anonymized session IDs, and zero cross-session state leakage. |
| **11. Unsafe Legal Document Generation** | Repudiation / Tampering | HIGH | Uncontrolled generation of legally invalid or fabricated affidavits. | `DocumentGeneratorService` uses deterministic Pydantic slot-filling into vetted statutory templates with mandatory non-lawyer disclaimers. |
| **12. Server-Side Request Forgery (SSRF)** | Elevation of Privilege | CRITICAL | Exploiting outbound retrieval URLs to probe cloud metadata (`169.254.169.254`) or internal subnets (`10.0.0.0/8`, `127.0.0.1`). | `SSRFValidator` restricts outbound requests to an official government allowlist (`*.gov.in`, `*.nic.in`) and blocks all private/link-local IP subnets. |

---

## 3. Defense-in-Depth Security Controls

### A. Network & HTTP Transport Hardening
- **Security Headers Injected**:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy: default-src 'self'`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- **CORS Allowlist**: Strict origin validation restricting unauthorized cross-origin requests.

### B. Input Validation & Size Enforcement
- Non-upload JSON endpoints restricted to 2 MB max body size (`413 Payload Too Large`).
- File uploads restricted to 12 MB max body size with magic byte confirmation.

### C. Legal Ethics & Safety Guardrails
- **Mandatory Non-Lawyer Disclaimer**: Every single API response and generated document draft carries an explicit statutory disclaimer.
- **Section 12 LSAA Escalation**: Matters involving arrest, police custody, or domestic violence automatically route to the National 15100 Legal Aid Helpline.

---

## 4. Security Checklist & Audit Verification

- [x] Rate limiting active on all non-health routes
- [x] SSRF protection blocking `127.0.0.1`, `localhost`, and AWS/GCP metadata (`169.254.169.254`)
- [x] Prompt injection scanner active across all input text
- [x] PII redaction active across logging and document processing
- [x] Zero unverified legal citations permitted in responses
- [x] Security headers present on all HTTP responses
