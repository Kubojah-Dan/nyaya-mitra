# NyayaMitra — End-to-End Implementation Plan

> **Purpose:** This document is the execution contract for an AI coding/development agent building NyayaMitra from an empty repository to a production-ready public MVP.
>
> **Operating rule:** Implement the phases strictly in order. Do not skip a phase because a later feature appears easier. Every phase ends with automated verification, manual acceptance checks where specified, a security check, and a written completion report before the next phase begins.

---

## 0. Product Mission

Build a trustworthy, India-focused GenAI legal-access platform that helps ordinary people:

1. explain a problem in plain language or voice;
2. identify the relevant legal area and important facts;
3. understand rights and practical next steps using current, source-grounded Indian law;
4. extract important dates/deadlines from uploaded legal documents;
5. generate useful, editable documents from controlled templates;
6. connect users to appropriate human legal-aid resources when AI should not be the final layer.

This is **not** a general-purpose legal chatbot. The product should behave as a guided legal-information and access-to-services system.

The existing blueprint defines three principal jobs — **Samjho Mera Problem**, **Mere Adhikaar**, and **Mera Document** — with a persistent trust layer. Preserve these as the core experience. fileciteturn0file0L21-L29

The implementation should also preserve the existing modular monorepo separation of frontend, FastAPI backend, services, repositories, prompts, evals, tests, and documentation. fileciteturn0file1L1-L36

---

# 1. Non-Negotiable Engineering Principles

## 1.1 Source before model

The LLM must never be the primary authority for current law, current government services, deadlines, contact details, or case-status information.

Use a source hierarchy:

**Tier 1 — official primary sources**
- India Code / Government legislation sources
- Gazette / official notifications where applicable
- Supreme Court / High Court / official judiciary sources
- eCourts and NJDG official services
- NALSA / SLSA / DLSA / Tele-Law official resources
- official department or regulator websites

India Code is the Government of India's legislation portal and exposes Acts, sections and subordinate legislation. citeturn812724search4

**Tier 2 — official institutional sources**
- Government department FAQs and schemes
- official state portals
- regulator portals

**Tier 3 — trusted secondary sources**
- only for discovery, cross-checking, or explanatory background;
- never silently override a conflicting primary source.

Every source record should carry:

```text
source_id
publisher
source_url
source_type
retrieved_at
published_at (nullable)
effective_from (nullable)
effective_to (nullable)
content_hash
version_label
jurisdiction
language
verification_status
```

## 1.2 “Real-time” means freshness-aware

Do not promise that every fact is literally live. Instead, expose freshness internally and, when useful, visibly:

- `Verified from official source`
- `Last checked: <date/time>`
- `Source updated: <date>`
- `Freshness: current / stale / unavailable`

If a source cannot be reached, the system must not manufacture a replacement. It should use the last validated snapshot where policy permits and clearly label it, or ask the user to verify manually.

## 1.3 Retrieval-grounded generation only

The rights/explanation pipeline must follow:

**intent → jurisdiction → retrieval → evidence validation → answer generation → citation validation → safety policy → response**

Never:

**user → LLM → legal answer**

## 1.4 Legal text is data, not instructions

Retrieved documents, uploaded PDFs, OCR text, webpages, and search results can contain adversarial or irrelevant text. Treat all retrieved material as untrusted data. Never allow source text to override system/developer policies or execution instructions.

The original blueprint explicitly requires a prompt-injection guardrail for retrieved documents. fileciteturn0file0L63-L67

## 1.5 Deterministic wherever possible

Use deterministic components for:

- dates;
- citation validation;
- section lookup;
- document templates;
- required fields;
- file validation;
- source freshness;
- escalation contacts;
- rate limiting;
- policy checks.

Use the LLM for:

- intent interpretation;
- question generation;
- natural-language transformation;
- multilingual understanding;
- summarization;
- controlled slot filling;
- explanation generation.

## 1.6 Human escalation is a product feature, not an error

When a situation is high-risk, ambiguous, fact-heavy, urgent, or outside the supported workflow, stop pretending AI is sufficient and guide the user to appropriate human assistance.

NALSA maintains official state legal-services directories, including Tamil Nadu, and the official system should be preferred over a hard-coded contact database. citeturn812724search0turn812724search1

---

# 2. Target Architecture

Use a **modular monorepo + layered backend + source-adapter architecture**.

