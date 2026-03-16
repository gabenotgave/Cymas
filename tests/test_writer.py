"""Tests for data_io.writer (CSV writing)."""
import csv
import pytest

from data_io.writer import write_data, FIELDNAMES


def test_write_data_writes_headers_on_first_call(tmp_path, sample_row):
    """First write to a path creates file and writes header row."""
    csv_path = tmp_path / "data.csv"
    assert not csv_path.exists()
    write_data(sample_row, str(csv_path))
    assert csv_path.exists()
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == FIELDNAMES
        row = next(reader)
        assert row["timestamp"] == sample_row["timestamp"]
        assert row["gateway_ip"] == sample_row["gateway_ip"]


def test_write_data_does_not_repeat_headers_on_second_call(tmp_path, sample_row):
    """Subsequent writes append rows only; header is not repeated."""
    csv_path = tmp_path / "data.csv"
    write_data(sample_row, str(csv_path))
    sample_row2 = {**sample_row, "timestamp": "2025-03-15T12:01:00"}
    write_data(sample_row2, str(csv_path))
    with open(csv_path, newline="") as f:
        lines = f.readlines()
    header_count = sum(1 for line in lines if line.strip() == ",".join(FIELDNAMES))
    assert header_count == 1, "Header should appear exactly once"


def test_write_data_every_row_has_all_fieldnames(tmp_path, sample_row):
    """Every written row contains all FIELDNAMES columns."""
    csv_path = tmp_path / "data.csv"
    write_data(sample_row, str(csv_path))
    write_data({**sample_row, "timestamp": "2025-03-15T12:02:00"}, str(csv_path))
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for name in FIELDNAMES:
                assert name in row, f"Missing column {name} in row {row}"


def test_write_data_appends_to_existing_file(tmp_path, sample_row):
    """Multiple calls append rows; existing content is preserved."""
    csv_path = tmp_path / "data.csv"
    write_data(sample_row, str(csv_path))
    row2 = {**sample_row, "timestamp": "2025-03-15T12:05:00", "device_count": 10}
    write_data(row2, str(csv_path))
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["timestamp"] == "2025-03-15T12:00:00"
    assert rows[1]["timestamp"] == "2025-03-15T12:05:00"
    assert rows[1]["device_count"] == "10"
