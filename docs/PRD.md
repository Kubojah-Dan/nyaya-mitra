# NyayaMitra — Product Requirements Document (PRD)

**Document Version:** 1.0.0  
**Phase:** 0 — Product Contract, Scope & Legal-Safety Boundaries  
**Status:** Approved Baseline  
**Product Theme:** AI for Legal Assistance & Access  
**Target Market:** India (Urban, Semi-urban, and Rural Citizens)  

---

## 1. Executive Summary & Mission

**NyayaMitra** ("Friend of Justice") is a citizen-first, Generative-AI-powered legal assistance and access platform designed specifically for people in India who struggle to understand legal problems, their constitutional and statutory rights, procedural steps, legal documents, court deadlines, and available legal-aid resources.

NyayaMitra is **not** a generic conversational chatbot, a lawyer replacement, or an automated court filing agent. Instead, it serves as a **guided, source-grounded legal triage, rights explanation, document generation, and human escalation assistant**.

### Core Value Proposition
1. **Intake in Plain Vernacular**: Transforms spoken or typed natural language (Hindi, English, and colloquial Hinglish) into structured factual summaries.
2. **Current-Law Grounding**: Answers grounded exclusively in verified Tier-1 Indian statutes and official procedures—specifically incorporating the **Bharatiya Nyaya Sanhita (BNS)**, **Bharatiya Nagarik Suraksha Sanhita (BNSS)**, and **Bharatiya Sakshya Adhiniyam (BSA)**, while explicitly flagging historical law (IPC, CrPC, IEA).
3. **Traceable Citations**: Every legal statement links directly to specific Acts, sections, and official government gazette/India Code snapshots. Zero fabricated citations.
4. **Actionable Plain-Language Guidance**: Rights explained at a Grade 6–8 reading level with concrete timelines and checklists.
5. **Controlled Document Generation**: Pre-formatted, deterministic legal templates (RTI applications, Consumer Complaints, Tenant dispute notices) filled safely via verified slots, not uncontrolled LLM hallucinations.
6. **Seamless Human Escalation**: Built-in escalation to official legal-aid resources (NALSA, SLSA, DLSA, and Tele-Law) whenever a situation is high-risk, ambiguous, or requires licensed representation.

---

## 2. User Personas

### Persona 1: Ramesh Kumar (Tenant / Gig Worker)
- **Profile:** 34-year-old delivery rider residing in rented accommodation in East Delhi.
- **Language Preference:** Spoken Hindi / Casual Hinglish. Smartphone literate, low formal legal literacy.
- **Problem:** Landlord sent an informal WhatsApp message demanding immediate eviction within 48 hours and refusing to return the security deposit.
- **Need:** Understand tenancy rights, learn if 48-hour eviction is legal under the Delhi Rent Control Act / Model Tenancy framework, determine immediate steps, and generate a formal reply letter.

### Persona 2: Sunita Devi (Consumer / Homemaker)
- **Profile:** 42-year-old homemaker from Jaipur, Rajasthan.
- **Language Preference:** Hindi (text and voice).
- **Problem:** Purchased an electric water heater online that arrived damaged. E-commerce seller refused return and customer support stopped answering.
- **Need:** Understand consumer rights under the Consumer Protection Act 2019, procedural timeline to send a grievance to the National Consumer Helpline (NCH), and generate a formal notice to the seller.

### Persona 3: Amit Patel (Citizen / RTI Applicant)
- **Profile:** 28-year-old community worker from Ahmedabad, Gujarat.
- **Language Preference:** English / Gujarati (MVP: English/Hindi).
- **Problem:** Local municipal road was repaired poorly and degraded within weeks; wants expenditure details and contractor work orders.
- **Need:** Understand how to file an RTI under RTI Act 2005, identify Public Information Officer (PIO) requirements, fee structure, 30-day statutory response deadline, and generate a compliant RTI application.

### Persona 4: Parvati Murmu (Individual facing Legal Notice)
- **Profile:** 50-year-old small shop owner from Ranchi, Jharkhand.
- **Language Preference:** Voice Hindi / Low-bandwidth Android user.
- **Problem:** Received a formal stamped paper from an advocate with confusing legal jargon and a threatening 15-day court date.
- **Need:** Upload notice photo/PDF, have dates and demands extracted into plain Hindi, assess genuine urgency, and obtain contact details for the District Legal Services Authority (DLSA) for free legal aid.

---

## 3. High-Value User Problem Journeys

