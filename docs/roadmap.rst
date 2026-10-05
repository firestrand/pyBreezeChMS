Feature and improvement roadmap
===============================

:Version: 1.1.0
:Reviewed: 2026-10-03
:Baseline: pyBreezeChMS d91fa92; EasyTithe submodule 29321b1
:Scope: Python API library, provider-independent data exchange, importer, tests, packaging and CI
:Status: Approved local implementation; authenticated provider acceptance remains

Purpose and review basis
------------------------

Make integrations safer to operate, easier to extend, and simpler to maintain.
This is a decision roadmap, not a dispatch-ready implementation plan. Before an
initiative is implemented, turn its acceptance criteria into a small reviewed
plan with protecting tests, any needed GOTCHA spec, and an ATLAS report.

The review used current source and configuration, not only the prior maintenance
report. Baseline verification: 115 offline tests passed; Ruff and ty passed.
No authenticated service call was made. Current service behavior and provider
payloads remain unverified beyond published documentation and existing fixtures.

Applicable technical guidance is Python Code Standards revision 2026-09-29 in
/home/firestrand/Dropbox/Projects/Software-Standards/. No roadmap-specific guide
was found in that library. The development-plan-creation-guide.md principles
DP-08 (SOLID/DRY/KISS), evidence-based sequencing, and explicit decision gates
inform this roadmap; its executable-plan emission contract does not describe
this deliverable. Features below are proposals, not invented PRD requirements.

Baseline capabilities and findings
----------------------------------

* The library covers people, profile fields, events, contributions, funds,
  pledges, tags, account summary, and form entries. BreezeApi provides a typed
  injectable HTTP boundary, per-client session ownership, bounded reads,
  sanitized errors, verified TLS, and no redirects or automatic retries.
* Tests exercise endpoint serialization, transport failures, cleanup, JSON
  validation, and the importer. Locked format/lint/type/test/security/build
  checks and installation smoke checks are already present. Preserve them.
* The importer resolves people by literal case-insensitive names. Duplicate
  detection uses person/date/amount; unmatched records are imported anonymously.
  It validates the downloaded report before writing, but donor ambiguity and
  duplicate decisions are discovered inside the write loop. Earlier gifts may
  already have been written when a later record fails.
* EasyTithe construction logs in and can save a changed Custom export format.
  Therefore --dry_run currently prevents Breeze calls, not all remote changes.
* Breeze requests have an inactivity timeout and byte limits, but no pacing,
  structured failure categories, or operation-wide deadline. Sequential calls
  can still exceed a provider quota.
* Query construction is duplicated across BreezeApi endpoint methods, especially
  add_contribution and edit_contribution. JsonValue is honest transport typing,
  but consumers must still check endpoint-specific shapes themselves.
* get_people accepts pagination arguments, but the importer fetches all people
  at once. No iterator manages pages or maximum traversal bounds.

Evidence anchors
----------------

* ``breeze/breeze.py``: HttpConnection, BreezeApi._request, get_people,
  add_contribution, edit_contribution, list_contributions and list_form_entries.
* ``samples/easytithe_importer.py``: Contribution, _people_index,
  import_contributions and main.
* ``samples/easytithe/src/easytithe/__init__.py``: EasyTithe.__init__, _login,
  _configure_export, _request and GetContributions.
* ``tests/test_client_boundaries.py``, ``tests/legacy/test_importer.py`` and
  ``samples/easytithe/tests/test_easytithe.py``: current behavior protections.
* ``pyproject.toml``, ``scripts/check.sh``, ``scripts/check-artifacts.sh`` and
  both repositories' ``.github/workflows/ci.yml``: current delivery gates.
* `Breeze API reference <https://app.breezechms.com/api>`_: people pagination,
  form discovery, attendance reads, and giving integration contracts. Its uid
  represents a giving-platform person identity, not a transaction identity.
* `Breeze API support guidance <https://support.breezechms.com/hc/en-us/articles/360001324153-API-Advanced-Custom-Development>`_:
  published request quota is 20 per minute, with approximately 3.5-second
  spacing recommended. Recheck policy before implementing R01.

Architecture rules for every initiative
---------------------------------------

* Single responsibility: keep HTTP mechanics, provider decoding, import
  decisions, and CLI configuration separate only where their reasons to change
  differ. Extract the existing importer use case before inventing new services.
* Open/closed: extend endpoint functions or a small adapter at established
  boundaries. A second contribution source should not require editing matching
  or duplicate policy. Avoid a plugin registry before a real second source.
