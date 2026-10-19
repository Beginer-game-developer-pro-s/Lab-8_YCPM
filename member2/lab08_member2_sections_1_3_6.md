# LAB 08 REPORT CONTRIBUTION – MEMBER 2
**Course:** CSE703095 – Software Requirements  
**Case Study Project:** MedBook – Online Medical Appointment Booking System  
**Prepared by:** Tran Doan Viet Anh (Member 2 – Safety & Requirements Analyst)  
**Deliverables Covered:** Section 1 (Hazard → NFR Mitigation Cross-check), Section 3 (New Scenario Analysis), Section 6 (Limitations & Future Work)  
**Date:** 2026-10-14  

**Evidence sources.** `datasets/hazards.csv`, `datasets/nonfunctional_requirements.csv`, `datasets/functional_requirements.csv`, `datasets/test_cases.csv`, `code/simulate_booking.py`, `code/test_safety_scenarios.py`. Machine-readable companion table: `member2/hazard_nfr_crosscheck.csv`.

---

## 1 Hazard → NFR Mitigation Cross-check (Part 1)

Safety requirements are logically consistent only when each identified hazard is mitigated by a **quantified** non-functional requirement whose measurement criterion actually addresses that hazard. A functional requirement such as FR-008 (“the system shall warn”) specifies *that* a behaviour exists; it does not bound *how often the behaviour may silently fail*. The table below therefore traces each hazard to the FR/NFR identifiers currently recorded in `hazards.csv`, then judges whether those NFRs are sufficient.

### 1.1 Cross-check table

| Hazard ID | Hazard (summary) | Overall risk | Traced FR | Traced NFR | Does the NFR actually mitigate this hazard? | Current mitigation in the safety case | Compliance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **HZ-001** | Drug-interaction / allergy warning fails to display because of a system fault | High (Catastrophic × Low) | FR-008 | **NFR-007** | **No.** NFR-007 is a *booking-conflict latency* requirement (≤ 1 s when a doctor is double-booked). It has no false-negative bound for clinical alerts. | Mandatory manual double-check + warning logging | **Insufficient** |
| **HZ-002** | Undetected appointment conflict (same doctor, same slot) | High (Major × Medium) | FR-003 | NFR-007 | **Yes.** NFR-007, TC-007, and the unique `(doctor, slot)` check in `BookingSystem.book()` target this exact failure mode. | Database unique constraint + application-layer validation | **Sufficient** |
| **HZ-003** | Medical-record data breach via cyberattack | High (Catastrophic × Low) | FR-012 (RBAC, supporting) | NFR-003, NFR-004 | **Partially.** NFR-003 requires AES-256 at rest and TLS 1.2+ in transit; NFR-004 requires data minimisation. Neither SMART statement requires an independent attack to succeed or fail. | Encryption, TLS, RBAC, intrusion monitoring | **Insufficient** |
| **HZ-004** | System outage during peak hours | Medium | FR-003 (booking unavailable) | NFR-002, NFR-008 | **Yes.** 99.5% monthly uptime and RPO ≤ 5 min / RTO ≤ 15 min address loss of booking capability. | Redundant architecture, auto-scaling, disaster-recovery plan | **Sufficient** |
| **HZ-005** | Reminder sent at the wrong local time (timezone bug) | Low | FR-006 | *(none)* | **No NFR is traced.** Mitigation is stated as UTC storage and timezone testing, but it is not a SMART NFR. | Standardise storage in UTC; multi-timezone testing | **Insufficient** (low residual risk) |

**Score.** 2 of 5 hazards (HZ-002, HZ-004) are sufficiently covered by existing NFRs. The three High-risk clinical/security hazards are not uniformly covered: HZ-001 and HZ-003 remain **Insufficient**. HZ-002 must not be confused with the *patient-side overlap* scenario analysed in Section 3; those are different conflict types.

A second logical defect in the current trace is that **HZ-001 lists NFR-007**. NFR-007 belongs to HZ-002. Reusing a booking-safety NFR as the “safety NFR” for prescribing is a category error: ISO/IEC 25010 *Safety* is not a single budget that can be spent once.

### 1.2 Critical commentary — HZ-001 requires an additional NFR on alert accuracy (false-negative rate)

HZ-001 is a **fail-open clinical decision-support (CDS)** hazard: the doctor continues to prescribe while the software silently omits the warning. The potential consequence in `hazards.csv` is catastrophic (dangerous drug administered). The existing artefacts do **not** constrain this failure:

1. **Wrong NFR is traced.** NFR-007’s SMART criterion is: *“The system shall raise a conflict warning within ≤ 1 second when a doctor double-booking is detected.”* Passing NFR-007 (and TC-007) can be achieved in a build that never evaluates allergies. Latency of a booking check is orthogonal to whether Amoxicillin is flagged against a Penicillin allergy.

