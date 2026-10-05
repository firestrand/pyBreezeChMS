Roadmap implementation record
=============================

GOTCHA specification
--------------------

Goals: implement R01-R10 from roadmap.rst while preserving raw Breeze APIs,
privacy, deterministic verification and explicit external decision gates.

Objectives: quota-aware requests and classified failures; read-only dry-run;
complete reviewed import plans; durable recovery; bounded people iteration;
shared serialization and validated models; opt-in contract checks; an offline
CSV source; read-only endpoint slices; an installed operator CLI.

Tasks: first establish regression evidence for R01/R02, implement and run their
focused checks, then expand dependency-ready slices. Track every acceptance
criterion against observed evidence. Synthetic fixtures and financial policy were approved by the operator;
live-service verification requires private account configuration.

Capabilities: local source, tests, docs, locked tools and published API docs.
Credentials belong only in private ignored configuration; no provider data in logs. No live mutations, package publishing
or scheduled imports. Preserve existing untracked user-owned files.

Health: there is no explicit time/token budget. No automatic mutation retry.
Use deterministic clocks; finite I/O deadlines and bounded data sizes. Report
blocking decisions narrowly and continue independent work.

Approved scope update -- 2026-10-03
----------------------------------

The operator approved the proposed financial matching/review, exact amount/fund/
date validation, local SQLite recovery, synthetic tests, optional installed CLI
and forms discovery. Currency, decimal precision and retention are required run
inputs. Breeze credentials will be supplied through private .env; no EasyTithe
account is available and no further account-dependent EasyTithe work is required.
Build a provider-independent versioned contribution CSV interchange, plus JSON
Lines/CSV Breeze exports usable by additional consumers. Historical EasyTithe
code remains optional and does not gate the supported installation/workflow.

GOTCHA slice: define immutable contribution/policy/plan records and small source/
gateway boundaries; use UTF-8 CSV with an explicit version, ISO dates, exact
decimal strings and opaque donor/source identities. Plans cover every row and
require reviewed decisions before writes. Source snapshots are bounded and keyed
by digest/ordinal; journal states commit before dispatch and after valid receipt.
Recovery never automatically replays submitted/uncertain rows. One local writer,
private files, explicit retention and sanitized summaries/exits are invariants.
Exports are bounded, read-only and atomically published only when traversal
completes. dotenv reads without shell evaluation and does not override ambient
environment. Live checks are explicitly opted in and never print/save credentials
or raw provider data. Test planner late-row ambiguity, equal gifts, exact precision,
malformed/bounded sources, every journal crash boundary, installed commands and
exports before claiming completion. No live mutation or package publication.

Attributes: preserve error causes internally, sanitize operator output, and
close streams/sessions on failure. No exactly-once or live-compatibility claims
without supporting service evidence.

Constraints/users: Python 3.14 and locked toolchain. One coordinated worker per
account. API consumers and import operators require explicit review/recovery.

Runtime: requests remain synchronous; importer decisions use immutable records;
future persistence records progress, not inferred remote transaction certainty.

Beliefs/intentions: baseline is d91fa92/29321b1, 115 offline tests. Requests uses
an inactivity timeout; a synchronous blocked call cannot be forcibly interrupted
by a Python-level deadline. Add deadline budgeting/checks without pretending it
provides instantaneous cancellation. R01 retries remain disabled until provider
transient/retry contracts have been validated (R07).

Execution status -- approved scope
----------------------------------

* R01: Breeze quota pacing, finite request/deadline/byte bounds, classified
  errors and cleanup implemented. All ten raw mutations have single-attempt
  regressions. Retries remain disabled; real quota/transient contracts unverified.
* R02: offline preview performs no credential reads or provider requests. Plan
  and export use read-only Breeze operations. EasyTithe changes and account
  verification are withdrawn from the supported scope by the operator.
* R03: immutable complete plans, pure planner, unique literal case-insensitive
  names, explicit ambiguous/anonymous/candidate decisions, exact currency/amount/
  date/fund checks and zero-write unresolved refusal implemented. Provider reads
  finish before a plan is returned. Account currency and destination inventory
  are checked before writes; no conversion, rounding or automatic duplicate skip.
* R04: local SQLite journal, durable submission/acknowledgment, crash recovery,
  corruption checks, one writer, explicit reconciliation, private artifacts,
  fixed retention and read-only audit export implemented. No cross-export
  identity or remote exactly-once claim is made. Reuse the original journal.
* R05: bounded raw and typed people iterators detect repeated IDs and failed or
  excessive traversal. Planning consumes the complete index before candidate
  queries; failure prevents a completed plan and therefore apply.