* Liskov substitution: adapters satisfying a port must preserve error, cleanup,
  absence and side-effect contracts. A no-op or preview mode cannot secretly
  perform a write or silently change return shapes.
* Interface segregation: import code needs a few domain operations, not every
  BreezeApi endpoint. Expose narrow importer ports when R03 needs them; retain
  HttpConnection for low-level transport tests.
* Dependency inversion: import policy should depend on those small ports and
  validated records, not Requests, provider JSON dictionaries, or a CLI parser.
  Implement provider conversion at the edge; keep wiring at the entry point.
* DRY: consolidate repeated query/validation rules within Breeze only after
  characterization tests protect their differences. Do not build a shared
  transport framework across Breeze and EasyTithe merely because both use HTTP.
* KISS: start with synchronous functions, a small immutable plan, and a local
  journal where justified. Add concurrency, databases, or plugins only when a
  measured workload or an approved capability requires them.

Priority and sequencing
-----------------------

P0 protects against external side effects or incorrect financial decisions;
P1 improves repeatable operation; P2 expands capability after those foundations.
Size is relative review scope (S: focused change; M: a few related slices;
L: cross-cutting work). It is not a time or delivery commitment.

.. list-table:: Proposed queue
   :header-rows: 1
   :widths: 10 10 42 8 30

   * - ID
     - Priority
     - Outcome
     - Size
     - Prerequisites
   * - R01
     - P0 / Now
     - Respect quotas and classify failures
     - M
     - Refresh rate/error contracts
   * - R02
     - P0 / Now
     - Preview without changing provider settings
     - S-M
     - Confirm read-only export behavior
   * - R03
     - P0 / Now
     - Review a complete import plan before writes
     - M
     - R01, R02; matching-policy decision
   * - R04
     - P1 / Next
     - Resume safely and reconcile uncertain writes
     - L
     - R03; identity gate for cross-export deduplication
   * - R05
     - P1 / Next
     - Traverse people in bounded pages
     - S-M
     - R01; pagination contract
   * - R06
     - P1 / Next
     - Reduce endpoint duplication and add typed helpers
     - M
     - Characterization evidence; R01 contract
   * - R07
     - P1 / Next
     - Validate actual provider compatibility
     - M
     - Authorized non-production access
   * - R08
     - P2 / Later
     - Import an approved local CSV export
     - M
     - R03, R04; CSV schema decision
   * - R09
     - P2 / Later
     - Discover forms and read attendance
     - M
     - R01, R06, R07; user demand
   * - R10
     - P2 / Later
     - Package repeatable operator workflows
     - S-M
     - R03, R04, R07; support scope decision

R01 -- Quota-aware requests and actionable failures
---------------------------------------------------

**Why:** BreezeApi._request issues requests immediately and collapses HTTP
statuses into one BreezeError. The importer can make a lookup and write per gift.

**Approach:** Introduce configurable per-account pacing at the Breeze boundary,
including an explicit sharing strategy for multiple client instances. Use
sanitized error subclasses/metadata for authentication, rate limits, transport,
and response validation. Classify endpoints by business effect: several writes
use HTTP GET, so the HTTP verb alone cannot determine retry safety. Keep mutation
retries disabled. Add bounded read retries only after transient status and
Retry-After behavior are verified. Define finite timeout inputs and distinguish
inactivity timeout from an overall operation deadline; review both clients.

**Acceptance:** tests demonstrate configured pacing across relevant calls,
finite configuration validation, bounded read attempts/deadlines, correct error
categories, response cleanup, and exactly one attempt for every mutation after
an uncertain transport failure. Existing base BreezeError catches still work.
Use a controlled clock for time-policy tests; never make the suite sleep.

**Design/rollout:** one request-policy responsibility (SRP), additive exceptions
for compatibility (LSP), small configurable policy rather than a scheduler (KISS).
Shared credentials in other processes remain outside an in-process limiter;
restrict initial supported deployment to one coordinated account worker unless
an approved distributed requirement justifies more. Ship before bulk imports.

R02 -- Read-only source previews
--------------------------------

**Why:** main constructs EasyTithe even during dry-run; its constructor may call
SaveExportProfileOptions. Current tests confirm that save behavior.

**Approach:** Make export-format setup an explicit source operation. Provide a
read-only path that uses an already-compatible profile and fails with a clear
setup instruction if a change is needed. Preserve the BreezeApi dry-run no-call
contract. Separate report-only dry-run from an optional read-only Breeze preview;
name and document those modes explicitly rather than silently changing behavior.

