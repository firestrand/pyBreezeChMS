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
    breeze_url="https://your_subdomain.breezechms.com",
    api_key=os.environ["BREEZE_API_KEY"],
) as client:
    people = client.get_people()
```

The client owns its default session. Injected connections stay caller-owned
and must implement the `HttpConnection` protocol, including streaming responses.
Requests use verified TLS, a 60-second inactivity timeout, no redirects or
retries, and a 16 MiB response limit (`max_response_bytes` is configurable).
Paginate large result sets. `dry_run=True` returns `None` without making Breeze
requests, including contribution operations. HTTP failures, malformed responses,
and API errors raise `BreezeError` with sanitized messages and chained causes.
Query values are encoded individually. Endpoint constants are now `StrEnum`
values that continue to work as strings. The legacy `make_enum` utility remains
available but no longer mutates caller-owned method mappings.

Version 2.0 drops Python 2 and older Python 3 versions. URLs must be HTTPS Breeze
subdomains without credentials, paths, or query strings. Supported Requests
versions are `>=2.34.2,<3`; the lock records all exact development versions.

## Development and verification

```sh
git clone --recurse-submodules https://github.com/firestrand/pyBreezeChMS.git
cd pyBreezeChMS
uv sync --locked --group dev
scripts/check.sh
scripts/check-artifacts.sh
```

The shared gate checks formatting, lint, types, offline tests, dependency
vulnerabilities, and wheel/sdist builds. Artifact checks install both distributions
in a clean environment outside the checkout. The standards audit and migration
notes are in [docs/maintenance.rst](docs/maintenance.rst).

## EasyTithe importer

The `samples/easytithe` Git submodule is the Python 3.14 replacement maintained at
[firestrand/easytithe](https://github.com/firestrand/easytithe). Its original
login/export HTTP contract is verified with offline fixtures; live service
availability has not been checked. Logging in configures the account's Custom
export format when needed, matching the original adapter's behavior.

Set `EASYTITHE_USERNAME`, `EASYTITHE_PASSWORD`, and `BREEZE_API_KEY` in the runtime
environment, then run:

```sh
uv run --locked python samples/easytithe_importer.py \
  --breeze_url https://your_subdomain.breezechms.com \
  --start_date 10/01/2026 --end_date 10/03/2026 --dry_run
```

Remove `--dry_run` to import. Dry-run downloads and validates the report but makes
no Breeze requests. The importer matches exact case-insensitive names, skips
existing contributions for matching people, rejects ambiguous names, and imports
unmatched rows anonymously. Secrets and individual records are excluded from
logs. CLI credentials have been replaced by environment variables. Financial
records are validated before the first write. Review matches and date ranges
before importing; anonymous records do not have a stable person ID for duplicate
checks. Duplicate detection preserves the original same-person/date/amount
heuristic; distinct gifts with those same values may be skipped. Importing is sequential and does not roll back earlier successful writes
if a later record fails. No automatic retry is performed.

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
