#!/usr/bin/env bash
# Install and exercise the published wheel outside the source checkout.
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
artifact_dir="$(mktemp -d)"
trap 'rm -rf -- "$artifact_dir"' EXIT
uv venv --python 3.14.8 "$artifact_dir/venv"
uv pip install --python "$artifact_dir/venv/bin/python" "$repo_dir"/dist/*.whl "$repo_dir"/samples/easytithe/dist/*.whl
cd "$artifact_dir"
"$artifact_dir/venv/bin/python" - <<'PY'
from importlib.metadata import version
from pathlib import Path
import breeze
from easytithe import EasyTithe, EasyTitheError
from unittest.mock import patch
import requests
from breeze.breeze import BreezeApi

assert version('pyBreezeChMS') == '2.0.0'
assert Path(breeze.__file__).with_name('py.typed').is_file()
with BreezeApi('https://demo.breezechms.com', 'synthetic-key', dry_run=True) as client:
    assert client.get_people() is None
    assert client.add_contribution() is None
with patch.object(requests.Session, 'request', side_effect=requests.Timeout('offline')):
    try:
        EasyTithe('synthetic-user', 'synthetic-password')
    except EasyTitheError as error:
        assert isinstance(error.__cause__, requests.Timeout)
    else:
        raise AssertionError('Expected translated timeout')
assert version('easytithe') == '2.0.0'
print('Installed Breeze and EasyTithe wheel smoke tests passed')
PY
# Confirm that an sdist builds independently of the original checkout.
uv pip install --python "$artifact_dir/venv/bin/python" --reinstall "$repo_dir"/dist/*.tar.gz "$repo_dir"/samples/easytithe/dist/*.tar.gz
"$artifact_dir/venv/bin/python" -c 'from breeze.breeze import BreezeApi; from easytithe import EasyTithe; assert BreezeApi and EasyTithe'
