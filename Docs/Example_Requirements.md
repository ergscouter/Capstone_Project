# EagleEye — Requirements & Traceability

Requirements as stated by the project sponsor, each mapped to the backlog that implements it. The backlog (`docs/backlog/BACKLOG.md`) is the source of truth for scope; this document is the source of truth for *why* each item exists and for proving coverage.

- **Status:** baselined 2026-09-19 · Sprint 0
- **Backlog:** 13 epics · 57 features · 185 stories (78 happy path, 60 alternate path, 47 error condition)
- **IDs:** `FR-n` functional, `NFR-n` non-functional, `PR-n` process/project. Backlog references use `E<epic>.F<feature>.S<story>`.
- **Priority:** MoSCoW. MVP = Must, R2 = Should, R3 = Could.
- **Change control:** the Product Owner approves changes here; every change updates the mapped backlog stories in the same PR.

---

## 1. Functional requirements

| ID | Requirement | Backlog coverage | Stories | Priority | Verified by |
|---|---|---|---|---|---|
| FR-01 | Produce a daily route plan from the student's schedule, recommending the least expensive way to travel between each pair of classes. | E3.F1 Daily Itinerary · E3.F3 Least-Expensive Recommendation · E3.F5 Cost Model | 11 | Must | Unit tests on the cost optimizer; E2E day-plan test |
| FR-02 | Support walking, bicycle or scooter, driving, and the campus bus system where available. | E3.F2 Mode Options · E3.F4 Mode-Appropriate Paths | 9 | Must (walk, bus, drive) / Should (bike, scooter) | Per-mode routing tests against fixture schedules |
| FR-03 | Each mode uses avenues appropriate to it (sidewalks, bike lanes and racks, scooter rules and corrals, permitted parking lots, bus routes and stops). | E3.F4.S1–S6 | 6 | Must / Should | Routing assertions on OSM + campus rule data |
| FR-04 | Show distance and time estimates for every mode on every leg. | E3.F2.S1 · E3.F2.S2 · E3.F2.S3 | 3 | Must | Unit + UI tests; degraded-estimate labeling test |
| FR-05 | Check in real time whether weather, traffic or campus activity affects the planned route. | E6.F1 Weather · E6.F2 Traffic · E6.F3 Real-Time Bus · E6.F4 Campus Disruptions · E6.F6 Emergency Alerts | 15 | Should | Integration tests with recorded feed responses |
| FR-06 | Offer alternate travel options, with completion time frames, when conditions change. | E6.F1.S2 · E6.F2.S2 · E6.F3.S2 · E6.F5 Alerts & Notifications | 7 | Should | Scenario tests: rain, traffic delay, late bus |
| FR-07 | Account for national holidays and the UNT academic calendar. | E7.F1 National Holidays · E7.F2 Academic Calendar & Testing | 6 | Must (holidays) / Should (finals, breaks) | Calendar-rule unit tests across a full term |
| FR-08 | Account for campus activities: testing schedules, sporting events, club activities, protests and religious holidays. | E7.F2.S3 · E7.F3 Sporting Events · E7.F4 Clubs · E7.F5 Protests · E7.F6 Religious Observances · E7.F7 Admin Curation | 12 | Should | Admin-curation tests; geofence effect on routing |
| FR-09 | Upload a class schedule and activities from one or more calendars. | E2.F1 File Upload · E2.F2 Connected Calendars · E2.F3 Manual Entry · E2.F4 Location Resolution · E2.F5 Personal Activities | 18 | Must (file, Google, ICS URL, manual) / Should (Outlook, activities) | Parser unit tests; OAuth integration tests; dedupe tests |
| FR-10 | Support multiple user accounts, including more than one account on a shared device. | E1.F1 Registration & Sign-in · E1.F2 MFA & Sessions · E1.F3 Multiple Accounts · E1.F4 Profiles · E1.F5 Onboarding · E1.F6 Data Rights | 23 | Must | Auth E2E tests; per-account encryption test |
| FR-11 | Share the application with other users using a 2D barcode. | E9.F1 Invite QR · E9.F2 Scan & Install · E9.F3 Share a Meeting Route | 7 | Must (invite, scan) / Could (route share) | QR round-trip test; tampered-payload rejection test |
| FR-12 | Schedule a ride with a rideshare app such as Uber or Lyft. | E8.F1 Rideshare as a Mode · E8.F2 Book a Ride · E8.F3 Scheduled Rides | 8 | Could | Deep-link launch tests per platform |
| FR-13 | Display routes on a map. | E4.F1 Route Map Display | 3 | Must | Widget tests; screen-reader step-list audit |
| FR-14 | Aid navigation to a classroom inside a building. | E5.F1 Floor Plans · E5.F2 Entrance-to-Room Routing | 5 | Should | Indoor routing tests on digitized floor plans |
| FR-15 | Use the device GPS when it is available or activated. | E4.F2 GPS Positioning · E5.F3 Indoor Positioning | 6 | Must (outdoor) / Should (indoor) | Simulated-location tests, including denied and low-accuracy |
| FR-16 | Load and save map data so the app works when GPS or the network is unavailable. | E4.F4 Offline Map Data · E5.F4 Offline Building Data | 6 | Must (campus pack) / Should (buildings) | Airplane-mode E2E test; signature-mismatch test |

---

## 2. Non-functional requirements