```text
                         ┌─────────────────────────┐
                         │        Next.js PWA       │
                         │ Mobile-first / WCAG AA   │
                         └────────────┬────────────┘
                                      │ HTTPS / SSE
                         ┌────────────▼────────────┐
                         │     API / BFF Layer      │
                         │ Next.js BFF + FastAPI    │
                         └────────────┬────────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                │                     │                     │
       ┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼─────────┐
       │ Guided Intake   │   │ Rights / RAG    │   │ Document Engine  │
       │ + Routing       │   │ + Citations     │   │ + OCR + Deadlines │
       └────────┬────────┘   └────────┬────────┘   └────────┬─────────┘
                │                     │                     │
                └─────────────────────┼─────────────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │   Policy / Trust Layer  │
                         │ citation checks         │
                         │ safety + escalation     │
                         │ PII controls            │
                         └────────────┬────────────┘
                                      │
             ┌────────────────────────┼────────────────────────┐
             │                        │                        │
    ┌────────▼────────┐     ┌────────▼────────┐      ┌────────▼────────┐
    │ Postgres +      │     │ Redis / Cache   │      │ Object Storage  │
    │ pgvector        │     │ rate limiting   │      │ temporary files │
    └────────┬────────┘     └─────────────────┘      └─────────────────┘
             │
             │
    ┌────────▼─────────────────────────────────────────────────────┐
    │                    Source Adapter Layer                      │
    │ India Code | judiciary/eCourts | NALSA | Tele-Law | states │
    │ official notifications | approved secondary sources        │
    └──────────────────────────────────────────────────────────────┘
```

### Architectural choice

Do **not** start with microservices. Start with a well-factored modular monolith for the backend. It is simpler to test, deploy, observe and keep under the repo-size constraint. Extract services later only when traffic or operational requirements justify it.

The original design already calls for thin routers, fat services, repositories, versioned prompts and first-class evals; retain that structure. fileciteturn0file1L138-L145

---

# 3. Recommended Technology Baseline

Use these as defaults; the agent may replace a component only after documenting the reason in `/docs/ARCHITECTURE_DECISIONS.md`.

### Frontend

- Next.js App Router
- TypeScript strict mode
- Tailwind CSS
- shadcn/ui or equivalent accessible component system
- PWA / service worker
- TanStack Query or equivalent server-state layer
- Zod for client validation
- Web Speech API for browser-native voice where supported

### Backend

- Python 3.11+
- FastAPI
- Pydantic v2 / pydantic-settings
- SQLAlchemy or equivalent typed data-access layer
- Alembic migrations
- httpx async HTTP client
- structured logging

### Data

- PostgreSQL
- pgvector
- Redis-compatible cache/rate limiter
- object storage for temporary user documents

### AI

Implement a provider abstraction:

```text
LLMProvider
 ├── primary provider
 ├── fallback provider
 └── deterministic/mock provider for tests
```

Never scatter provider-specific SDK calls throughout business logic.

### Documents

- controlled HTML/Jinja templates
- HTML → PDF using a server-side renderer
- editable structured field model
- document integrity checks before delivery

### OCR

- OCR adapter abstraction
- local/self-hosted OCR as default where practical
- optional managed OCR provider behind an adapter
- multilingual OCR path

### Testing

- pytest
- pytest-cov
- FastAPI TestClient/httpx
- frontend unit tests
- Playwright end-to-end tests
- accessibility checks
- prompt/eval harness
- secret scanning

The original plan specifies pytest, endpoint tests, a 50-query legal evaluation harness, and mockable LLM dependencies. fileciteturn0file0L63-L67

---

# 4. Source & Data Strategy

## 4.1 Build a source registry

Create:

```text
backend/app/sources/
  registry.py
  models.py
  freshness.py
  policies.py
  adapters/
    indiancode.py
    ecourts.py
    nalsa.py
    telelaw.py
    state_portals.py
    notifications.py
```

Do not hard-code source URLs inside random service functions.

Each adapter must implement a common interface similar to:

```python
class SourceAdapter(Protocol):
    async def health(self) -> SourceHealth: ...
    async def fetch(self, request: SourceRequest) -> SourceResponse: ...
    async def normalize(self, response: SourceResponse) -> list[NormalizedRecord]: ...
    async def verify(self, record: NormalizedRecord) -> VerificationResult: ...
```

## 4.2 Legal corpus

Initial corpus should prioritize current central legislation relevant to the supported workflows, including BNS/BNSS/BSA and other citizen-facing statutes selected during discovery.

Do not assume that one static PDF is sufficient. Store versioned legal records with effective dates and source hashes.

The existing blueprint correctly treats post-2024 statutory accuracy as a central differentiator and expects BNS/BNSS/BSA rather than obsolete IPC/CrPC/Evidence Act references. fileciteturn0file0L11-L14

