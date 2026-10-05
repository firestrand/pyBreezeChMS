#!/usr/bin/env bash
# Install and exercise the published wheel outside the source checkout.
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
artifact_dir="$(mktemp -d)"
trap 'rm -rf -- "$artifact_dir"' EXIT
uv venv --python 3.14.8 "$artifact_dir/venv"
wheels=("$repo_dir"/dist/*.whl)
uv pip install --python "$artifact_dir/venv/bin/python" "${wheels[0]}"
cd "$artifact_dir"
"$artifact_dir/venv/bin/python" - <<'PY'
from importlib.metadata import version
from pathlib import Path
import breeze
import csv
import json
import subprocess
import importlib.util
from breeze.breeze import BreezeApi

assert version('pyBreezeChMS') == '2.0.0'
assert Path(breeze.__file__).with_name('py.typed').is_file()
with BreezeApi('https://demo.breezechms.com', 'synthetic-key', dry_run=True) as client:
    assert client.get_people() is None
    assert client.add_contribution() is None
assert importlib.util.find_spec('easytithe') is None
assert importlib.util.find_spec('dotenv') is None
from breeze.interchange import COLUMNS
with Path('source.csv').open('w', newline='', encoding='utf-8') as stream:
    writer = csv.writer(stream)
    writer.writerow(COLUMNS)
    writer.writerow(('contributions-v1', '2026-10-01', '12.34', 'USD', 'general', 'donor', 'Test Donor', '', 'Cash'))
Path('policy.json').write_text(json.dumps({'currency':'USD','precision':2,'start':'2026-10-01','end':'2026-10-03','funds':{'general':'5'}}))
# sys.executable locates the artifact venv independently of package layout.
import sys
executable = Path(sys.executable).with_name('breeze')
subprocess.run([str(executable), '--help'], check=True, capture_output=True)
result = subprocess.run([str(executable), 'preview', '--source', 'source.csv', '--policy', 'policy.json'], check=True, capture_output=True, text=True)
assert json.loads(result.stdout)['summary'] == {'create':0,'skip':0,'unresolved':1}
from breeze.importing import plan_import
from breeze.cli import load_policy
from breeze.interchange import CsvContributionSource, save_plan
from breeze.journal import Journal
# Installed recovery commands operate on private synthetic state without dev tools.
plan = plan_import(CsvContributionSource(Path('source.csv')).load(), load_policy(Path('policy.json')), None)
save_plan(Path('unresolved.json'), plan)
refusal = subprocess.run([str(executable), 'apply', '--source', 'source.csv', '--plan', 'unresolved.json', '--journal', 'runs/run.sqlite', '--retention-days', '30', '--confirm-plan', plan.digest], capture_output=True)
assert refusal.returncode == 3
with Journal(Path('runs/run.sqlite'), plan, retention_days=30) as journal:
    journal.submit(1)
result = subprocess.run([str(executable), 'journal-status', '--journal', 'runs/run.sqlite', '--output', 'recovery.jsonl'], check=True, capture_output=True, text=True)
assert json.loads(result.stdout) == {'submitted': 1}
assert '12.34' not in Path('recovery.jsonl').read_text()
with Journal(Path('runs/run.sqlite'), plan, retention_days=30) as journal:
    assert journal.states() == {1: 'uncertain'}
result = subprocess.run([str(executable), 'reconcile', '--plan', 'unresolved.json', '--journal', 'runs/run.sqlite', '--retention-days', '30', '--row', '1', '--decision', 'skip', '--confirm-plan', plan.digest], check=True, capture_output=True, text=True)
assert json.loads(result.stdout) == {'skipped': 1}
# Exercise installed planning/apply/export wiring with synthetic HTTP responses.
# All Session.send calls are intercepted; no account or network is used.
import io
import os
from contextlib import redirect_stdout
from unittest.mock import patch
from urllib.parse import urlsplit
import requests
from breeze import cli
from breeze.interchange import load_plan
from breeze.policy import RateLimiter
writes = []
def fake_send(request, **kwargs):
    path = urlsplit(request.url).path
    payloads = {
        '/api/account/summary': {'details': {'country': {'currency': 'USD'}}},
        '/api/people/': [{'id': '1', 'first_name': 'Test', 'last_name': 'Donor', 'details': {'custom': 'synthetic'}}],
        '/api/funds/list': [{'id': '5'}],
        '/api/giving/list': [],
    }
    if path == '/api/giving/add':
        writes.append(path)
        payload = {'payment_id': 'synthetic-receipt'}
    else:
        assert path in payloads, 'Unexpected offline artifact endpoint'
        payload = payloads[path]
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps(payload).encode()
    response._content_consumed = True
    return response
with patch.dict(os.environ, BREEZE_URL='https://demo.breezechms.com', BREEZE_API_KEY='synthetic-key'), patch.object(requests.Session, 'send', side_effect=fake_send), patch('breeze.breeze.account_limiter', return_value=RateLimiter(interval=0)), redirect_stdout(io.StringIO()) as output:
    assert cli.main(['plan', '--source', 'source.csv', '--policy', 'policy.json', '--output', 'reviewed.json']) == 0
    reviewed = load_plan('reviewed.json')
    arguments = ['apply', '--source', 'source.csv', '--plan', 'reviewed.json', '--journal', 'runs/reviewed.sqlite', '--retention-days', '30', '--confirm-plan', reviewed.digest]
    assert cli.main(arguments) == 0
    assert cli.main(arguments) == 0
    assert len(writes) == 1
    assert cli.main(['export', 'people', '--details', '--output', 'people.jsonl']) == 0
assert 'Test Donor' not in output.getvalue()
assert '12.34' not in output.getvalue()
assert 'synthetic-key' not in output.getvalue()
assert json.loads(Path('people.jsonl').read_text())['record']['details'] == {'custom': 'synthetic'}
print('Installed base wheel plan/apply/export/preview/recovery passed with synthetic HTTP and no EasyTithe, dotenv or dev tools')
PY
# Confirm that an sdist builds independently of the original checkout.
sdists=("$repo_dir"/dist/*.tar.gz)
uv pip install --python "$artifact_dir/venv/bin/python" --reinstall "${sdists[0]}[operator]"
"$artifact_dir/venv/bin/breeze" --help >/dev/null
"$artifact_dir/venv/bin/breeze" preview --source source.csv --policy policy.json >/dev/null