2. **FR-008 is existence-only.** FR-008 states that the system *shall warn* when a prescription conflicts with a known allergy. It does not state a maximum **false-negative (FN)** rate, a maximum checker downtime, or fail-closed behaviour when the checker is unavailable. A function that warns on 70% of true conflicts still “implements FR-008” in a weak reading of the text.

3. **Tests currently reward true positives and false-positive hygiene, not FN control.** TC-005 and `test_TC005_drug_interaction_warning` assert that a known conflict *does* raise `warning=True`. `test_TC005b_no_false_positive_when_safe` asserts that Paracetamol does *not* warn. There is **no** requirement, test, or metric for: incomplete allergy lists, missing rows in the interaction catalogue, timeout of the checker, or “no warning because the service threw an exception.” In safety engineering, **false negatives dominate false positives** for this hazard. A false positive costs a confirmation click (alert fatigue is real, but secondary). A false negative realises HZ-001.

4. **The recorded mitigation is procedural, not a system NFR.** “Mandatory manual double-check + mandatory warning logging” shifts residual risk onto the clinician and onto an audit log. Logging proves that a warning was *emitted*; it cannot detect warnings that were *never generated*. Manual double-check is not measurable in the NFR set and is unreliable under time pressure.

**Recommended additional NFR (proposed NFR-011 – Clinical alert accuracy).**

| Field | Proposed content |
| --- | --- |
| ID | NFR-011 |
| Attribute | Safety / reliability of CDS alerts |
| SMART criterion | On a frozen, versioned clinical test set of ≥ 1,000 prescription–patient pairs with known ground truth, the allergy/interaction checker shall achieve a **false-negative rate ≤ 0.1%** (no more than one missed true conflict per 1,000 positive cases, 95% confidence to be demonstrated). If the checker is unavailable, times out, or returns an error, prescription **save shall be blocked** (fail-closed) and the incident shall be logged; fail-open save is prohibited. |
| ISO 25010 | Reliability (availability of the checker) + Safety |
| Verification | Independent clinical test-set evaluation + fault-injection (checker down / timeout) + TC-005 extended with FN cases |
| Priority | High, because HZ-001 is High residual risk until this NFR exists |

Without NFR-011, the safety case for HZ-001 is incomplete: FR-008 and a mis-traced NFR-007 cannot be said to “mitigate” a missed warning.

### 1.3 Critical commentary — HZ-003 requires the addition of Penetration Testing as an NFR

HZ-003 is a **confidentiality / integrity** hazard: an attacker obtains or alters medical records. Current mitigations (AES-256, TLS, RBAC, “intrusion monitoring”) and NFR-003/NFR-004 are **necessary but not sufficient**.

1. **Encryption is not evidence of exploit resistance.** NFR-003’s measurable statement is only that data *shall be encrypted* (AES-256 at rest, TLS 1.2+ in transit). CR-002 further upgrades the algorithm to AES-256-GCM. A correctly encrypted database still leaks if an attacker obtains a valid session (broken authentication), injects a query (SQLi), traverses an IDOR on `visit_result`, or exfiltrates keys. TC-010 only checks that a column is ciphertext at rest. TC-009 checks one RBAC path (patient → admin API). Neither simulates an adaptive adversary.

2. **Verification method ≠ requirement.** NFR-003 lists “Configuration review + penetration test” under *VerificationMethod*. That cell describes *how someone might later check* the encryption requirement; it does **not** make pentesting itself a contractual, recurring, SMART obligation. A team can mark NFR-003 as “implemented” after a checklist review of TLS ciphers and never commission a pentest. For a Catastrophic privacy hazard, verification that can be skipped is not a mitigation.

3. **NFR-004 is not testable against HZ-003.** “Follow data-minimisation principles” has no numeric criterion (fields collected, retention days, access-log completeness). A compliance checklist cannot substitute for attempting to break the system.

4. **Why pentesting specifically.** Configuration review confirms *intended* controls. Penetration testing attempts *unintended* paths (OWASP ASVS / healthcare profile: authn, session, access control, injection, cryptographic misuse, API abuse). Only the latter can falsify the claim “a cyberattack will not yield medical records.” Intrusion monitoring (listed in the hazard row) is detective; pentesting is preventive assurance before production.

**Recommended additional NFR (proposed NFR-012 – Independent penetration testing).**

