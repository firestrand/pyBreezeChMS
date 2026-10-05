"""Read forms, then fields and entries; print only bounded counts."""

import json
import sys
from pathlib import Path

from breeze.breeze import BreezeApi, BreezeError
from breeze.configuration import breeze_credentials


def main() -> int:
    try:
        with BreezeApi(*breeze_credentials(Path(".env"))) as client:
            forms = client.list_forms()
            if not isinstance(forms, list):
                raise ValueError("Invalid forms collection")
            summary = {"forms": len(forms), "fields": 0, "entries": 0}
            if forms:
                first = forms[0]
                identifier = first.get("id") if isinstance(first, dict) else None
                if isinstance(identifier, bool) or not isinstance(identifier, str | int):
                    raise ValueError("Invalid form identifier")
                fields = client.list_form_fields(identifier)
                entries = client.list_form_entries(identifier)
                if not isinstance(fields, list) or not isinstance(entries, list):
                    raise ValueError("Invalid form fields or entries collection")
                summary.update(fields=len(fields), entries=len(entries))
            print(json.dumps(summary, sort_keys=True))
        return 0
    except BreezeError, ValueError, OSError:
        print(
            "Forms read failed; check account configuration and provider contracts.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
