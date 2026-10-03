Maintenance acceptance spec (GOTCHA)
===================================

Goals and objectives
--------------------
Merge all upstream commits, adopt the latest stable Python and dependencies,
correct gaps against Python Code Standards revision 2026-09-29, and push the
verified result to the fork's main branch.

Tasks and capabilities
----------------------
Fetch and inspect upstream; modernize package metadata and locked verification;
fix client boundaries and type public APIs; review the entire owned codebase;
build and test installed artifacts; commit and push. Preserve existing untracked
user files. Never use live church data or credentials in verification.

Health and constraints
----------------------
Use deterministic offline tests, bounded HTTP reads and timeouts, no automatic
retries for state-changing GET endpoints, and no redirects carrying API keys.
Keep current endpoint names and ordinary response contracts. Python 3.14.8 is
the runtime; Python 3.14 is the supported minor. Requests remains the transport.
There is no service deployment or package publication in this task.

Users, runtime, beliefs and intentions
-------------------------------------
Library callers retain responsibility for pagination and injected sessions.
Each client owns its default session and provides explicit cleanup. Tests use
synthetic records and exercise failures without external requests. The fork
starts on master, upstream is eight commits ahead, and main does not exist.
The legacy EasyTithe dependency was Python 2-only. The operator requested its
complete replacement in an owned submodule; automated report downloads remain.


Standards audit and hardness report (ATLAS)
==========================================

Scope and sources
-----------------
All owned Python source, tests, sample code, dependency metadata, packaging,
README files and CI were reviewed against Python Code Standards revision
2026-09-29 from /home/firestrand/Dropbox/Projects/Software-Standards/.
No project-specific coding guide was present. Graphify and Context7 were not
available; live Serena symbols, rg, installed packages, and official Requests,
Astral, PyPI and Python.org documentation supplied evidence. The independent
EasyTithe fork retains upstream history and replaces the Python 2 implementation.

Findings resolved, ordered by impact
-----------------------------------

* Security/dependency trust and sections 9-10: Breeze URL validation accepted
  non-Breeze hosts, query values could inject parameters, redirects could carry
  the API key, and debug logging exposed personal and financial payloads.
  HTTPS host validation, individual percent encoding, rejected redirects,
  bounded reads/URLs, sanitized errors and named loggers resolve these gaps.
  The sample suppresses transport debug logs and uses environment credentials.
* Sections 3, 9 and packaging: the default session was shared at import time,
  and HTTP/transport/JSON failures and cleanup were incomplete. Each client now
  owns a session and supports close/context managers. Injected Breeze transports
  remain caller-owned. Response streams close in finally/context managers.
* Sections 14 and 16: all public library/sample boundaries are now typed, JSON
  is validated before typed exposure, malformed write payloads fail locally,
  and financial rows validate dates and finite nonnegative amounts. Dry-run
  contribution calls now return None instead of indexing an absent response.
* Baseline, sections 1-2 and packaging: Python 2/3.6 Travis and setup.py test were
  replaced with Python 3.14 metadata, exact tool versions, uv locks, a shared
  gate, read-only CI permissions, SHA-pinned actions, and artifact installation
  outside the checkout. Coveralls is replaced by pytest-cov reports.
* Sections 7-8 and security: the importer uses real JSON serialization for fund
  names and amounts. Name matching treats names as literal data and rejects
  ambiguous matches. The EasyTithe submodule has no Python 2 imports or code.

Coverage by applicable rule group
--------------------------------

* PASS -- Runtime/tooling (baseline, 1-2): requires-python >=3.14,<3.15;
  .python-version and CI 3.14.8; uv 0.12.22; locked lint/type/test tools.
* PASS -- Mutation/API/collections (3-6): caller mappings remain unchanged;
  each session has one owner; iterable and mapping boundaries are typed;
  collection materialization is bounded by the response limit.
* PASS -- Strings/I/O (7-8): encoded query values, json.dumps fund payloads,
  bounded streaming response reads, explicit UTF-8 decoding and pathlib in
  test/artifact paths. Export reports are bounded in memory for CSV parsing.
* PASS -- Errors/logging (9-10): narrow translated transport/parse failures,
  chained causes, no automatic retries, deterministic cleanup, no secret or
  record payloads in application logs.
* N/A -- Threads, async, numerical acceleration (11-13): sequential clients;
  no concurrent task, process, database or vectorized workload exists.
* PASS -- Types/control flow/tests (14-16): ty checks source, sample, adapter and
  tests; offline boundary and importer tests accompany the original endpoint
  tests. Runtime JSON and payment shapes are validated.
* PASS -- Performance (17-18): the name-matching change was measured against
  the old regex/list approach on the same synthetic workload (details below).
  No end-to-end service latency claim is made.