| ID | Requirement | Backlog coverage | Priority | Verified by |
|---|---|---|---|---|
| NFR-01 | Stringent security review of the code; no exploitable vulnerabilities shipped. | E11.F5 Secure SDLC Pipeline · E11.F7.S2/S3 release gates | Must | SAST, dependency, secret and container scans on every PR; ZAP nightly; pen test before launch |
| NFR-02 | Student PII (schedule, location, name, email, calendar tokens) is protected against loss or disclosure. | E11.F1 Threat Model · E11.F2 Data Protection · E11.F3 Authorization · E11.F6 Logging | Must | Log-redaction test; IDOR test per endpoint; encryption verification |
| NFR-03 | Data minimization: location history stays on the device; the server never stores route coordinates. | E11.F2.S2 · E1.F6.S3 | Must | Network capture review; server-side storage assertion |
| NFR-04 | All untrusted input (calendar files, QR payloads, API requests) is validated before use. | E11.F4 Input Validation · E2.F1.S4 · E9.F2.S3 | Must | Schema validation tests; parser fuzz suite in CI |
| NFR-05 | Runs on iOS, Android, Windows, macOS, Linux and the web from one codebase. | E10.F1 Mobile · E10.F2 Desktop & PWA | Must (mobile, web) / Should (desktop) | Build matrix in CI; smoke test per platform |
| NFR-06 | Data stays consistent across a student's devices, including after offline use. | E10.F3 Sync Across Devices | Must | Two-device sync and conflict tests |
| NFR-07 | Accessible to students using screen readers or with mobility needs. | E10.F4.S1 · E4.F1.S3 · E1.F4.S3 · E5.F2.S2 | Must | WCAG 2.2 AA automated + manual audit |
| NFR-08 | A day plan returns within 2 seconds at p95 under 500 concurrent users. | E12.F2.S4 | Should | k6 performance test on staging |
| NFR-09 | Compliance with FERPA, the Texas Data Privacy and Security Act and UNT IT policy; accurate privacy disclosures. | E11.F7 Compliance & Release Gates · E11.F6.S3 | Must | Signed ASVS L2 / MASVS L2 checklist; privacy policy review |
| NFR-10 | Campus and map data can be rebuilt and republished without a code release. | E12.F4 Campus Data Pipeline | Should | Nightly pipeline run; bad-source-data failure test |

---

## 3. Process & project requirements

| ID | Requirement | Where satisfied |
|---|---|---|
| PR-01 | The plan is expressed as epics containing features, and features containing user stories. | `docs/backlog/BACKLOG.md` — 13 epics, 57 features, 185 stories |
| PR-02 | Each user story represents exactly one happy path, one alternate path, or one error condition. | Every story carries one tag: 78 [H], 60 [A], 47 [E] |
| PR-03 | The backlog is usable by a 4-person team with Product Owner, Project Manager, Developer, unit testing, QA and Marketing roles. | "Team Roles, Process & Roadmap" in the backlog; QA and unit testing in E12.F2; marketing in E13 |
| PR-04 | Recommend the skills and tooling that help build and manage the application. | "Recommended Claude Code Skills & Tools" in the backlog — 16 entries, including 3 team-specific skills to create |
| PR-05 | All application source is generated rather than hand-written. | Deferred by sponsor decision (2026-09-19): planning artifacts only until a specific story is requested. Recorded in `CLAUDE.md` → Status |
| PR-06 | Work is traceable from requirement to story to test. | This document → backlog story IDs → branch, PR and test names (`CLAUDE.md` → Conventions); traceability matrix required by E12.F2.S5 |

---

## 4. Assumptions

1. The campus is UNT Denton, including Discovery Park; other UNT locations are out of scope for the MVP.
2. Riding the UNT bus system is free with a student ID, so bus legs cost $0 in the default cost model.
3. Students supply their own schedule (file, calendar connection or manual entry); no direct integration with UNT student records is assumed.
4. Uber and Lyft are launched through deep links; fares shown are estimates unless partner API access is granted.
5. Indoor floor plans are available for a starter set of high-traffic buildings, not the whole campus.

## 5. Constraints and open dependencies

Each item below is a Sprint 0 spike. Every one has a fallback so no requirement is blocked.

| Dependency | Affects | Fallback if unavailable |
|---|---|---|
| UNT Transit / DCTA GTFS and GTFS-Realtime feeds | FR-02, FR-03, FR-05 | Manually authored GTFS; scheduled times labeled "scheduled" |
| UNT SSO (EUID) approval from UNT IT | FR-10 | Email registration with MFA (already in E1.F1/F1.2) |
| UNT Facilities floor plans | FR-14, FR-16 | Student-digitized plans for permitted buildings only |
| Uber / Lyft partner API | FR-12 | Deep links plus distance-based estimates |
| Official protest or demonstration feed | FR-08 | Admin-curated advisories plus moderated student reports |
| UNT trademark approval for public branding | E13.F1 | Launch with a clear "not affiliated with UNT" disclaimer |

## 6. Out of scope (this release series)

- Turn-by-turn driving navigation beyond reaching a parking lot (students use their own navigation app for the off-campus drive).
- Paying for parking, transit or scooters inside EagleEye.
- Booking rooms, registering for classes or any write-back to UNT systems.
- Campuses other than UNT Denton; languages other than English and, in R3, Spanish.

## 7. Verification summary

| Level | What it proves | Gate |
|---|---|---|
| Unit | Domain rules: cost optimizer, schedule parser, holiday and calendar rules | ≥ 85% coverage of domain logic in CI |
| Integration / contract | API and external feeds behave as expected, including failures | OpenAPI contract tests; recorded-response feed tests |
| E2E | Each MVP happy-path story works end to end | ≥ 1 automated E2E per MVP happy-path story |
| Security | NFR-01 to NFR-04, NFR-09 | Clean PR scans, nightly DAST, signed ASVS/MASVS checklist, pen test before launch |
| Accessibility | NFR-07 | WCAG 2.2 AA automated + manual audit per release |
| Performance | NFR-08 | k6 run on staging per release |
| Acceptance | Every story's acceptance criterion | QA sign-off on at least one mobile and one desktop target |