| Field | Proposed content |
| --- | --- |
| ID | NFR-012 |
| Attribute | Security assurance |
| SMART criterion | An independent penetration test covering the OWASP Application Security Verification Standard (ASVS) Level 2, including authentication, access control, injection, and medical-record APIs, shall be completed **before first production release** and **at least annually** thereafter, and after any High-priority change to NFR-003/FR-012. **No open Critical or High findings** at go-live; Medium findings shall have a documented owner and closure date ≤ 30 days. |
| ISO 25010 | Security |
| Verification | Third-party pentest report + issue tracker evidence (see Section 6: Jira) |
| Priority | High (HZ-003 is High risk) |

NFR-003 should remain (encryption). NFR-012 is the missing **assurance** requirement that makes HZ-003’s mitigation empirically checkable. Until NFR-012 is added, compliance of HZ-003 is judged **Insufficient**.

---

## 3 New Scenario Analysis (Part 3) — Patient appointment overlapping another doctor’s schedule

### 3.1 Business rationale for the proposed scenario

**Scenario name.** Patient overlapping booking (self-proposed; **not** HZ-002).  
**Actors.** Patient (SH-01), two or more doctors (SH-02), optionally Receptionist (SH-03).  
**Trigger.** A patient who already holds an appointment with Doctor A at interval \([t, t+d]\) attempts to book Doctor B at an interval that intersects \([t, t+d]\) (including travel/setup buffer if the clinic defines one).

This scenario is absent from the current 12 FRs, 10 use cases, and from NFR-007. HZ-002 and NFR-007 constrain **one doctor occupying two patients in the same slot**. The proposed scenario constrains **one patient occupying two doctors in overlapping time**. The failure modes differ:

| Dimension | HZ-002 / NFR-007 (doctor double-book) | Proposed scenario (patient overlap across doctors) |
| --- | --- | --- |
| Scarce resource | Doctor’s calendar (clinically exclusive) | Patient’s time (usually exclusive, sometimes legitimately not) |
| Harm if ignored | Two patients assigned to one clinician; queues, delayed urgent care | Patient misses or is late to one visit; wasted slot; possible no-show cost |
| Harm if over-constrained | Low: a doctor cannot ethically be in two rooms | **High:** denial of multi-specialty same-day care, second opinions, or walk-in follow-up |
| Current software | `BookingSystem.book()` **hard-blocks** same doctor + same slot (`BookingConflictError`) | Not implemented; a second doctor at the same datetime is currently allowed |

**Why MedBook should specify this scenario.** Outpatient journeys are not single-specialty. Typical legitimate overlaps or near-overlaps include: (i) same-day cascade (imaging or lab, then specialist); (ii) second opinion on the same morning; (iii) parent/caregiver using one account for two dependents if identity modelling is weak; (iv) a patient who accepts a newly offered slot that collides with an already-confirmed visit they intend to cancel later. Without a dedicated rule, receptionists discover collisions only at the desk (FR-005), after reminders have already been sent (FR-006), which wastes doctor capacity—the same operational harm HZ-002 tries to reduce, but on the patient side.

The scenario therefore has a **clear business case**: protect utilisation and patient experience *without* copying the doctor-side exclusive lock onto the patient.

### 3.2 Soft-warning rather than hard-block

The system shall **detect** the overlap, **inform** the patient (and show a flag to the receptionist), and **allow confirmation** after acknowledgement. It shall **not** refuse the second booking solely because another doctor is already booked for that patient in an overlapping window.

**Arguments for soft-warning**

1. **Access to care dominates calendar purity.** A hard-block would reject a cardiology slot because a GP slot overlaps by 15 minutes, even when the clinic can shorten the first visit or the patient can travel between adjacent departments. In a safety-critical *health* system, blocking care is itself a hazard (delayed diagnosis). HZ-004 already treats inability to book as a clinical-availability risk; a hard-block on overlap would manufacture that hazard for patients who need two services.

2. **Asymmetry with NFR-007 is intentional, not inconsistent.** A doctor’s slot is a physically exclusive resource; two concurrent patients is always a defect (HZ-002). A patient’s time is a *preference* with exceptions. Logical consistency of the safety case requires **different control strength** for different resources: hard-block (or DB unique constraint) for `(doctor, slot)`; advisory control for `(patient, overlapping interval)`. Using one policy for both would either weaken doctor safety or over-constrain patients.

3. **Hard-block creates unsafe workarounds.** If the product refuses the second booking, users register duplicate accounts, book under a relative’s name, or ask reception to delete the first appointment before the two-hour cancellation window (FR-004). Those workarounds degrade FR-001 identity integrity, FR-012 auditability, and HZ-003 accountability. A soft-warning keeps a single identity and an explicit acknowledgement in the audit log.

4. **The residual risk is operational, not catastrophic.** Missing a warning on a drug (HZ-001) is Catastrophic. A patient who knowingly double-books two doctors produces wait-time and no-show cost (Major at most, often Moderate). Residual risk is acceptably managed by: on-screen warning, optional travel-time buffer, receptionist visibility (UC-05), and reminder content that lists *all* same-day visits (FR-006).