**Acceptance:** dry-run produces no Breeze request and no export-profile save;
a mismatched source profile fails before any provider write; explicit setup
still works. Construction, setup and download cleanup paths stay tested.

**Design/rollout:** separate configuration from retrieval (SRP); read-only means
read-only for every adapter (LSP). Implement in the EasyTithe repository first,
verify its standalone artifact, then pin its commit and update the importer.
Document the changed setup default and keep rollback per repository.

R03 -- Plan, validate, review, then apply an import
---------------------------------------------------

**Why:** import_contributions mixes matching, duplicate decisions, logging and
writes. Name conflicts are found mid-import, and equal-value gifts can be skipped.

**Approach:** Extract a small pure planning function plus an apply function. A
validated immutable plan records create, skip and unresolved decisions and a
summary; apply refuses unresolved entries. Require an explicit mapping/policy
for ambiguous or anonymous donors. Compare verified transaction identity when
available; person/date/amount alone must produce a duplicate candidate requiring
review, not a claim of a confirmed duplicate. Validate required fund identifiers,
amount precision/currency rules and source date-window membership according to
approved financial policy. Read-only preview resolves donors and candidates;
report-only dry-run remains usable without contacting Breeze.

**Acceptance:** ambiguity in the final row results in zero writes; two distinct
gifts with equal person/date/amount are not silently discarded; unresolved donor
or duplicate candidates cannot reach apply. Summaries account for every row.
Validation errors are actionable without logging names, keys or gift payloads.

**Design/rollout:** pure decisions and separate I/O (SRP/DIP), one small importer
gateway rather than the whole Breeze client (ISP), immutable records (KISS).
Proposed module location: ``samples/import_plan.py`` until R10 justifies packaging;
this file does not exist yet. Define the gateway contract before its adapter.
Ship each reviewed slice with protecting tests; new policy requires operator
approval rather than quietly rewriting current matching semantics.

R04 -- Durable progress and uncertain-write reconciliation
----------------------------------------------------------

**Why:** there is no persisted run state. A crash after a successful remote write
but before local acknowledgement can lead to duplicate writes when rerun.

**Gate for cross-export deduplication:** obtain evidence of a stable source
transaction identity and determine whether Breeze preserves a usable receipt/reconciliation identifier. The current
EasyTithe export exposes PersonID, not a documented transaction ID. Breeze uid
is donor identity. Neither is sufficient evidence of transaction idempotency.

**Approach:** Begin with one approved immutable export snapshot and a minimal
local journal tracking planned, submitted, acknowledged and uncertain rows.
An uncertain row requires reconciliation; never replay it automatically. If a
source identity becomes available, strengthen cross-export duplicate detection.
Choose an atomic local file or stdlib SQLite only after required update/crash
semantics are agreed. Store minimal identifiers, restrict file access, define
retention, and enforce one writer. Do not promise exactly-once delivery.

**Acceptance:** restart preserves acknowledged rows; a crash at each write/journal
boundary causes no automatic resend of an uncertain gift; journal corruption
stops apply safely; operator reconciliation and decisions have a clear audit trail.
Distinct identical gifts stay distinct. Cross-export deduplication remains
blocked until identity evidence supports it.

**Design/rollout:** progress persistence has one responsibility (SRP); one small
journal seam if needed (DIP), one worker and explicit states (KISS). Introduce
recovery per capability slice. Reverting code must not erase the journal or
reverse already-imported gifts; provide a read-only recovery/export path.

R05 -- Bounded people pagination
--------------------------------

**Why:** get_people exposes limit/offset while the importer fetches one unbounded
logical result set, constrained only by the byte limit.

**Approach:** Add an additive iterator over people using documented pagination,
with positive page size, max pages/items, failure propagation and repeated-page
protection. Update planning to build its index from that iterator. Document that
offset pagination does not guarantee a snapshot if people change during traversal.

**Acceptance:** empty, partial and full final pages terminate; no records vanish
at a page boundary; traversal limits stop without returning an apparently complete
index; failed or repeated pages cannot proceed to apply. Pacing covers every page.

**Design/rollout:** keep get_people unchanged (LSP); one generator, one buffering
policy and no concurrent paginator (KISS). Tests precede the new iterator and its
consumer wiring. Benchmark memory only if making a scaling claim.