### Journey A: Tenancy & Eviction Defense ("Samjho Mera Problem" → "Mere Adhikaar" → "Mera Document")
1. **Intake:** User describes the situation using voice in Hindi: *"Mera landlord bol raha hai kal ghar khali karo warna saaman bahar phek dega."*
2. **Fact Confirmation:** System reflects back: *"1) You are a tenant. 2) The landlord gave verbal 24-hour notice to vacate. 3) Security deposit is held. Did we capture this accurately?"* User confirms or corrects.
3. **Rights Explanation:** System explains that illegal dispossession without due process of law is unlawful, cites applicable statutory provisions and rent control principles, highlights that reasonable notice (typically 15–30 days) is mandatory.
4. **Action Timeline:** Step 1: Document all payments. Step 2: Send formal written reply. Step 3: Approach Rent Controller or police if threat of force is made.
5. **Document Generation:** Generates a structured "Reply to Unlawful Eviction Notice" with verified user facts inserted into validated slots.
6. **Escalation:** Provides DLSA East Delhi contact details if the landlord attempts physical eviction.

### Journey B: Defective Goods & Consumer Redressal
1. **Intake:** User types defective product issue and lack of refund response.
2. **Classification:** Categorized under **Consumer Protection Act, 2019** (Deficiency of Service / Product Defect).
3. **Guided Questions:** System asks: Date of purchase? Amount paid? Did you notify seller in writing?
4. **Explanation:** Outlines rights under Section 2(47) & Section 35 of CPA 2019, statutory timeline (notice period 15 days, limitation period 2 years).
5. **Document:** Produces a standardized Consumer Notice / NCH complaint draft.

### Journey C: Right to Information (RTI) Drafting
1. **Intake:** User specifies the public matter/authority from which information is sought.
2. **Clarification:** Identifies whether Central or State public authority, clarifies specific records requested (tender copies, inspection reports).
3. **Explanation:** Explains Section 6(1) of RTI Act 2005, nominal fee (₹10 for Central), 30-day statutory response requirement (48 hours if life and liberty).
4. **Document:** Outputs a structured, printable Form-A RTI Application with mandatory declarations and fee submission instructions.

### Journey D: Notice / Order Understanding ("Deadline Guardian")
1. **Intake:** User uploads PDF or smartphone camera picture of a legal communication.
2. **Processing:** Safe OCR + text extraction, language detection, document classification (Legal Notice, Summons, Demand Letter).
3. **Summary:** 3-bullet plain-language breakdown: Who sent it, What do they want, What is the deadline.
4. **Deadline Extraction:** Extracts "Reply within 15 days from receipt" with confidence rating and source citation snippet.
5. **Escalation:** If marked as High-Risk (e.g. Criminal summons under BNSS), immediately renders NALSA / DLSA free legal aid contact card with click-to-call.

---

## 4. In-Scope vs. Out-of-Scope Legal Domains

### In-Scope Domains (MVP)
| Domain | Key Statutes / References | Supported Assistance |
| :--- | :--- | :--- |
| **Consumer Protection** | Consumer Protection Act, 2019; E-Commerce Rules 2020 | Rights explanation, National Consumer Helpline steps, formal consumer complaint drafting |
| **Tenancy & Housing** | Model Tenancy Act principles, State Rent Control Acts (Delhi, Maharashtra, Karnataka) | Eviction procedure, notice periods, security deposit rights, tenant reply drafting |
| **Right to Information** | Right to Information Act, 2005 (Central & State Rules) | Public authority guidance, fee rules, 30-day deadline, RTI application generation |
| **Basic Criminal Awareness** | Bharatiya Nyaya Sanhita (BNS 2023), Bharatiya Nagarik Suraksha Sanhita (BNSS 2023) | FIR registration rights (Zero FIR, e-FIR), arrest rights (Section 35-50 BNSS), legal aid entitlements |
| **Labor & Basic Employment** | Payment of Wages Act, Industrial Disputes Act, Code on Wages | Unpaid wages procedure, basic notice period disputes, labor commissioner grievance format |
| **Legal Aid & Access** | Legal Services Authorities Act, 1987; NALSA guidelines | Eligibility for free legal aid (Section 12), DLSA/SLSA/Tele-Law navigation |

