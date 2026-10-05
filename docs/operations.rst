Operator workflow and rollback
==============================

The supported workflow is documented in data-exchange.rst. Start with offline
preview, then read-only planning/export. Review every unresolved/candidate row
and the complete private plan before explicitly confirming apply. Account URL
and API key belong in the ignored mode-600 .env described by .env.example.

Reuse the same source, plan and journal after interruption. Inspect journal-status
and export its audit before recovery. Never start a fresh journal to bypass an
uncertain write. Reconcile received/not_applied/skip only after checking Breeze.
Retention expiry stops dispatch but preserves read-only inspection and recovery;
it never erases uncertainty or extends retention automatically.

Rollback preserves private artifacts and the active worktree. Install the prior
library release in a separate environment for prior read-only API consumers.
Older releases cannot consume the new versioned importer journal; use this
version's journal-status/audit export and resolve uncertain rows before retiring
an import deployment. Do not downgrade and replay gifts through the legacy sample.
Clean wheel/sdist installations exercise the current CLI outside this checkout.

The optional historical EasyTithe sample retains the published submodule revision
29321b1. It is excluded from supported core installation and gates. Local prior
experimental child commits remain in the child's main branch for history; the
parent does not depend on them. No EasyTithe account verification, child publishing
or account-dependent configuration change is required by the approved scope.