## 4.3 Current-law verification

Every citation displayed to a user should be traceable to:

```text
act → section → subsection (if applicable) → source snapshot → source URL → retrieval timestamp
```

Citation validator requirements:

- citation exists;
- act name matches;
- section exists in the indexed version;
- jurisdiction matches;
- source is allowed;
- source is current for the answer's relevant date;
- answer claim is supported by retrieved evidence.

## 4.4 Case-status and judiciary data

The eCourts services expose case lookup workflows including CNR, case number, party name, advocate name, FIR number, Act and case type, subject to their service controls. citeturn812208search0turn812208search3

Do not bypass CAPTCHA, anti-bot protections, rate limits, or access restrictions. If a direct machine interface is unavailable, do not build a fragile scraper just to claim “real-time.” Instead:

1. use an official API/feed when available;
2. use official publicly permitted endpoints where allowed;
3. link the user to the official search workflow;
4. accept user-supplied CNR/case information for guided lookup;
5. mark the data as external/currently unavailable when verification cannot be performed.

## 4.5 Legal-aid directory

Build the escalation service around official NALSA/SLSA/DLSA sources rather than a static list. The NALSA directory identifies state legal-services authorities, and state directories can provide district-level information. citeturn812724search0turn812724search1

The system should store:

```text
authority_name
state
jurisdiction
address
phone
email
website
source_url
retrieved_at
```

---

# 5. Public UX Standard

The UI must feel like a polished consumer product, not a developer demo.

## 5.1 First screen

The landing page should answer in under five seconds:

- What is this?
- Is it safe to use?
- What can it do?
- What should I click first?

Primary actions:

**Tell My Problem** | **Understand My Rights** | **Make a Document**

Secondary:

**Check My Case** | **Upload a Notice** | **Find Legal Help**

## 5.2 Guided conversation, not blank chat

Default flow:

```text
Choose language
→ speak/type problem
→ AI summarizes what it understood
→ user confirms
→ 3–5 targeted questions
→ identify domain + urgency
→ rights + options
→ document / escalation
```

## 5.3 Trust UX

Always display a compact but clear legal-information disclaimer.

Every important legal claim should support “Why am I seeing this?” and “Source”.

Show:

- source;
- relevant section;
- verification/freshness status;
- what the user should verify;
- escalation path.

## 5.4 Low-literacy and mobile design

The agent must optimize for lower-end Android devices and intermittent networks:

- large tap targets;
- short screens;
- progressive disclosure;
- minimal animation;
- lightweight assets;
- voice first where beneficial;
- offline shell for core UI;
- retry without losing user state;
- resumable sessions.

The original blueprint explicitly calls for mobile-first accessibility, Hindi + English, voice input and WCAG AA. fileciteturn0file0L67-L68

## 5.5 Accessibility

Target WCAG 2.1 AA at minimum and perform real automated + manual checks:

- keyboard navigation;
- visible focus;
- screen-reader labels;
- form errors announced;
- streamed content announced appropriately;
- contrast;
- reduced motion;
- semantic headings;
- touch target size;
- language metadata for Hindi/English.

---

# 6. Safety & Legal Boundaries

The product must explicitly distinguish:

### Allowed

- legal information;
- source-grounded explanations;
- procedural guidance at a general level;
- document drafting from user-provided facts;
- source navigation;
- public-resource discovery;
- deadline extraction with uncertainty indicators.

### Escalate / do not overclaim

- active criminal matters requiring urgent counsel;
- imminent violence or safety risks;
- matters with complex procedural posture;
- advice dependent on documents not yet verified;
- individualized legal strategy where reliable source grounding is insufficient;
- requests to impersonate a lawyer or court;
- forged evidence or deceptive filings;
- fabricated citations.

The output policy should support structured refusal/escalation instead of a generic “I cannot help.”

---

# 7. Phase-by-Phase Implementation Plan

## PHASE 0 — Product Contract, Scope & Legal-Safety Boundaries

### Objective
Freeze the product contract before implementation.

### Agent tasks

1. Read the project brief and this document completely.
2. Create `/docs/PRD.md`.
3. Define the initial primary persona and 3–5 high-value problem journeys.
4. Define in-scope vs out-of-scope legal domains.
5. Define what constitutes an answer, escalation, refusal and “needs verification.”
6. Define supported languages for MVP: English + Hindi minimum.
7. Create the first domain taxonomy.
8. Create a risk taxonomy: low / medium / high / emergency.
9. Define the source hierarchy and data-freshness policy.
10. Define a measurable North Star outcome and supporting metrics.
11. Create `/docs/SOURCE_POLICY.md`.
12. Create `/docs/SAFETY_POLICY.md`.