### Explicitly Out-of-Scope Domains
1. **Active Criminal Defense Strategy**: Substantive bail arguments, trial tactics, evidence suppression filings.
2. **Corporate & Commercial M&A / Complex Tax**: Tax litigation, insolvency proceedings (IBC), corporate restructuring.
3. **Complex Family & Custody Battles**: Contested divorces, adoption disputes, high-conflict child custody.
4. **Constitutional Writs & Direct Supreme Court Filings**: Article 32/226 petition drafting.
5. **Automated Filing / Court Representation**: Impersonating advocates, filing directly into court portals, or claiming formal legal representation.

---

## 5. Interaction Modes: Answer, Escalation, Refusal & Verification

| Response Type | Trigger Condition | System Behavior |
| :--- | :--- | :--- |
| **Answer** | In-scope domain, unambiguous facts, clear statutory basis in Tier-1 verified source. | Plain-language explanation (Grade 6–8), explicit citations, action checklist, document option, standard non-lawyer disclaimer. |
| **Needs Verification** | Incomplete factual input, ambiguous timeline, state-specific local rules unverified in database. | System marks claim with `[Needs Verification]`, asks targeted follow-up question, or instructs user on specific factual confirmation required. |
| **Escalation** | High risk, imminent legal deadline (< 48 hrs), complex procedural posture, or user requests human lawyer. | Clear explanation of why AI is insufficient, display of relevant NALSA/SLSA/DLSA office, Tele-Law link, and helplines. |
| **Refusal** | Out-of-scope query, request for unlawful acts, document forgery, adversarial prompt injection, or demand for representation. | Polite, firm, structured refusal explaining boundaries and guiding to lawful authorized resources. |

---

## 6. Risk Taxonomy

| Risk Tier | Definition | Example Scenarios | Mandatory System Action |
| :--- | :--- | :--- | :--- |
| **Emergency (Tier 4)** | Imminent threat of bodily harm, domestic violence, human trafficking, immediate custodial torture. | *"My spouse is attacking me"*, *"Police picked up my brother without warrant and are beating him."* | Immediate emergency banner: Emergency 112, Women Helpline 181, Childline 1098. No standard RAG delay; immediate emergency referral. |
| **High Risk (Tier 3)** | Imminent court appearance date (< 48 hours), arrest warrant, eviction today, child custody confiscation. | Notice with 24-hour compliance deadline, non-bailable warrant notification. | Prominent human escalation banner (DLSA / Tele-Law / High Court Legal Services Committee) + basic rights summary. |
| **Medium Risk (Tier 2)** | Formal notice received with 15–30 day deadline, consumer dispute, unpaid salary, RTI refusal. | 15-day cheque bounce notice, delayed delivery of online purchase. | Standard intake → rights explanation → timeline → template drafting → optional legal aid directory. |
| **Low Risk (Tier 1)** | General procedural awareness, eligibility for government legal schemes, standard rights inquiries. | *"How to file an RTI online?"*, *"What is zero FIR?"* | Direct educational answer, citations, checklist. |

---

## 7. Supported Languages & Vernacular Interaction

- **Phase 0 / MVP Target:** English & Hindi (Devanagari and Romanized Hinglish).
- **Audio & Speech:** Browser-native Web Speech API for voice input with automatic fallback to text input.
- **Language Switcher:** Persistent, accessible header toggle (English / हिंदी) across all screens.
- **Post-MVP Language Roadmap:** Bengali, Marathi, Tamil, Telugu, Kannada, Gujarati.

---

## 8. Measurable North Star Outcome & Key Performance Indicators

### North Star Metric
> **Zero Fabricated Citations**: 100% of generated statutory citations and legal sections must validate against verified Tier-1 indexed Indian legal sources in benchmark evaluations.

### Supporting KPIs & Target Service Levels
1. **Readability Target:** Grade 6–8 reading complexity (Flesch-Kincaid / Hindi readability equivalent) for rights explanations.
2. **First-Token Latency (p50):** < 1.5 seconds on broadband, < 3.0 seconds on mobile 3G/4G network simulations.
3. **Total Response Latency (p50):** < 4.0 seconds for complete rights synthesis.
4. **Document Generation Latency:** < 5.0 seconds from confirmed slots to PDF download.
5. **Mobile Accessibility:** 100% WCAG 2.1 AA compliance; lighthouse accessibility score ≥ 95.
6. **Mobile Bundle & Performance:** Core PWA bundle < 200 KB gzip; full repository footprint strictly < 10 MB.
7. **Hallucination Rate on Legal Evaluations:** 0% on statutory citations, < 3% unsupported factual claims on the 50-query test suite.
