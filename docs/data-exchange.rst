Provider-independent data exchange
===================================

The supported operator workflow has no EasyTithe dependency. Consumers can use
the installed API or UTF-8 CSV/JSON Lines artifacts. Formats are explicitly
versioned application schemas, not claims of a universal church-data standard.
JSON uses standard JSON values; CSV uses the stdlib CSV reader/writer with
quoting and CRLF record separators. Dates and monetary values have explicit rules.

Installation and credentials
----------------------------

Install the ``operator`` extra to read dotenv files::

    uv pip install '.[operator]'

For development, run ``uv sync --locked --group dev --extra operator``. A public package or
remote clone does not yet contain these local changes. CLI help and offline
preview work with the base wheel; the extra provides python-dotenv support.

Populate the ignored private ``.env`` with BREEZE_URL and BREEZE_API_KEY using
``.env.example`` as the field reference. BREEZE_URL is the HTTPS account
subdomain, without an API path. Use an owned regular file with permissions 600; symlinks and pipes are rejected. ``breeze --env-file PATH``
selects another private file. Existing environment values take precedence.
Loading does not execute shell code, interpolate values, or mutate the environment.
Help/offline preview require no credentials. Never commit credential files.

Breeze exports -- breeze-export-v1
-----------------------------------

Supported datasets are people, funds, contributions, forms and form_fields::

    breeze export people --details --format jsonl --output .breeze-runs/people.jsonl
    breeze export funds --format csv --output .breeze-runs/funds.csv
    breeze export contributions --start 2026-10-01 --end 2026-10-03 --output .breeze-runs/gifts.jsonl
    breeze export forms --output .breeze-runs/forms.jsonl
    breeze export form_fields --form-id FORM_ID --output .breeze-runs/fields.jsonl

Each JSON line is an object with ``schema`` (breeze-export-v1), ``dataset``, and
``record`` (one decoded provider object). CSV has the exact header
``schema,dataset,record_json``; the last cell is the same object encoded as JSON.
Parse CSV with a CSV library, then parse record_json as JSON. Nested vendor fields
and unknown additions remain available; the exporter does not guess a financial
mapping or silently flatten data. It preserves decoded API values, not original
wire formatting or an independent monetary-precision guarantee. People exports
retain raw fields; ``--details`` requests vendor details. Offset paging is not a
snapshot of concurrently changing people. Other collection endpoints have byte
bounds but no inferred pagination or completeness guarantee beyond their response.

Files are private and atomically published after successful traversal. Destinations
must not already exist. A failed/repeated page or item/byte limit leaves no final
output. Exports default to 100000 items and 64 MiB; library callers may set finite
positive integer limits. Financial exports require an explicit inclusive ISO
date window. No export command writes to Breeze or changes provider settings.

Contribution interchange -- contributions-v1
---------------------------------------------

This source schema is provider independent and directly usable by import adapters.
Its exact header, in order, is::

    schema,date,amount,currency,fund,donor_id,donor_name,transaction_id,method

Every row declares schema contributions-v1. Date is YYYY-MM-DD. Amount is a plain
nonnegative decimal string, never an exponent, currency symbol or float. Currency
is an explicit uppercase three-letter code. Fund is the source key mapped by
operator policy to a Breeze fund ID. Donor IDs/names and transaction_id may be
empty; unresolved donors require review. Method must be explicitly supplied;
no adapter assumes every gift is a card payment. CSV supports UTF-8/BOM, quoting,
commas and multiline text. Input defaults to 16 MiB and 100000 rows; any malformed
or excessive input fails before apply. Monetary representations are locally
bounded to 1000 digits. No rounding or currency conversion is performed.

The synthetic example and policy in examples/ demonstrate the format. The example
USD/precision values describe only that invented data; configure the actual
source/account currency, precision, inclusive window and fund mappings per run.
An EasyTithe or other consumer/producer can implement the small ContributionSource
boundary and produce these records. Website login and export retrieval belong to
that adapter, not matching/recovery policy. No EasyTithe account is used here.

Preview, plan, review and apply
-------------------------------

