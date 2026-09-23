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