### Deliverables

- PRD
- persona
- user journeys
- scope matrix
- safety policy
- source policy
- initial success metrics

### Gate
No code feature work beyond repository scaffolding until the scope and safety policies exist.

### Tests/checks
- document consistency review;
- all MVP features map to a user journey;
- all high-risk journeys have escalation rules.

### Exit criteria
Agent writes `/docs/phases/PHASE_00_REPORT.md` containing:

- what was completed;
- decisions made;
- open risks;
- acceptance-test results;
- files changed.

---

## PHASE 1 — Repository, CI/CD & Developer Experience

### Objective
Create the production-quality skeleton before business logic.

### Agent tasks

1. Create monorepo.
2. Create frontend and backend packages.
3. Add `.env.example` only; never add secrets.
4. Add formatting, linting, typing and test configuration.
5. Add GitHub Actions.
6. Add gitleaks or equivalent secret scanning.
7. Add pre-commit hooks if practical.
8. Add Docker development environment.
9. Add health endpoint.
10. Add structured logging.
11. Add dependency-injection skeleton.
12. Add versioned API namespace `/api/v1`.
13. Add `SECURITY.md`.
14. Add `LICENSE`.
15. Add minimal README with setup instructions.

### Required CI order

```text
install
→ lint
→ type-check
→ unit tests
→ integration tests
→ frontend build
→ accessibility smoke test
→ secret scan
```

### Gate
CI must be green before Phase 2.

---

## PHASE 2 — Database, Domain Model & Persistence

### Objective
Create the durable data foundation.

### Agent tasks

Define typed models for:

- user session;
- intake state;
- domain classification;
- source;
- source snapshot;
- legal document;
- legal section;
- citation;
- retrieval chunk;
- uploaded document;
- OCR result;
- extracted deadline;
- generated document;
- escalation resource;
- evaluation result.

Implement migrations and repositories.

### Privacy requirements

Use data minimization:

- no unnecessary user accounts in MVP;
- anonymous session IDs where possible;
- short-lived storage for uploaded documents;
- explicit deletion lifecycle;
- no full raw user conversations in production logs.

### Gate
Migration tests, repository tests and rollback verification must pass.

---

## PHASE 3 — Source Registry & Live Data Connectors

### Objective
Make the system capable of acquiring current information correctly.

### Agent tasks

1. Implement source registry.
2. Implement source adapter interface.
3. Add official legislation ingestion/refresh path.
4. Add official judiciary/eCourts navigation or permitted integration path.
5. Add NALSA/SLSA/DLSA directory synchronization path.
6. Add Tele-Law resource synchronization path where technically and legally permitted.
7. Add source health checks.
8. Store source timestamps and content hashes.
9. Add retry/backoff.
10. Add circuit breakers.
11. Add source failure states.
12. Add change detection.
13. Store historical source versions.

### Important
Do not scrape a website merely because a browser can display it. The agent must document authorization/technical limitations and choose a compliant integration strategy.

### Gate
Run source adapter tests using mocked upstream responses and at least one controlled live smoke test per source family.

### Exit condition
The system can answer “where did this fact come from?” for every source-derived record.

---

## PHASE 4 — Legal Corpus Ingestion & Citation-First RAG

### Objective
Build the legal reasoning substrate.

### Agent tasks

1. Implement legal-text-aware parsing.
2. Chunk by Act / Chapter / Section / subsection rather than arbitrary text length where possible.
3. Store section metadata.
4. Embed and index corpus.
5. Implement hybrid retrieval.
6. Implement jurisdiction filtering.
7. Implement effective-date filtering.
8. Implement top-k evidence selection.
9. Implement citation verification.
10. Implement claim-to-evidence checks.
11. Implement stale-source handling.
12. Implement current-law replacement/mapping data where necessary.
13. Build corpus refresh tooling.

### RAG response contract

The model must produce structured output:

```json
{
  "summary": "...",
  "rights": [],
  "next_steps": [],
  "deadlines": [],
  "citations": [],
  "uncertainties": [],
  "escalation_needed": false
}
```

Reject output if citation validation fails for a required legal claim.

### Gate
The initial evaluation set must contain adversarial and outdated-law questions, not only easy queries.

---

## PHASE 5 — Guided Intake Engine

### Objective
Implement “Samjho Mera Problem”.

### Agent tasks