* PASS -- Agent/dependency/security: source/lock provenance checked against
  PyPI, all resolved registry versions match their latest releases, and the
  scanner found no known vulnerabilities. Credentials and real data were never
  used. Both new and existing dependencies come from PyPI or the owned Git
  submodule; Requests, setuptools, pytest, Ruff, ty and the audit tools are
  established upstream packages with compatible open-source licenses.
* PASS -- Packaging: both packages build wheel/sdist artifacts and install in
  a fresh Python 3.14.8 environment outside the checkout. Breeze includes
  py.typed. Requires-python limits support to the tested minor; Requests' floor
  is the current locked version, also used by clean artifact installations.
* PASS -- Exceptions/review (19): no MUST-rule override or global type-checker
  suppression was added. README documents deliberate compatibility changes.
  The replacement EasyTithe adapter uses a typed src layout. The existing Breeze
  flat package layout is retained to keep the migration focused
  (src layout is a SHOULD recommendation).
* N/A -- PR template (20): the requested deliverable is a commit pushed to main.
  CI guidance (21) is implemented in both repositories. No external service,
  database, durable queue, agent application, or deployment exists.

Edge cases and service failures
------------------------------
Tests cover hostile hostnames/credentials, redirects, HTTP errors, timeouts,
connection and stream failures, malformed/invalid/nonfinite JSON, response and
URL limits, payment shape errors, zero values, false all-day flags, dry-run
writes, literal Unicode/query round trips, header isolation, session ownership,
CSRF tokens, login rejection, export permissions, CSV quoting and Unicode,
invalid dates/amounts, duplicate and ambiguous donor matching, and import safety.
No live Breeze or EasyTithe account was contacted. The EasyTithe login/export
contract is based on upstream endpoints; current live service behavior remains
unverified. User-supplied date windows bound exports; no operation is retried.

Verification observed locally
----------------------------
* scripts/check.sh: locked sync, format, lint and ty passed; 115 offline tests
  passed; pip-audit found no known vulnerabilities; both wheel/sdist builds
  succeeded. Coverage: Breeze client 98%, EasyTithe adapter 95%, importer 80%.
* scripts/check-artifacts.sh: both wheels installed and passed import/behavior
  smoke tests outside the source tree; both source distributions independently
  built and installed in the same clean environment.
* Standalone EasyTithe locked format/lint/ty checks passed; its 17 tests passed.
* uv lock --check and git diff --check passed. PyPI JSON metadata comparison
  found no newer registry dependency versions than either lock's resolution.
* Upstream pyBreezeChMS master at 3dc0aa8 was fast-forward merged, preserving
  all eight commits missing from the fork. EasyTithe upstream 22b33b3 was
  inspected before its complete Python 3 replacement. The owned submodule
  commit 29321b1 passed GitHub CI run 37106617336 after standalone layout
  verification identified and corrected a root-package import issue.

Performance evidence
--------------------
CPython 3.14.8, Linux aarch64, five repetitions, 1,000 synthetic people and 200
synthetic contributions, with identical matching results for this workload.
People were named PersonNNNN LastNNNN; the first 200 names were looked up.
Legacy re.search(..., re.IGNORECASE) over every person had median 2.134502 s
(range 2.130764-2.146721), tracemalloc peak 306,184 bytes. Exact casefolded
indexed matching, including index construction, had median 0.000140 s
(range 0.000136-0.000350), peak 147,260 bytes. These synthetic measurements
support the collection choice, not claims about live import throughput.

Compatibility, rollout and residual limits
------------------------------------------
Version 2.0 deliberately drops older Python versions. Errors are sanitized,
endpoint constants use StrEnum, JSON arrays are validated, and custom Breeze
connections must support streaming and response closure. The EasyTithe
replacement runs on Python 3.14 and uses Requests; its credentials are loaded
from runtime environment variables. No credentials are stored in files.

Importing does not provide transactions or rollback: earlier successful writes
remain after a later failure. Duplicate detection retains the legacy
same-person/date/amount heuristic; two distinct gifts with those same values
can be treated as duplicates. Anonymous rows cannot use person-based duplicate
checks. These limitations are documented rather than promising idempotency the
service contract does not provide. Run dry-run and review the report first.
EasyTithe login can update the account's Custom export format, matching the
original adapter; dry-run prevents Breeze writes, not that login configuration.
Neither HTTP client retries mutations. Default response limits may require
pagination or smaller report windows. Roll back code by reverting the migration
commit; previously imported gifts require operator review rather than an
automatic destructive cleanup. Real service behavior requires a separate,
authorized integration check using a non-production account.
