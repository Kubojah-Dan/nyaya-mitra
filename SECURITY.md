# Security Policy — NyayaMitra

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security and privacy of citizen legal queries seriously. If you discover a vulnerability or potential exploit, please report it privately:

1. **Email:** Send details to `security@nyayamitra.org` (or create a private GitHub Advisory).
2. **Details to Include:**
   - Description of the vulnerability and potential impact.
   - Exact steps to reproduce or proof-of-concept.
   - Any suggested mitigations.
3. **Disclosure Policy:** We follow coordinated vulnerability disclosure. Please allow up to 48 hours for an acknowledgment and up to 30 days for remediation before public disclosure.

## Core Security Commitments

1. **Zero Secret Leakage:** No API keys, credentials, or production tokens are committed to source control. CI enforces automated secret scanning via Gitleaks.
2. **Privacy by Design (DPDPA 2023):** Zero raw PII logging. Personal names, phone numbers, Aadhaar, and case details are masked prior to structured log persistence.
3. **Prompt-Injection Defense:** External legal text, retrieved documents, and user-uploaded files are treated strictly as untrusted data and isolated from system directives.
4. **Data Minimization:** User sessions are ephemeral and transient. Uploaded documents are automatically pruned with a 24-hour TTL.

## Threat Model Traceability Matrix (STRIDE)

Cross-referenced from [docs/THREAT_MODEL.md](file:///d:/Legal-Assistance-Access/docs/THREAT_MODEL.md):

| Threat ID | Threat Vector | STRIDE Category | Mitigation Strategy | Implementation File / Line |
|:---|:---|:---|:---|:---|
| **TM-01** | Prompt Injection & Jailbreak | Tampering / Elevation | Multi-pattern heuristic & injection signature scanner | [`backend/app/services/prompt_guard.py`](file:///d:/Legal-Assistance-Access/backend/app/services/prompt_guard.py#L26-L120) |
| **TM-02** | SSRF (Outbound Metadata Probing) | Elevation of Privilege | Strict gov/nic allowlist & private IP blocking | [`backend/app/utils/security_urls.py`](file:///d:/Legal-Assistance-Access/backend/app/utils/security_urls.py#L12-L70) |
| **TM-03** | PII Exposure (Aadhaar / PAN / Phone) | Information Disclosure | Regex redaction in structured logging & preview extraction | [`backend/app/middleware/logging.py`](file:///d:/Legal-Assistance-Access/backend/app/middleware/logging.py#L20-L80) & [`ocr_service.py`](file:///d:/Legal-Assistance-Access/backend/app/services/ocr_service.py#L115-L160) |
| **TM-04** | Malicious File & Zip/PDF Bombs | Tampering / DoS | Magic byte validation, strict MIME enforcement, 10MB limit | [`backend/app/services/ocr_service.py`](file:///d:/Legal-Assistance-Access/backend/app/services/ocr_service.py#L25-L95) |
| **TM-05** | Rate-Limit & DoS Abuse | Denial of Service | Sliding-window IP rate limiter (120 req/min, 20 upload/min) | [`backend/app/middleware/security.py`](file:///d:/Legal-Assistance-Access/backend/app/middleware/security.py#L15-L65) |
| **TM-06** | Citation Hallucination & Fabrication | Spoofing | Deterministic Tier-1 statutory enactment verification | [`backend/app/services/citation_verifier.py`](file:///d:/Legal-Assistance-Access/backend/app/services/citation_verifier.py#L20-L90) |
| **TM-07** | Upstream Provider Outage | Denial of Service | Multi-tier fallback circuit (Gemini → Groq → Deterministic) | [`backend/app/services/model_router.py`](file:///d:/Legal-Assistance-Access/backend/app/services/model_router.py#L77-L215) |
| **TM-08** | Insecure Document Generation | Repudiation / Tampering | Deterministic Pydantic slot-filling into vetted templates | [`backend/app/services/document_generator.py`](file:///d:/Legal-Assistance-Access/backend/app/services/document_generator.py#L30-L150) |
| **TM-09** | Missing Security Headers | Information Disclosure | Next.js & FastAPI CSP, HSTS, X-Frame-Options, Referrer-Policy | [`frontend/next.config.mjs`](file:///d:/Legal-Assistance-Access/frontend/next.config.mjs#L2-L40) & [`backend/app/main.py`](file:///d:/Legal-Assistance-Access/backend/app/main.py#L70-L82) |
| **TM-10** | Production Fail-Closed API Contract | Configuration Tampering | Throw explicit fatal error if API URL unset in production | [`frontend/lib/api.ts`](file:///d:/Legal-Assistance-Access/frontend/lib/api.ts#L7-L15) |
| **TM-11** | Stale Outdated Law Dissemination | Information Disclosure | Automatic IPC/CrPC/IEA → BNS/BNSS/BSA transition mapping | [`backend/app/services/transition_mapping.py`](file:///d:/Legal-Assistance-Access/backend/app/services/transition_mapping.py#L15-L80) |
| **TM-12** | Secret & API Key Leakage | Information Disclosure | Gitleaks CI scanning, zero secrets in source, env loading | [`.github/workflows/ci.yml`](file:///d:/Legal-Assistance-Access/.github/workflows/ci.yml#L10-L25) |
