# NyayaMitra — Legal Source & Data Freshness Policy

**Document Version:** 1.0.0  
**Phase:** 0 — Product Contract, Scope & Legal-Safety Boundaries  
**Status:** Approved Policy  
**Scope:** Ingestion, Verification, Retrieval, and Citation of Indian Legal Materials  

---

## 1. Fundamental Principle: Source Before Generation

In NyayaMitra, **the Large Language Model is never the source of legal truth**. All statutory provisions, rights statements, procedural deadlines, and legal-aid directory information must originate from verifiable, version-controlled records in our index.

Every legal proposition surfaced to the user must be attributable to:
```text
Act Name → Section / Rule → Subsection/Proviso → Source Snapshot → Source URL → Retrieval Timestamp
```

---

## 2. Source Classification Hierarchy

All external data utilized by NyayaMitra is strictly classified into three tiers:

```
┌─────────────────────────────────────────────────────────────┐
│  Tier 1 — Authoritative Primary Sources                     │
│  India Code, Official Gazettes, eCourts, NALSA/DLSA portals │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Overrides all secondary sources)
┌──────────────────────────────▼──────────────────────────────┐
│  Tier 2 — Official Institutional Sources                    │
│  Government Ministry FAQs, State Citizen Portals, Regulators│
└──────────────────────────────┬──────────────────────────────┘
                               │ (Informational only)
┌──────────────────────────────▼──────────────────────────────┐
│  Tier 3 — Trusted Secondary Research & Discovery Sources    │
│  Judicial education manuals, recognized legal portals       │
└─────────────────────────────────────────────────────────────┘
```

