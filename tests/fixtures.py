"""Existing synthetic records, independent of the optional legacy importer."""

ROW = {
    "Name": "A.* Person",
    "Date": "10/01/2026",
    "Fund": 'A "quoted" fund',
    "Amount": "$1,000.25",
    "Type": "onCARD",
    "Email": "test@example.invalid",
    "PersonID": "42",
}
MATCHED_PEOPLE = [{"id": "1", "first_name": "A.*", "last_name": "Person"}]
OTHER_PEOPLE = [{"id": "2", "first_name": "Alice", "last_name": "Person"}]
