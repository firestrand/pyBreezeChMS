Provider compatibility checks and evidence
==========================================

The operator approved synthetic tests and read-only Breeze checks on their
account. Configure BREEZE_URL and BREEZE_API_KEY in the private ignored .env;
ambient environment values take precedence. Credentials have not yet been
supplied, so authenticated verification remains pending. No EasyTithe account
or capture is required by the amended scope.

Default CI is offline. The live_provider marker is skipped before credentials
are read unless explicitly enabled::

    uv run --locked pytest --live-provider -q --tb=no tests/live/test_provider_contracts.py

The probe reads account summary, two people pages of at most two records each,
forms and funds. It uses real pacing and no writes. Responses are neither printed
nor saved. It checks basic shapes and repeated identifiers, not complete account
traversal or snapshot consistency. Never enable pytest local-variable dumps or
verbose transport recording on a real account. Failures are compatibility signals;
they do not enable retries or authorize configuration changes.

Offline serialization, malformed response, export and recovery tests use synthetic
records. The published Breeze API reference at https://app.breezechms.com/api
supports the new forms/fields parameters. Synthetic fixtures and documentation
are not authenticated service evidence. Quota/status/redirect behavior, giving
receipts, reconciliation and provider transaction identities remain unverified.

Capture approval and refresh
----------------------------

Account access does not authorize adding real provider data to fixtures. Before
any capture, approve test-only records, collection procedure, retained fields,
private storage, deletion date and reviewer. Never capture production records
and rely on later redaction. Retain only the smallest approved response needed;
remove credentials, cookies, headers, request URLs and identifying values.

Approved fixtures require adjacent provenance: provider/endpoint, nonsensitive
parameters, capture date, provider/schema version (or unknown), account type,
approval reference, redactions, reviewer, retention date and consuming regression.
Synthetic fixtures keep that designation. Update fixtures/tests together after
an observed contract change, provider notice, material dependency update or
retention expiry. This document creates no recurring schedule.

Local gates
-----------

Run scripts/check.sh and scripts/check-artifacts.sh for core format/lint/types,
offline tests, dependency audit, builds and outside-checkout wheel/sdist CLI
checks. EasyTithe is optional historical code and does not gate these checks.
Package publishing and live mutations require their own explicit authorization.