### Tier 1: Authoritative Primary Sources (Highest Precedence)
- **Legislation:** [India Code](https://www.indiacode.nic.in) (Official digital repository of all Central & State Acts).
- **Gazette Notifications:** The Gazette of India ([egazette.gov.in](https://egazette.gov.in)) and State Gazettes for commencement dates, amendments, and subordinate rules.
- **Judicial Services:** Official eCourts portal ([ecourts.gov.in](https://ecourts.gov.in)), National Judicial Data Grid (NJDG), and Supreme Court of India portal.
- **Legal Aid Directories:** National Legal Services Authority ([nalsa.gov.in](https://nalsa.gov.in)), State Legal Services Authorities (SLSAs), District Legal Services Authorities (DLSAs), and Department of Justice Tele-Law portal ([tele-law.in](https://www.tele-law.in)).
- **Statutory Regulators & Tribunals:** National Consumer Disputes Redressal Commission (NCDRC), Central Information Commission (CIC), State Information Commissions (SICs), Real Estate Regulatory Authorities (RERAs).

### Tier 2: Official Institutional Sources
- Official Ministry Portals (Ministry of Consumer Affairs, Ministry of Housing and Urban Affairs, Ministry of Law & Justice).
- National Consumer Helpline ([consumerhelpline.gov.in](https://consumerhelpline.gov.in)).
- Official State citizen delivery portals.
- *Usage:* Contextual procedural guidance, fee schedules, helpline routing. Never overrides primary statutory text.

### Tier 3: Trusted Secondary Sources
- Bar Council publications, National Law University research databases, judicial academies.
- *Usage:* Clarifying definitions, historical timelines, educational plain-language translations.
- *Rule:* Tier 3 sources may **never** be cited as sole legal authority and must never contradict a Tier 1 statute.

### Prohibited Sources
- Unverified legal blogs, anonymous forums, crowd-sourced wikis, marketing articles by legal aggregators, and unvetted AI summaries.
- Any source obtained via unauthorized scraping that circumvents CAPTCHAs, paywalls, or `robots.txt`.

---

## 3. The 2024 Indian Criminal Law Transition Protocol

Effective **July 1, 2024**, India transitioned from legacy colonial criminal codes to modern statutory enactments:
1. **Bharatiya Nyaya Sanhita, 2023 (BNS)** replaced the Indian Penal Code, 1860 (IPC).
2. **Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)** replaced the Code of Criminal Procedure, 1973 (CrPC).
3. **Bharatiya Sakshya Adhiniyam, 2023 (BSA)** replaced the Indian Evidence Act, 1872 (IEA).

### Mandatory System Rules for Criminal Law
1. **Default to Current Law:** The system must answer all current queries using BNS, BNSS, and BSA provisions.
2. **Strict Prohibition on Citing Repealed Law as Current:** Under no circumstances should IPC, CrPC, or IEA be cited as active governing law for offences or procedures taking place after July 1, 2024.
3. **Historical Concordance Mapping:**
   - Where an older case, document, FIR, or user query mentions an IPC section (e.g. *"IPC 420"* or *"IPC 302"*), the system must:
     - Explicitly label it: `[Historical / Legacy Provision: IPC Section 420]`.
     - Provide the verified current equivalent: `[Current Equivalent: BNS Section 318(4) - Cheating]`.
     - Explain that events committed prior to July 1, 2024 are prosecuted under IPC/CrPC, while subsequent acts fall under BNS/BNSS.
4. **Validation Gate:** Any generated output citing IPC or CrPC without an explicit historical concordance badge fails citation validation and will be rejected before reaching the user.

---

## 4. Source Record Schema & Provenance Metadata

Every source ingested and indexed in NyayaMitra must conform to the following Pydantic / DB schema:

```python
class SourceRecord(BaseModel):
    source_id: str                      # UUID / canonical identifier (e.g. "ind-act-bns-2023")
    title: str                          # Full formal title
    short_title: str                    # e.g. "BNS 2023"
    publisher: str                      # e.g. "Legislative Department, Ministry of Law and Justice, GoI"
    source_url: HttpUrl                 # Canonical URL on Tier 1 domain
    source_tier: Literal[1, 2, 3]       # 1, 2, or 3
    source_type: str                    # "act", "rule", "notification", "directory", "faq"
    retrieved_at: datetime              # Timestamp when crawled/snapshotted
    published_at: Optional[datetime]    # Official gazette publication date
    effective_from: Optional[date]      # Date of legal enforcement (e.g. 2024-07-01)
    effective_to: Optional[date]        # Date of repeal/expiry (None if current)
    content_hash: str                   # SHA-256 hash of the normalized source text
    version_label: str                  # e.g. "As enacted", "2024-amendment"
    jurisdiction: str                   # "Central", "State:Delhi", "State:Maharashtra", etc.
    language: str                       # "en", "hi"
    verification_status: str            # "verified", "provisional", "deprecated"
```

---

## 5. Dynamic Data Refresh & Freshness Policy

"Real-time" in legal-tech does not mean indiscriminate live web scraping on every user keystroke. It means **audited, freshness-aware ingestion** with proactive change detection:

### Refresh Schedules by Source Category
| Source Category | Refresh Cadence | Change Detection Mechanism | Fallback Behavior |
| :--- | :--- | :--- | :--- |
| **Central Acts (BNS, CPA, RTI)** | Weekly / On-demand Gazette watch | SHA-256 content diff against India Code | Serve last validated snapshot; log alert |
| **Official Gazettes & Rules** | Bi-weekly | RSS / Official portal scraper | Flag if snapshot > 30 days old |
| **NALSA / DLSA Directories** | Monthly | Periodic crawl of official directories | Display directory with `[Verified as of: <date>]` |
| **eCourts Status Queries** | Live / User-initiated | Official public CNR search API/link | If upstream down, provide direct official URL |

### Source Freshness Indicators on the UI
Users must see clear, human-readable freshness badges alongside citations:
- 🟢 `Verified from India Code (Checked: Sept 2026)`
- 🟡 `Snapshot from NALSA Directory (Updated: Aug 2026)`
- 🔴 `Upstream Source Temporarily Unreachable (Showing cached record)`

---

## 6. Prohibited Scraping & Compliance Safeguards

1. **Adherence to Access Controls:** No crawling behind logins, CAPTCHAs, or sessions without official written permission or API keys.
2. **Rate Limiting & Politeness:** All automated crawler requests must use configured timeouts (10s), exponential backoff, User-Agent identification (`NyayaMitra-LegalAccess-Bot/1.0`), and concurrency caps (max 2 requests/sec).
3. **SSRF Safeguards:** All URLs fetched by background jobs or adapters must pass an IP/domain allowlist check; internal subnet ranges (`127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`, AWS/GCP metadata endpoints) are strictly blocked.