* R06: shared giving serialization, additive people/fund models, exact decimal
  totals, typed malformed receipts and sanitized operation diagnostics preserve
  existing raw API contracts. Diagnostics contain categories/counts/timing only.
* R07: opt-in Breeze-only read probes and capture provenance guidance exist.
  Default tests skip before reading credentials. Authenticated acceptance remains
  pending private configuration; synthetic tests are not provider evidence.
* R08: bounded UTF-8 contributions-v1 CSV source, exact decimal strings, immutable
  digest/ordinal identity and offline preview implemented. Versioned CSV/JSON
  Lines exports preserve decoded vendor records for additional consumers.
* R09: read-only forms and fields endpoints, shared pacing/errors and executable
  counts-only example implemented and verified with synthetic provider I/O.
  Authenticated forms/fields acceptance remains pending R07.
* R10: optional operator dotenv extra, installed preview/plan/apply/export/status/
  reconcile commands, sanitized exits and private recovery artifacts implemented.
  Core packaging/CI require no EasyTithe installation or account. Legacy sample
  tests remain separately archived; parent retains published child 29321b1.

ATLAS hardness report
---------------------

Assumptions: one coordinated account worker on a local POSIX filesystem; the same
source, reviewed plan and journal must be reused on restart. A digest identifies
that snapshot/plan, not a provider transaction or a gift across exports. Currency,
precision, date window, fund IDs and retention are explicit run inputs. Method
is supplied by each source record. Account access does not authorize real writes
or recording production fixtures.

Tests and adversarial cases: final-row ambiguity and failed later people pages;
identical gifts requiring individual decisions; explicit anonymous imports;
nonfinite/negative/excessive amounts and exact trailing-zero preservation;
malformed encoding/header/date/row widths and source byte/row bounds; changed
source/wrong confirmation/unresolved CLI refusals; partial apply failure; private
file modes/no overwrite; late export failure with no published artifact; SQLite
physical/logical corruption and writer exclusion; retention expiry with read-only
recovery; interrupts before/after submission, remote response and acknowledgment.
Hard subprocess exits before a SQLite commit roll back; exits after submission
recover as uncertain without replay and release the kernel writer lock.

Limits and load: requests are synchronous. Socket inactivity limits and elapsed
budget checks cannot forcibly cancel blocked DNS/I/O. Host pacing is shared only
in-process. People offset pagination does not promise an account snapshot.
Giving exports require an explicit date window and use the existing list endpoint;
no undocumented pagination is invented. Source bounds are 16 MiB/100,000 rows;
exports default to 64 MiB/100,000 items. Decoded provider numbers retain the raw
API's Python JSON semantics, not independent exact monetary guarantees. Fund
policy lookup was measured on Python 3.14.8/aarch64 with 500 mappings,
10,000 lookups and seven repetitions. Rebuilding dicts: median 0.066503 s,
range 0.066389-0.066985 s. Cached lookup: median 0.000427 s, range
0.000416-0.000443 s. This isolates lookup strategies, not complete validation or
provider throughput.

Security and recovery: .env and generated artifacts are private, credentials
never enter tracked files, and operator errors omit chained provider values.
SQLite stores minimal progress/receipts/audit, not full gift bodies. Expiry blocks
writes without deleting uncertain evidence; recovery-only reconciliation remains
available. No automatic replay, retention reset or deletion. Archive/remove only
after reconciliation and the operator's retention policy. A receipt persists only
after shape validation; an interrupted write is treated as uncertain.

Observed verification (2026-10-03): scripts/check.sh passed format, Ruff, ty,
242 offline tests (one live probe skipped), dependency audit with no known
vulnerabilities, and wheel/sdist builds. scripts/check-artifacts.sh installed
artifacts outside the checkout: base wheel help/preview/unresolved refusal,
synthetic HTTP plan/apply/resume/export, and journal status/export/reconciliation passed without EasyTithe, dotenv or dev
tools; sdist with the operator extra passed installed help and offline preview.
No live calls, real mutations, package publication or provider captures have
been performed. Private configuration was checked without displaying values and
remains incomplete.

Remaining acceptance
--------------------

Authenticated Breeze response shapes, account currency, forms/fields and actual
quota/error behavior require populated private configuration and opt-in probes.
The bounded probe cannot prove full account traversal, giving write receipts,
transaction identity or reconciliation contracts. No read retry is enabled by
passing the probe. Those limits remain visible; local checks do not mark the full
roadmap accepted. No EasyTithe account or unpublished child pin is required.

Local completion audit -- account checks excluded
-------------------------------------------------