R06 -- Shared request serialization and useful typed helpers
------------------------------------------------------------

**Why:** add/edit contribution query construction is substantially repeated;
all ordinary methods return broad JsonValue unions to consumers.

**Approach:** First characterize endpoint differences, field ordering where
observable, omitted versus explicit values, Unicode, and zero/false inputs.
Then extract one small query/optional-field helper within Breeze. Offer additive
validated helpers for frequently consumed people/payment shapes and structured
fund input, keeping raw methods for callers needing vendor-specific fields.
Do not add a model hierarchy for every endpoint or share a generic cross-vendor
HTTP framework. Add observability only as bounded counts, status categories and
elapsed time, with no raw URLs, headers, bodies or donor identifiers.

**Acceptance:** existing public raw contracts and serialization behavior remain
protected; malformed endpoint shapes fail at the new typed boundary; fund payloads
serialize exactly; no broad Any or global diagnostic suppression is introduced.
Changed endpoint parameters get regression cases, not tests of a private helper.

**Design/rollout:** centralize repeated policy (DRY), preserve substitution and
raw compatibility (LSP/OCP), and extract only repeated logic (KISS). Split modules
only when responsibilities justify it, retaining BreezeApi as the public facade.

R07 -- Provider contract verification and compatibility upkeep
--------------------------------------------------------------

**Why:** offline fixtures verify local behavior but not today's authenticated
Breeze/EasyTithe service contracts. Packaging currently supports Python 3.14 only.

**Approach:** Capture approved minimal non-production provider responses and
login/export behavior without storing credentials or real church records.
Document provenance, retention, schema/version and refresh triggers. Keep default
tests offline; put authorized live checks behind explicit opt-in markers. Verify
redirect, quota, pagination and error behavior before enabling dependent features.
Keep locked tooling and review dependency/submodule updates as one compatibility
unit. Consider expanding Python support only after an actual compatibility need
and dependency validation, not by silently widening requires-python.

**Acceptance:** adapter behavior is traceable to a reviewed provider contract;
a service-contract change gives a clear regression signal; default CI never needs
live secrets. Both repos independently pass locked gates and clean wheel/sdist
installation checks, then the pinned integrated revision passes those checks.

**Design/rollout:** adapters own vendor details (SRP); shared domain-contract tests
protect interchangeable sources (LSP). No new capture/contract framework is
needed initially (KISS). Missing access blocks contract verification, not local
refactoring or this roadmap. Security approval governs any captured data.

R08 -- Offline CSV contribution source
--------------------------------------

**Why:** automated exports depend on an authenticated third-party website; an
approved local export can support offline validation and controlled recovery.

**Approach:** Add a streaming stdlib CSV source for an explicitly versioned export
schema. Reuse the validated contribution record and planning policy from R03;
include immutable source/row identity agreed in R04. Keep credentials out of the
local workflow. Normalize dates/encoding at the source edge and reject malformed
or incomplete financial records.

**Acceptance:** the local source produces the same approved domain records as
the automated source for a verified matching export; malformed rows and excessive
input stop before apply; previews work offline. Duplicate/recovery policy is
shared, not reimplemented in another CLI.

**Design/rollout:** a real second adapter demonstrates OCP/DIP/LSP; the source
port has only retrieval operations (ISP); use csv and pathlib before adding a
parser dependency (KISS). New source code belongs in the parent repository;
EasyTithe remains the owner of website-specific retrieval.

R09 -- Focused read-only API expansion
--------------------------------------

**Why:** published Breeze endpoints include form discovery/fields and attendance
reads, while the wrapper currently provides form entries and attendance writes.

**Approach:** Select one confirmed operator workflow first: discover forms and
fields before fetching entries, or inspect an event's attendance. Add only that
small endpoint slice and an executable usage example. Consider people filtering,
calendar/location discovery, or account-log reads only after demand is identified.
Deletion, family mutation and volunteer administration remain unprioritized.

**Acceptance:** each selected endpoint has verified parameters/response contracts,
success/empty/error cases, pacing, safe encoding and a working example. Existing
methods remain compatible. No server capability is inferred from a similar URL.

**Design/rollout:** thin additions at existing seams (OCP), optional validated
models where consumers need them, no speculative all-endpoints generator (KISS).
Published docs support candidates; R07 confirms actual authenticated behavior.

R10 -- Supported operator workflow and release documentation
------------------------------------------------------------

