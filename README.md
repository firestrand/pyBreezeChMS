PyBreezeChMS
=================

Python interface to BreezeChMS REST API https://www.breezechms.com

[![CI](https://github.com/firestrand/pyBreezeChMS/actions/workflows/ci.yml/badge.svg)](https://github.com/firestrand/pyBreezeChMS/actions/workflows/ci.yml)

## Installation

Requires Python 3.14; development and CI use Python 3.14.8 and uv 0.12.22.
Install this fork with its declared Requests dependency:

```sh
uv pip install 'git+https://github.com/firestrand/pyBreezeChMS.git@main'
```

## Getting Started

Set `BREEZE_API_KEY` in your environment, then use a context manager:

```python
import os
from breeze import breeze

with breeze.BreezeApi(
    breeze_url="https://your-subdomain.breezechms.com",
    api_key=os.environ["BREEZE_API_KEY"],
) as client:
    people = client.get_people()
```

The client owns its default session. Injected connections stay caller-owned
and must implement the `HttpConnection` protocol, including streaming responses.
Requests share 3.5-second account pacing within one process, use verified TLS,
a 60-second inactivity timeout and per-request elapsed budget, no redirects or
retries, and a 16 MiB response limit (`max_response_bytes` is configurable).
Paginate large result sets. `dry_run=True` returns `None` without making Breeze
requests, including contribution operations. HTTP failures, malformed responses,
and API errors raise `BreezeError` with sanitized messages and chained causes.
The elapsed budget is checked before dispatch, after return, during streaming,
and after decoding. Requests cannot forcibly interrupt a blocked synchronous
call or DNS lookup; this is budget enforcement, not instantaneous cancellation.
`RateLimiter` can be explicitly injected and shared; the default in-process
registry retains at most 128 account hosts, with no credentials, and fails
rather than resetting a quota window when full. Independent processes must use
one coordinated account worker. `request_timeout` and `operation_timeout` are
finite positive constructor options. Specific transport/deadline, HTTP,
authentication, rate-limit and response errors remain subclasses of BreezeError.
Debug diagnostics contain one event per non-dry-run operation: a fixed outcome
category, count and elapsed seconds, including pacing time. Validation failures
before dispatch are operations, not HTTP attempts. No request values or exception
text are included; debug logging remains off unless the caller enables it.

`iter_people` yields validated Person records with page/item bounds, raising on
partial traversal rather than claiming completion. Offset traversal is not a
snapshot of changing data. `add_allocated_contribution` accepts FundAllocation
records containing exact Decimal amounts, computes the total without rounding,
and preserves raw contribution methods. Allocations are bounded to 1000 entries
and 1000 representation digits per amount; account currency and precision remain
caller policy.

Query values are encoded individually. Endpoint constants are now `StrEnum`
values that continue to work as strings. The legacy `make_enum` utility remains
available but no longer mutates caller-owned method mappings.

Version 2.0 drops Python 2 and older Python 3 versions. URLs must be HTTPS Breeze
subdomains without credentials, paths, or query strings. Supported Requests
versions are `>=2.34.2,<3`; the lock records all exact development versions.

## Development and verification

```sh
git clone https://github.com/firestrand/pyBreezeChMS.git
cd pyBreezeChMS
uv sync --locked --group dev --extra operator
scripts/check.sh
scripts/check-artifacts.sh
```

The shared gate checks formatting, lint, types, offline tests, dependency
vulnerabilities, and wheel/sdist builds. Artifact checks install the core distribution
in a clean environment outside the checkout. The standards audit and migration
notes are in [docs/maintenance.rst](docs/maintenance.rst).
Opt-in read-only provider checks and capture requirements are documented in
[docs/provider-contracts.rst](docs/provider-contracts.rst). Default CI stays offline.
The supported workflow and schemas are in [docs/data-exchange.rst](docs/data-exchange.rst).

## Data exchange and reviewed imports

The installed `breeze` CLI provides provider-independent contribution CSV input,
offline preview, read-only planning, explicit reviewed apply, durable SQLite
recovery, and versioned CSV/JSON Lines exports. No EasyTithe account, package,
submodule, or dev tools are needed by installed workflows.

For this unreleased worktree, install `.[operator]` or use the development sync
above. Populate the ignored `.env` with `BREEZE_URL` and `BREEZE_API_KEY`, using
[.env.example](.env.example) as the field reference. Offline preview needs neither:

```sh
uv run --locked breeze preview \
  --source examples/contributions-v1.csv --policy examples/import-policy.json
uv run --locked breeze export people --details --output .breeze-runs/people.jsonl
```

Currency/precision, fund mappings, date windows and journal retention are explicit
run inputs. Ambiguous/unmatched donors and possible duplicates require review;
unresolved plans cannot apply. Confirm the exact plan digest before writes. Any
uncertain submission requires reconciliation, never automatic replay. Outputs
are private and complete-only. See the data-exchange guide for schemas, exits,
recovery and adapter boundaries. Public releases do not yet include these changes.

The previous EasyTithe sample/submodule remain historical optional code. They
are excluded from core verification and have not been live-verified. New adapters
should produce the common contribution records and reuse planning/recovery.

## How do I make a contribution?
Never made an open source contribution before? Wondering how contributions work in the in our project? Here's a quick rundown!

1. Find an issue that you are interested in addressing or a feature that you would like to add.
2. Fork the repository associated with the issue to your local GitHub organization. This means that you will have a copy of the repository under `your-GitHub-username/pyBreezeChMS`.
3. Clone the repository to your local machine using git clone https://github.com/github-username/pyBreezeChMS.git.
4. Create a new branch for your fix using `git checkout -b branch-name-here`.
5. Make the appropriate changes for the issue you are trying to address or the feature that you want to add.
6. Use `git add insert-paths-of-changed-files-here` to add the file contents of the changed files to the "snapshot" git uses to manage the state of the project, also known as the index.
7. Use `git commit -m "Insert a short message of the changes made here"` to store the contents of the index with a descriptive message.
8. Push the changes to the remote repository using `git push origin branch-name-here`.
9. Submit a pull request to the upstream repository.
10. Title the pull request with a short description of the changes made and the issue or bug number associated with your change. For example, you can title an issue like so "Added more log outputting to resolve #4352".
11. In the description of the pull request, explain the changes that you made, any issues you think exist with the pull request you made, and any questions you have for the maintainer. It's OK if your pull request is not perfect (no pull request is), the reviewer will be able to help you fix any problems and improve it!
12. Wait for the pull request to be reviewed by a maintainer.
13. Make changes to the pull request if the reviewing maintainer recommends them.
14. Celebrate your success after your pull request is merged!

## License

Code released under the [Apache 2.0](https://github.com/firestrand/pyBreezeChMS/blob/main/LICENSE) license.