The active objective is to finish changes that do not need Breeze access. The
original roadmap's authenticated acceptance remains a separate follow-up. The
previous turn made implementation/verification progress; this audit continues
from the current worktree. No credentials are read or live probes run here.

.. list-table:: Approved requirements and authoritative local evidence
   :header-rows: 1
   :widths: 8 52 40

   * - ID
     - Verified local requirement and evidence
     - Account-dependent follow-up
   * - R01
     - test_request_policy.py: controlled pacing/deadlines, finite bounds,
       classification, cleanup and all ten single-attempt mutations;
       test_client_boundaries.py protects raw serialization and redirects.
     - Actual quota/transient/Retry-After behavior; retries stay disabled.
   * - R02
     - test_operator_cli.py: preview reads no credentials and makes no requests;
       exporting.py uses read-only selections. Legacy setup work withdrawn.
     - Actual read-only response contracts.
   * - R03
     - test_import_workflow.py and test_operator_boundaries.py: immutable complete
       plans, exact policy checks, unique names, explicit candidate/anonymous
       decisions, consistent action/reason, stale destination refusal.
     - Account metadata, giving lookup/filter and receipt contracts.
   * - R04
     - test_journal.py: each interrupt boundary, hard subprocess exits, restart,
       corruption, ownership, identical gifts and read-only recovery. Boundary
       tests cover expiry during a run, invalid receipts and audited decisions.
     - Remote reconciliation and cross-export transaction identity.
   * - R05
     - test_people_iterator.py: page boundaries, repeat/failure/limit refusal,
       mixed numeric/text repeated IDs. Planner consumes the complete index.
     - Actual pagination semantics and account changes during traversal.
   * - R06
     - breeze_test.py, test_typed_funds.py, test_request_policy.py protect raw
       contracts, exact structured funds, malformed/empty receipts and private
       diagnostics. Direct typed models validate runtime input.
     - Provider shape acceptance beyond the published/local contracts.
   * - R07
     - conftest.py skips the live marker before configuration reads; opt-in probe
       and provider-contracts.rst specify bounded reads and capture safeguards.
     - Run the probe after configuration; no capture or mutation authorized.
   * - R08
     - test_interchange.py: version/header, UTF-8/BOM/quoting, exact records,
       malformed/byte/row refusal, plan roundtrip and complete-only exports.
       Boundary tests reject repeated JSON keys and aliased review ordinals.
     - Matching actual source/provider data without recording real fixtures.
   * - R09
     - test_forms.py: success/empty/error, shared pacing, encoding and executable
       counts-only forms/fields/entries example.
     - Authenticated forms/fields parameters and shapes.
   * - R10
     - check-artifacts.sh verifies base wheel CLI including synthetic HTTP
       plan/apply/resume/export and recovery, without dev tools or dotenv;
       sdist installs operator extra. CLI regressions prove safe exits/privacy.
       operations.rst documents artifact-preserving rollback and retention.
     - Real operator use after read-only compatibility checks; no publishing.

Standards audit: Python Code Standards revision 2026-09-29, sections 1, 3-10,
14, 16-17, Security and Dependency Trust, and Packaging and Project Boundaries.
Toolchain/types/contracts/input bounds/ownership/cleanup/privacy/testing/packaging
PASS locally with the evidence above and the final gates. Domain records use
frozen dataclasses; source and gateway ports stay narrow. String paths normalize
to Path at new file boundaries. Cancellation propagates after conservative
journal handling. Translated exceptions retain internal causes; CLI output hides
them. Async/model-selected tools N/A. Provider-contract acceptance UNVERIFIED and
explicitly excluded from this objective.

Dependency review: optional python-dotenv 1.2.4 is from PyPI with hashed artifacts
in uv.lock, no added transitive dependencies, BSD-3-Clause installed license and
an active 2026-10-01 upstream release. Its maintained parser avoids inventing a
shell-like credential parser; interpolation and global mutation are disabled.
Primary references: https://pypi.org/project/python-dotenv/ and
https://bbc2.github.io/python-dotenv/. requests remains the existing Apache-2.0
transport dependency. Generated wheel/sdist inventories exclude .env and local
run-state files. .serena and legacy submodule history remain user-owned/preserved.

Final local verification: scripts/check.sh passed with 242 tests, one deliberately
skipped live probe, 90% aggregate statement coverage, no known dependency
vulnerabilities and both builds. scripts/check-artifacts.sh passed installed
synthetic plan/apply/resume/export and recovery plus sdist operator installation.
git diff --check passed. No required local item remains open; the account-dependent
items in the table remain outside this goal. The next authorized account step is
the bounded read-only opt-in probe after the operator supplies configuration.
