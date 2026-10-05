Decisions needed to implement the remaining roadmap
===================================================

The operator approved all recommendations on 2026-10-03. Currency/precision and
retention are explicit run inputs. Synthetic regression cases are authorized.
Forms/fields are the selected read-only expansion. Breeze account access will be
configured locally through .env. EasyTithe account-dependent work is withdrawn:
the operator has no account and requested a provider-independent interchange and
export path. The old sample/submodule remain historical optional artifacts.
The new supported workflow must install and verify without EasyTithe.

The original proposal follows for traceability; it is not implementation evidence.
The roadmap explicitly requires D01 approval before R03, D03 authorization
before authenticated checks, and D04 schema/support decisions before R08/R10.
The new interchange replaces the EasyTithe-specific primary CSV proposal below.

D01 -- Financial planning policy
--------------------------------

* Require an explicit account currency and permitted decimal precision in the
  run configuration. Do not assume USD, convert currency, or round amounts.
  Retain the existing finite/nonnegative rule; reject amounts that cannot be
  represented exactly at the declared precision.
* Require an operator mapping from each source fund to a Breeze fund identifier.
  No fallback to an unresolved fund name. Require every source date to fall in
  the inclusive declared source window; retain the existing MM/DD/YYYY source
  and YYYY-MM-DD normalized representations.
* Preserve literal case-insensitive unique-name matching as an approved matching
  policy only if accepted. Ambiguous and unmatched donors stay unresolved until
  explicitly mapped or approved as anonymous. No fuzzy or automatic anonymous
  import. PersonID may be used for donor mapping, never transaction identity.
* Treat donor/date/amount matches as duplicate candidates. Each requires an
  explicit create/skip decision; two equal-value gifts remain distinct rows.
  Complete planning and all validation before any write. Apply refuses any
  unresolved row. Summaries contain counts and decision categories, not records.

Approval must state the currency/precision and donor-policy choice, or require
them as explicit per-run operator inputs. Existing anonymous import and automatic
duplicate skipping remain unchanged until a replacement policy is approved.

R04 -- Local journal semantics
------------------------------

Propose stdlib SQLite with one writer and durable transactions for one immutable
snapshot. Identify rows by snapshot digest and ordinal; these are local identities,
not evidence of provider transaction idempotency. Keep equal rows distinct.
Persist submitted before dispatch and acknowledged only after a valid receipt.
On restart, submitted/uncertain rows require operator reconciliation; never
resend automatically, including a crash between submission recording and dispatch.
Corruption or mismatched plan/snapshot stops apply. Reconciliation records an
explicit decision and audit event. Restrict local file access and keep financial
payloads out of the journal. Require an approved retention period before use.
Recovery inspection/export is read-only. Provider identity/reconciliation
evidence is still needed for cross-export guarantees (D02).

D03 -- Verification authorization
---------------------------------

Approve dedicated non-production accounts with test-only records and the capture
review/retention procedure in provider-contracts.rst. Say which providers are
available and supply only environment-variable names or access availability,
never credential values. Separately approve generated synthetic financial/provider
cases for protecting new behavior. Existing fixtures have been reused so far;
they do not establish live compatibility.

D04 -- Source and distribution
-------------------------------

Propose ``easytithe-custom-v1``: explicitly selected, UTF-8/BOM-tolerant,
headerless CSV in the current adapter's eight-field order: Amount, Type, Date,
Fund, Name, Email, Phone, PersonID. Require bounded bytes/rows and normalize only
at the source boundary. Reuse planning and recovery, not a second financial policy.
Other exports require their own approved schema; do not guess a CSV layout.

Propose a parent-owned optional importer CLI, with an explicit EasyTithe version
dependency and plan/preview/apply commands installable outside the checkout.
Support ownership remains with this repository; publishing/version expectations
need agreement. This authorizes neither package publishing nor scheduled imports.

R09 -- Operator workflow
------------------------

Choose form/field discovery before entries, or event attendance inspection.
Implement only the selected read-only slice and example; published parameters
and authorized provider evidence must both support acceptance.