Report-only preview is entirely offline::

    breeze preview --source examples/contributions-v1.csv --policy examples/import-policy.json

Read-only planning validates all source rows first, verifies account currency and
mapped funds, consumes
the complete bounded people traversal, and checks duplicate candidates::

    breeze plan --source SOURCE.csv --policy POLICY.json --output .breeze-runs/plan.json

Unique literal case-insensitive donor matches can create. Ambiguous/unmatched
donors and possible duplicates require explicit review. Equal-value gifts remain
distinct rows; neither PersonID nor uid proves transaction identity. Even a
provided transaction_id is preserved without claiming verified idempotency.

Supply a JSON decisions object keyed by canonical one-based source row (1, 2,
etc.); repeated keys and alternate spellings such as 01 are rejected. For example
``{"2":{"action":"create","person_id":"BREEZE_PERSON_ID"}}`` or
``{"3":{"action":"create","anonymous":true}}`` or
``{"4":{"action":"skip"}}``. Re-run plan with ``--decisions FILE`` and a new
output path. Anonymous writes omit name/uid so server matching cannot silently
override the decision. Summaries contain counts and the immutable plan digest.
Source/plan artifacts contain records and must remain private.

Apply requires the original unchanged source, a fully resolved plan, the same
account, declared retention and confirmation of the exact reviewed digest::

    breeze apply --source SOURCE.csv --plan .breeze-runs/plan.json --journal .breeze-runs/run.sqlite --retention-days DAYS --confirm-plan PLAN_DIGEST

No remote apply is executed by development verification. Before dispatch, pending
account currency, funds and donor IDs are checked again. Use the same journal on restart. Single
writer ownership is enforced per journal; deployment still requires one coordinated
account worker. Never substitute a fresh journal to bypass uncertain progress.
POSIX local filesystems are required for operator atomic output and writer locks;
network filesystems and multi-process account coordination are not supported.

Recovery, retention and exits
------------------------------

Submission commits before the remote call; acknowledgement commits only after a
valid receipt. Any interrupted submission becomes uncertain on restart. No
uncertain row is automatically resent. Explicit reconciliation records an audit
event and either a verified receipt, verified absence, or operator skip::

    breeze journal-status --journal .breeze-runs/run.sqlite --output .breeze-runs/recovery.jsonl
    breeze reconcile --plan .breeze-runs/plan.json --journal .breeze-runs/run.sqlite --retention-days DAYS --row ROW --decision received --receipt RECEIPT --confirm-plan PLAN_DIGEST

Use ``not_applied`` only after verifying absence, or ``skip`` to prevent resend.
Recovery-only contexts cannot dispatch. Journal records contain minimal local
identities/receipts and audit states, not gift bodies. Expiry is checked before each submission and stops further apply;
read-only inspection/export and explicit reconciliation remain available. Retention
does not silently delete files or reset ledger state. After resolving uncertainty,
archive or remove artifacts under the operator's approved retention procedure.
Keep recovery evidence when rolling back code; code rollback cannot reverse gifts.
Cross-export deduplication remains unverified until provider identity evidence exists.

Exit 0 means the requested command succeeded, 1 a configuration/read/validation
failure, 2 an invalid invocation, 3 unresolved plan refusal, and 4 failed
apply requiring journal inspection. Process interrupts keep their normal signal
exit behavior and also require journal inspection before another attempt. A failure exit does not mean zero prior
writes. Errors omit raw chained exceptions and record values; summaries use
counts. Default tests are offline. The explicit ``--live-provider`` pytest option
enables only read probes using the populated .env; response data is not saved or
printed. Authenticated compatibility remains pending those probes.

Standards references
--------------------

`Python 3.14 CSV documentation <https://docs.python.org/3.14/library/csv.html>`_,
`Breeze published forms/pagination contracts <https://app.breezechms.com/api>`_,
and `SQLite atomic commit documentation <https://www.sqlite.org/atomiccommit.html>`_
inform the local boundaries. Provider contracts and financial receipt behavior
still require authenticated evidence; these references do not prove live acceptance.