1. Build domain classifier.
2. Build intake state machine.
3. Generate 3–5 high-value questions.
4. Avoid asking questions already answered by the user.
5. Track confidence.
6. Detect urgent/high-risk cases.
7. Support English/Hindi.
8. Normalize colloquial language without changing factual meaning.
9. Permit correction after each AI summary.
10. Store only the minimum state needed.
11. Add voice input adapter.
12. Add fallback text input.

### UX requirement
After user input, show:

> “Here’s what I understood…”

with edit/confirm controls before the system acts on the facts.

### Gate
Tests must cover:

- incomplete input;
- contradictory input;
- Hindi input;
- mixed Hindi-English;
- speech transcription errors;
- ambiguous intent;
- urgent/high-risk case.

---

## PHASE 6 — Rights Explanation & Action Timeline

### Objective
Implement “Mere Adhikaar”.

### Agent tasks

1. Retrieve evidence.
2. Explain at Grade 6–8 reading complexity where appropriate.
3. Present citations inline.
4. Distinguish rights from practical suggestions.
5. Add “what to do next” timeline.
6. Compute deterministic date windows where enough information exists.
7. Show uncertainty where dates depend on missing facts.
8. Provide source/freshness information.
9. Add translation layer that preserves legal meaning.
10. Add escalation recommendations.

### Never do
- invent a deadline;
- infer an exact legal entitlement from incomplete facts without qualification;
- cite a section not verified in the source registry;
- use outdated law without an explicit historical-context label.

### Gate
Run citation validation and compare every generated claim against evidence.

---

## PHASE 7 — OCR, Deadline Guardian & Document Understanding

### Objective
Allow users to upload a notice/order/document and understand it.

### Agent tasks

1. Validate file type and size.
2. Malware/content safety screening.
3. Extract text.
4. OCR when necessary.
5. Detect document language.
6. Identify document type.
7. Extract important dates.
8. Extract parties and non-sensitive metadata needed for explanation.
9. Build a plain-language summary.
10. Identify possible deadlines.
11. Show exact source text/snippet supporting each extracted date.
12. Mark confidence.
13. Allow the user to correct extracted dates.
14. Add optional calendar export only after the extraction is confirmed.

### Deadline object

```text
label
value
source_text
page_number
confidence
assumptions
requires_verification
```

### Gate
Use synthetic documents with known ground truth. Do not rely on LLM self-confidence alone.

---

## PHASE 8 — Controlled Document Generator

### Objective
Implement “Mera Document”.

### Initial MVP documents

At least three, selected after user/problem validation. Recommended starting set:

1. RTI application
2. Consumer complaint
3. Legal notice / response template

Additional templates can include affidavit or rent-dispute reply where the legal review supports them.

### Architecture

```text
user facts
→ structured schema
→ deterministic validation
→ LLM slot filling
→ template rendering
→ legal/source validation
→ PDF generation
→ visual validation
→ download
```

Never ask the LLM to generate an entire uncontrolled legal PDF from scratch.

### Document safety

- mark missing fields;
- never invent facts;
- preserve user-provided names exactly unless corrected by user;
- flag assumptions;
- include appropriate non-lawyer disclaimer;
- retain source/version metadata internally.

### Gate
Golden-file tests + PDF parsing + visual smoke test + field completeness tests.

---

## PHASE 9 — Human Escalation & Resource Navigator

### Objective
Implement safe handoff to human assistance.

### Agent tasks

1. Detect escalation conditions.
2. Determine jurisdiction from user-provided location.
3. Retrieve official legal-aid resources.
4. Show district/state authority.
5. Show source timestamp.
6. Provide click-to-call/tap-to-open where appropriate.
7. Provide Tele-Law/human-help navigation.
8. Explain why escalation is recommended.
9. Never imply that an AI response constitutes representation by a lawyer.

### Gate
Test districts across multiple states, missing data, stale directory data and upstream outage scenarios.

---

## PHASE 10 — Security, Privacy & Abuse Resistance

### Objective
Harden the system before public exposure.

### Agent tasks

Implement:

- request size limits;
- upload limits;
- MIME/content validation;
- rate limiting;
- bot/abuse mitigation appropriate to the deployment;
- CORS restrictions;
- security headers;
- secure cookies where used;
- CSRF strategy if applicable;
- prompt-injection defense;
- output validation;
- SSRF protection;
- URL allowlists for remote retrieval;
- PII redaction from logs;
- secret management;
- dependency scanning;
- deletion/retention policy;
- access control for admin operations;
- audit events for privileged actions.

### Threat model

Create `/docs/THREAT_MODEL.md` covering at least:

- prompt injection;
- malicious PDFs;
- OCR abuse;
- data exfiltration;
- prompt leakage;
- API key leakage;
- denial of service;
- source poisoning;
- citation spoofing;
- user impersonation;
- unsafe document generation.

### Gate
Security checklist + automated secret scan + dependency scan + basic penetration tests against the local deployment.

---

## PHASE 11 — Evaluation Framework & 50+ Query Benchmark

### Objective
Turn correctness into a measurable engineering property.

### Build `/evals`

At minimum include categories for:

- current-law questions;
- outdated-law traps;
- citation accuracy;
- ambiguity;
- Hindi;
- Hinglish;
- colloquial speech transcripts;
- deadline extraction;
- document field completion;
- escalation decisions;
- refusal/safety cases;
- prompt injection;
- hallucination traps.

The original challenge plan calls for a 50-query set and published results, including a target of zero fabricated citations. fileciteturn0file0L64-L68

### Metrics

Track at least:

- citation precision;
- citation recall;
- unsupported-claim rate;
- outdated-law error rate;
- domain classification accuracy;
- deadline extraction exact/partial accuracy;
- document field accuracy;
- escalation precision/recall;
- latency p50/p95;
- cost per successful request;
- cache hit rate.

### Important
A passing eval is a release condition, not a presentation-only metric.

---

## PHASE 12 — Full UX Polish & Accessibility Certification

### Objective
Transform the working MVP into a public-quality product.

### Agent tasks

1. Perform complete mobile audit.
2. Test on slow network.
3. Test low-end viewport sizes.
4. Test screen readers.
5. Test keyboard-only navigation.
6. Improve loading/streaming states.
7. Add skeletons rather than blank screens.
8. Preserve state on navigation/reload where safe.
9. Add error recovery.
10. Add friendly empty states.
11. Add confirmation before destructive actions.
12. Improve Hindi typography and layout.
13. Add PWA installation.
14. Optimize bundle size and images.
15. Run Lighthouse and accessibility tools.

### UX acceptance standard
A first-time user should be able to complete the principal demo journey without developer assistance.

---

## PHASE 13 — Performance, Cost & Reliability Engineering

### Objective
Make the platform fast and economically sustainable.

### Agent tasks

Implement:

- model routing;
- semantic/response caching where safe;
- bounded retrieval;
- streaming responses;
- connection pooling;
- concurrency controls;
- timeout budgets;
- retry policy;
- graceful degradation;
- source circuit breakers;
- file-processing queue/limits.

### Establish budgets

Define and measure:

```text
page load target
first-token target
complete-answer target
PDF-generation target
OCR target
p50 / p95 latency
cost/query
cost/session
```

Do not publish estimated cost as fact until measured against actual usage.

The original blueprint explicitly asks for latency, cost-per-query and cache-hit evidence in the README. fileciteturn0file0L64-L67

### Gate
Run a repeatable load test and publish benchmark methodology.

---

## PHASE 14 — Production Readiness & Observability

### Objective
Make failures diagnosable before public release.

### Agent tasks

Add:

- health checks;
- readiness checks;
- source health dashboard/logs;
- model/provider health;
- error-rate monitoring;
- latency metrics;
- queue/file-processing metrics;
- structured correlation IDs;
- privacy-safe error logs;
- uptime checks;
- incident runbook.

Create `/docs/OPERATIONS.md` with:

- common failures;
- provider outage response;
- source outage response;
- rollback procedure;
- data-deletion procedure;
- secret rotation procedure.

---

## PHASE 15 — Final Validation, Demo & Release

### Objective
Prepare the public release and judging/demo package.

### Agent tasks

1. Run all backend tests.
2. Run all frontend tests.
3. Run all E2E tests.
4. Run accessibility tests.
5. Run security scans.
6. Run 50+ legal evals.
7. Run source-integrity checks.
8. Run performance benchmark.
9. Verify repo size < 10 MB.
10. Verify no secrets.
11. Verify no model weights/datasets accidentally committed.
12. Verify README setup from a clean environment.
13. Produce architecture diagram.
14. Record demo journey.
15. Produce cost/latency table.
16. Produce known-limitations document.
17. Tag release.

### Final demo journey

Use one coherent story from beginning to end:

```text
citizen problem
→ vernacular voice/text
→ confirmation of facts
→ classification
→ current-law retrieval
→ rights explanation + citations
→ deadline/action timeline
→ document generation
→ document validation
→ legal-aid escalation when appropriate
```

---

# 8. Mandatory Agent Workflow After Every Phase

The agent must perform this exact process after each phase:

```text
1. Implement phase
2. Run formatter/linter
3. Run type checks
4. Run unit tests
5. Run integration tests relevant to phase
6. Run security checks relevant to phase
7. Run build
8. Run acceptance checks
9. Inspect generated UI/artifacts where applicable
10. Fix failures
11. Re-run complete applicable suite
12. Record results in PHASE_XX_REPORT.md
13. Only then begin next phase
```

### No “tests probably pass”

The agent must include actual command output summaries in every phase report, such as:

```text
pytest: PASS — 143 passed
ruff: PASS
mypy: PASS
frontend build: PASS
Playwright: PASS — 18 passed
secret scan: PASS
accessibility smoke: PASS
```

If something cannot be executed because a key/service is not yet provided, the report must explicitly state:

```text
BLOCKED — missing dependency/key
What is required:
Why it is required:
Temporary mock used:
What remains to be re-run:
```

Never mark the phase as fully complete when a release-critical validation has not actually run.

---

# 9. “Stop the Line” Conditions

The agent must stop the current phase and fix the problem before continuing if any of these occur:

- fabricated citation;
- source conflict not resolved;
- outdated law presented as current;
- generated document invents user facts;
- security secret committed;
- raw PII appears in logs;
- tests fail;
- type checking fails;
- build fails;
- critical accessibility failure;
- unsafe escalation decision;
- an upstream source is silently substituted with an unverified source;
- a feature depends on prohibited or unauthorized scraping;
- latency/cost exceeds the documented product budget without an explicit decision record.

---

# 10. Required Repository Layout

Maintain a structure based on the existing project plan, with room for the source layer and phase reports:

```text
nyayamitra/
├── .github/workflows/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── models/
│   │   ├── sources/
│   │   ├── middleware/
│   │   ├── core/
│   │   └── utils/
│   ├── scripts/
│   └── tests/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   └── public/
├── prompts/
├── evals/
├── docs/
│   ├── phases/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── ARCHITECTURE_DECISIONS.md
│   ├── COMPLIANCE.md
│   ├── SOURCE_POLICY.md
│   ├── SAFETY_POLICY.md
│   ├── THREAT_MODEL.md
│   ├── COST_PERFORMANCE.md
│   ├── USER_VALIDATION.md
│   └── OPERATIONS.md
├── tests/
├── .env.example
├── .gitleaks.toml
├── SECURITY.md
├── LICENSE
├── README.md
└── IMPLEMENTATION.md
```

The existing project blueprint already separates routers, services, repositories, prompts, tests, docs, and evals; this implementation adds source adapters and phase reports because current-data correctness is central to the product. fileciteturn0file1L21-L68

---

# 11. Prompt Engineering Standard

All important prompts must be versioned.

Recommended format:

```text
prompts/
├── classifier/
│   ├── v1.txt
│   └── v2.txt
├── intake/
├── rights/
├── document/
├── ocr/
├── translation/
├── escalation/
└── safety/
```

Each prompt must document:

- purpose;
- inputs;
- required output schema;
- constraints;
- failure conditions;
- examples;
- version;
- evaluation set.

Prompt changes must be evaluated before release.

---

# 12. Dynamic Data Refresh Strategy

Do not make the application dependent on manual database editing.

Implement:

```text
scheduler / controlled trigger
        ↓
source adapter
        ↓
fetch
        ↓
normalize
        ↓
validate
        ↓
hash/diff
        ↓
version snapshot
        ↓
re-index if changed
        ↓
health + metrics
```

For every source define a refresh cadence based on the actual source volatility.

Examples:

- legislation / notifications: frequent change detection;
- legal-aid directory: scheduled refresh;
- case status: query-time or permitted live lookup;
- cached explanatory content: safe TTL + source invalidation.

The agent must not invent refresh intervals before inspecting the source behavior.

---

# 13. Compliance Mapping

Create `/docs/COMPLIANCE.md` with one row per challenge requirement.

Minimum fields:

```text
Requirement
Implementation
Source file(s)
Endpoint/component
Test(s)
Evidence
Status
```

The existing requirements explicitly include guided intake, vernacular voice, citation-grounded rights, 3+ PDF generators, OCR + deadline extraction, disclaimer/escalation, mobile/WCAG, and security controls. fileciteturn0file0L61-L68

---

# 14. Required Final README

The README must contain:

1. product overview;
2. problem + persona;
3. architecture diagram;
4. feature walkthrough;
5. supported domains;
6. current-law/source strategy;
7. setup in five minutes;
8. environment variables;
9. local development;
10. database setup;
11. corpus ingestion;
12. evaluation commands;
13. testing commands;
14. deployment;
15. security posture;
16. accessibility statement;
17. cost/latency table;
18. known limitations;
19. demo video;
20. screenshots/GIFs where useful.

---

# 15. Suggested User Journeys for the MVP

## Journey A — Rent / Eviction Assistance

```text
Hindi voice
→ tenant explains issue
→ facts confirmed
→ relevant domain detected
→ current rights retrieved
→ notice/deadline explained
→ draft response / notice generated
→ human-help option offered when necessary
```

## Journey B — Consumer Problem

```text
User explains defective product/service
→ classifier
→ missing facts requested
→ consumer-rights explanation
→ evidence checklist
→ complaint generated
→ next procedural step
```

## Journey C — RTI

```text
User says what information they need
→ identify public authority/topic
→ explain RTI process
→ gather applicant details
→ generate structured RTI application
→ produce printable PDF
```

## Journey D — Uploaded Notice

```text
Photo/PDF upload
→ OCR
→ document type detection
→ plain-language summary
→ dates extracted
→ deadline confidence + source excerpt
→ action checklist
→ escalation if urgent/complex
```

---

# 16. Suggested Additional Features — Only After Core Reliability

These are intentionally **post-MVP** unless user testing proves they are critical:

### A. “Ask about this paragraph”
User taps a sentence in an uploaded document and asks what it means.

### B. Source comparison
Show “current provision vs older provision” when legally appropriate.

### C. Court-case navigation helper
Help users understand what an official eCourts result means without pretending to be the court.

### D. Calendar/reminder integration
Only after deadline extraction accuracy is strong.

### E. Progressive language expansion
Tamil, Bengali, Marathi, Telugu and other languages after Hindi/English quality is proven.

### F. Human-reviewed knowledge workflows
Admin tooling for approved legal experts/partners to review source changes and safety policies.

---

# 17. Features Explicitly Deferred Unless a Later Phase Justifies Them

Do not allow scope creep into:

- lawyer marketplace;
- unrestricted legal chatbot mode;
- court e-filing automation;
- automated filing on behalf of users;
- direct legal representation claims;
- video consultation infrastructure;
- large case-law search experience for general users;
- autonomous legal strategy engine;
- opaque “AI confidence scores” presented as legal certainty.

The original product synthesis also recommends avoiding e-filing, lawyer marketplace, video consultation, and raw case-law overload in the MVP. fileciteturn0file1L221-L225

---

# 18. Completion Definition

NyayaMitra is considered **complete for public MVP release** only when all of the following are true:

- all phases 0–15 are completed;
- all phase reports exist;
- CI is green;
- production build succeeds;
- 50+ legal evaluations run successfully;
- no fabricated citations in the release benchmark;
- current-law/outdated-law trap set passes agreed threshold;
- document generation tests pass;
- OCR/deadline tests pass;
- security scan passes;
- accessibility audit passes;
- public setup works from a clean environment;
- dynamic source refresh works for the supported source families;
- source outages degrade safely;
- no raw secrets are present;
- no prohibited data is logged;
- repo is below the submission-size limit;
- README is complete;
- demo flow works end-to-end;
- known limitations are documented.

---

# 19. Agent Handoff Instructions

The development agent must follow these instructions literally:

### Before coding
Read:

```text
IMPLEMENTATION.md
/docs/PRD.md
/docs/SOURCE_POLICY.md
/docs/SAFETY_POLICY.md
```

Then inspect the current repository and identify the current phase.

### During coding
- make small, reviewable commits;
- avoid unrelated refactors;
- use typed interfaces;
- keep AI provider calls abstracted;
- keep source adapters isolated;
- write tests alongside features;
- update documentation when behavior changes;
- never add a secret to source control;
- never silently disable a failing test.

### At phase completion
Produce:

```text
/docs/phases/PHASE_<NN>_REPORT.md
```

The report must contain:

```text
Phase
Objective
Implemented
Files changed
Commands executed
Test results
Security results
Accessibility results (if relevant)
Performance observations
Known limitations
Blocked items
Decision records
Ready for next phase: YES/NO
```

### Proceed rule

Only proceed when:

```text
all required checks = PASS
AND
no critical blocker exists
AND
phase report = COMPLETE
```

---

# 20. Final Product Principle

The winning product is not the one with the most AI features.

It is the one that makes a citizen feel:

> **“It understood my problem, showed me where the information came from, told me what I can do next, helped me create something useful, and knew when I needed a real human.”**

Build for that outcome above everything else.
