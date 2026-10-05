"""Installed-boundary behavior using approved synthetic records and fake provider I/O."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from breeze import cli
from breeze.breeze import BreezeApi, BreezeError
from breeze.configuration import breeze_credentials
from breeze.interchange import load_plan
from breeze.journal import inspect_journal
from tests.test_client_boundaries import KEY, URL, Connection
from tests.test_interchange import source_text


def inputs(tmp_path: Path) -> tuple[Path, Path]:
    source, policy = tmp_path / "source.csv", tmp_path / "policy.json"
    source.write_text(source_text().replace('Test ""Donor"", Café', "Test Donor"), encoding="utf-8")
    policy.write_text(
        json.dumps(
            {
                "currency": "USD",
                "precision": 2,
                "start": "2026-10-01",
                "end": "2026-10-03",
                "funds": {"general": "5"},
            }
        )
    )
    return source, policy


def test_preview_needs_no_credentials_or_breeze_requests(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source, policy = inputs(tmp_path)
    with patch.object(
        cli, "breeze_credentials", side_effect=AssertionError("Offline means no credentials")
    ):
        assert cli.main(["preview", "--source", str(source), "--policy", str(policy)]) == 0
    output = capsys.readouterr()
    assert json.loads(output.out)["summary"] == {"create": 0, "skip": 0, "unresolved": 1}
    assert "Test Donor" not in output.out
    assert "12.34" not in output.out


def test_dotenv_is_private_does_not_interpolate_and_preserves_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("BREEZE_URL", raising=False)
    monkeypatch.delenv("BREEZE_API_KEY", raising=False)
    path = tmp_path / ".env"
    path.write_text("BREEZE_URL=https://demo.breezechms.com\nBREEZE_API_KEY=${UNSET_VALUE}\n")
    path.chmod(0o600)
    assert breeze_credentials(path) == (URL, "${UNSET_VALUE}")
    monkeypatch.setenv("BREEZE_API_KEY", KEY)
    assert breeze_credentials(path) == (URL, KEY)
    path.chmod(0o644)
    with pytest.raises(ValueError, match="private"):
        breeze_credentials(path)


def test_live_plan_and_apply_require_digest_and_resume_without_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("BREEZE_URL", URL)
    monkeypatch.setenv("BREEZE_API_KEY", KEY)
    source, policy = inputs(tmp_path)
    plan_path, journal = tmp_path / "plan.json", tmp_path / "run.sqlite"
    with (
        BreezeApi(URL, KEY, connection=Connection()) as client,
        patch.object(cli, "BreezeApi", return_value=client),
        patch.object(
            client,
            "get_people",
            return_value=[{"id": "1", "first_name": "Test", "last_name": "Donor"}],
        ),
        patch.object(client, "list_funds", return_value=[{"id": "5"}]),
        patch.object(
            client,
            "get_account_summary",
            return_value={"details": {"country": {"currency": "USD"}}},
        ),
        patch.object(client, "list_contributions", return_value=[]),
        patch.object(client, "add_allocated_contribution", return_value="receipt") as create,
    ):
        prefix = ["--env-file", str(tmp_path / "absent.env")]
        assert (
            cli.main(
                prefix
                + [
                    "plan",
                    "--source",
                    str(source),
                    "--policy",
                    str(policy),
                    "--output",
                    str(plan_path),
                ]
            )
            == 0
        )
        plan = load_plan(plan_path)
        arguments = prefix + [
            "apply",
            "--source",
            str(source),
            "--plan",
            str(plan_path),
            "--journal",
            str(journal),
            "--retention-days",
            "30",
            "--confirm-plan",
            plan.digest,
        ]
        assert cli.main(arguments) == 0
        assert cli.main(arguments) == 0
    assert create.call_count == 1
    assert inspect_journal(journal) == {"acknowledged": 1}
    output = capsys.readouterr()
    assert KEY not in output.out + output.err
    assert "Test Donor" not in output.out + output.err


def test_expected_error_output_omits_raw_chained_values(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source, policy = inputs(tmp_path)
    error = BreezeError("synthetic-secret-key and Test Donor")
    error.__cause__ = ValueError("synthetic-password")
    with patch.object(cli, "run", side_effect=error):
        assert cli.main(["preview", "--source", str(source), "--policy", str(policy)]) == 1
    output = capsys.readouterr()
    assert "Breeze operation failed" in output.err
    assert "synthetic" not in output.err
    assert "Test Donor" not in output.err


def test_partial_apply_reports_failure_and_preserves_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from breeze.importing import plan_import
    from breeze.interchange import CsvContributionSource, save_plan
    from tests.test_import_workflow import Gateway
    from tests.test_import_workflow import policy as import_policy

    source, _ = inputs(tmp_path)
    source.write_text(
        source.read_text() + source.read_text().splitlines()[1].replace("12.34", "23.45") + "\n"
    )
    gateway = Gateway()
    plan = plan_import(CsvContributionSource(source).load(), import_policy(), gateway)
    plan_path, journal = tmp_path / "plan.json", tmp_path / "run.sqlite"
    save_plan(plan_path, plan)
    monkeypatch.setenv("BREEZE_URL", URL)
    monkeypatch.setenv("BREEZE_API_KEY", KEY)
    arguments = [
        "--env-file",
        str(tmp_path / "absent.env"),
        "apply",
        "--source",
        str(source),
        "--plan",
        str(plan_path),
        "--journal",
        str(journal),
        "--retention-days",
        "30",
        "--confirm-plan",
        plan.digest,
    ]
    with (
        patch.object(cli, "BreezeImportGateway", return_value=gateway),
        patch.object(
            gateway, "create", side_effect=["receipt", BreezeError("private gift payload")]
        ) as create,
    ):
        assert cli.main(arguments) == 4
        assert cli.main(arguments) == 4
    assert create.call_count == 2
    assert inspect_journal(journal) == {"acknowledged": 1, "uncertain": 1}
    output = capsys.readouterr()
    assert "private gift payload" not in output.out + output.err


@pytest.mark.parametrize("failure", ["unresolved", "digest", "source"])
def test_apply_refusals_precede_credentials_and_writes(tmp_path: Path, failure: str) -> None:
    from breeze.importing import plan_import
    from breeze.interchange import CsvContributionSource, save_plan
    from tests.test_import_workflow import Gateway
    from tests.test_import_workflow import policy as import_policy

    source, _ = inputs(tmp_path)
    plan = plan_import(
        CsvContributionSource(source).load(),
        import_policy(),
        None if failure == "unresolved" else Gateway(),
    )
    plan_path = tmp_path / "plan.json"
    save_plan(plan_path, plan)
    if failure == "source":
        source.write_text(source.read_text().replace("12.34", "23.45"))
    with patch.object(cli, "breeze_credentials", side_effect=AssertionError("No provider access")):
        assert cli.main(
            [
                "apply",
                "--source",
                str(source),
                "--plan",
                str(plan_path),
                "--journal",
                str(tmp_path / "run.sqlite"),
                "--retention-days",
                "30",
                "--confirm-plan",
                "wrong" if failure == "digest" else plan.digest,
            ]
        ) == (3 if failure == "unresolved" else 4)