**Why:** the importer is a sample script and is excluded from the Breeze wheel;
using it requires a recursive checkout and the dev dependency group.

**Approach:** Decide whether the importer becomes supported product functionality.
If approved, package a minimal CLI with an explicit optional importer dependency
and version pin, plan/preview/apply commands, environment-based credentials,
nonzero failure exits, and privacy-safe run summaries. Handle expected failures
at the CLI boundary without printing raw chained transport exceptions, which
may contain request URLs or sensitive values. Keep READMEs and versioned
migration guidance synchronized without duplicating long operating procedures.
Do not introduce a web application or background service for this CLI use case.

**Acceptance:** a clean installed environment outside the checkout can run help
and an offline preview without dev tools; optional dependencies are explicit;
missing config, unresolved plans and partial failures have documented exits;
error output and summaries contain no credentials or personal/financial records;
recovery/retention guidance and both-repo rollback instructions are tested.

**Design/rollout:** CLI wiring stays thin (SRP/DIP); reuse plan/apply and validation
(DRY), select one distribution approach after support ownership is agreed (KISS).
Do not publish packages or schedule automatic imports without separate authority.

Decision gates and deferred work
--------------------------------

* D01, before R03: operator approves donor mapping, anonymous handling, duplicate
  candidate review, amount precision/currency and date-window policy.
* D02, before cross-export R04 guarantees: verify transaction identity and remote
  reconciliation capabilities. A local snapshot key is not a provider identity.
* D03, before R07/live acceptance: approve non-production access and the capture,
  privacy/retention policy. Do not place sensitive data in fixtures or logs.
* D04, before R08/R10: choose a supported CSV schema and importer distribution,
  support ownership and release expectations.
* Defer async/concurrent writes, generalized plugin systems, automatic mutation
  retries, fuzzy donor matching and transaction-like rollback of remote gifts.
  They lack a demonstrated need or safe provider contract here. No timeline or
  provider promise is assumed. Revisit priority after each completed initiative.

Implementation readiness and exit gates
---------------------------------------

For each selected initiative, make a focused test-first implementation plan.
Record current behavior protections; separate regression/acceptance tests from
behavior-changing implementation. Name all external contract/data prerequisites;
unavailable access remains an explicit scoped gate. Proposed file names and
interfaces above are design suggestions, not existing implementation evidence.

Each slice must leave the package releasable. Run ``scripts/check.sh`` and
``scripts/check-artifacts.sh`` on the integrated result. For EasyTithe changes,
first run its standalone locked format/lint/ty/pytest/build and installation
checks, publish only with authority, and pin the verified commit in the parent.
Feature acceptance checks supplement the gate: a green baseline alone does not
prove a new feature. Use approved provider captures for adapter contracts and
explicitly approved generated cases where needed; existing synthetic tests are
local regression evidence, not proof of live-service compatibility.

Keep security, cleanup, logging and uncertainty handling in the first slice that
introduces the behavior. Retain public raw APIs unless an approved migration
changes them. Stage changes for review, document compatibility and rollback,
and update this roadmap with observed evidence rather than intended completion.

Version history
---------------

Scope amendment and implementation evidence (2026-10-03): the operator approved
the recommended financial/recovery policy, synthetic cases, optional installed
CLI and forms workflow. EasyTithe account-dependent work is withdrawn. R02/R08
now use offline contributions-v1 CSV preview and read-only Breeze planning/export;
R07 verifies Breeze only; R10 packages the parent-owned CLI with optional dotenv.
CSV/JSON Lines exports preserve vendor records in versioned envelopes for future
consumers. Historical proposals above remain design context where superseded.

Local R01-R10 slices are implemented, including immutable complete planning,
explicit donor/candidate decisions, exact policy validation, durable SQLite
recovery, bounded people traversal, additive models, forms/fields and installed
operator commands. Current acceptance evidence and limitations are maintained in
roadmap-implementation.rst; current operating/schema guidance is data-exchange.rst
and operations.rst. Private credentials remain pending. Passing offline gates
cannot establish authenticated compatibility, transaction idempotency or remote
exactly-once behavior. The parent retains published child 29321b1; no unpublished
EasyTithe pin or account is needed.

* 1.1.0 (2026-10-03): approved scope amendment and local implementation recorded;
  provider acceptance remains explicit.
* 1.0.0 (2026-10-03): reviewed current code and verification; proposed ten
  prioritized initiatives with evidence, dependencies, acceptance and design
  constraints. No application behavior changed.