5. **Usability (NFR-006) and confirmation workflow.** NFR-006 requires a first booking in ≤ 3 minutes. A hard-block forces the patient to cancel/reschedule (FR-004, UC-04) before retrying, which breaks the happy path of UC-03. A modal “You already have an appointment with Dr. A at 09:00. Book Dr. B at 09:15 anyway?” preserves the three-minute path.

**Proposed requirement sketch (not a hard-block NFR).** Extend FR-003 / UC-03 with an exception path: *If the selected slot overlaps another active appointment of the same patient, the system shall display a soft-warning and require explicit confirm; the booking is created if the patient confirms.* Receptionist confirmation (FR-005) shall display the same flag. This remains distinct from NFR-007, which continues to **reject** a second patient for the same doctor and slot.

---

## 6 Limitations and Future Work (Part 6)

### 6.1 Limitations

**Small requirements scale (12 FRs).** The MedBook corpus used in this laboratory contains 12 functional requirements, 10 NFRs, 10–12 use cases, 10–12 test cases, 5 change requests, and 5 hazards. That is appropriate for teaching traceability (FR → UC → TC → code), but it is not a hospital-scale specification. Entire classes of safety requirement are missing or only sketched: clinical alert accuracy (Section 1.2), assurance pentesting (Section 1.3), patient-overlap policy (Section 3), consent/audit retention, medical-device integration, and pharmacy systems. Coverage percentages (for example Lab 7 RTM figures) therefore **overstate** readiness: 58% FR-to-test coverage on 12 FRs is not comparable to coverage on a 200-requirement SRS.

**Simulated data, not operational evidence.** Stakeholders, hazards, and NFRs are constructed teaching datasets (`datasets/*.csv`), not extracts from a live HIS. `simulate_booking.py` holds appointments in memory; it does not exercise a unique SQL constraint, TLS, AES-256, or concurrent transactions. Lab 6 NFR “measurements” used a seeded random model (`random.seed(42)`), not production latency. TC-006 (500 concurrent search users) and NFR-001/NFR-002/NFR-008 have **not** been observed on real infrastructure. Safety judgements in Section 1 (Sufficient / Insufficient) are therefore **logical** cross-checks against the specification, not empirical residual-risk estimates. HZ-003 in particular cannot be closed without attacks on a deployed system (hence NFR-012).

**Narrow automated safety tests.** `test_safety_scenarios.py` implements TC-001–TC-005 and one false-positive check. It does not implement TC-007 race conditions against a real database, FN injection for HZ-001, or security tests for HZ-003. Conclusions about “the code implements NFR-007” apply only to the in-process uniqueness loop.

**Traceability defects inherited from the corpus.** HZ-001 is linked to NFR-007 (incorrect). HZ-005 has no NFR. These defects were treated as findings, not silently “fixed” in a way that would hide them from the group report.

### 6.2 Future work

**Integration with enterprise requirements tools (Jira, IBM DOORS).** CSV files and `re_tool.py` demonstrate classroom traceability (`trace FR-003`, `hazard-report`). A production RE process should:

- Hold the SRS objects (SH, FR, NFR, UC, TC, CR, HZ) as **configuration-managed objects** in IBM Engineering Requirements Management DOORS (or equivalent), with stable IDs and baseline/version history.
- Bidirectionally link each hazard to mitigating NFRs (so the HZ-001 ↔ NFR-007 error becomes a live traceability rule, not a spreadsheet inspection).
- Export approved requirements and the Hazard → NFR table to **Jira** as epics/stories/bugs (e.g. NFR-011, NFR-012, patient-overlap soft-warning), with `ReqID` as an issue label so test execution and pentest findings close against the same ID.
- Use Jira workflow to enforce Section 1.3: no production release while NFR-012 Critical/High findings remain `Open`.

**Real-world load and resilience testing (JMeter / k6).** Replace Lab 6’s simulated latency with tests against a deployed MedBook API:

- **k6** (or JMeter) scenarios for NFR-001 (doctor search, 500 virtual users, p95 ≤ 2 s) and for NFR-007 under contention (two users booking the same doctor-slot; assert rejection ≤ 1 s and exactly one success).
- Soak and spike tests toward NFR-005 (3× booking volume) and NFR-002 (error budget consistent with 99.5% monthly uptime).
- Disaster-recovery drills that measure NFR-008 RPO/RTO on real backups, not on an in-memory list.

Until those integrations and tests exist, MedBook’s safety case remains a **consistent specification review** (this member’s contribution) rather than a validated operational safety argument.

---

**End of Member 2 contribution (Sections 1, 3, and 6).**
