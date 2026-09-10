from pathlib import Path
import tempfile

from check_conventions import check_file


def diagnose(relative: str, source: str):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        path = root / relative
        path.parent.mkdir(parents=True)
        path.write_text(source)
        return check_file(path, root)


def test_clean_repository_function_should_have_no_diagnostics():
    assert diagnose("app/repository/tasks.py", "def find(db):\n    return db.execute(stmt)\n") == []


def test_service_sql_should_report_c1():
    result = diagnose("app/service/tasks.py", "def find(db):\n    return db.execute(stmt)\n")
    assert [item.rule_id for item in result] == ["C1"]


def test_repository_commit_and_fastapi_should_report_c2_and_c3():
    result = diagnose("app/repository/tasks.py", "from fastapi import HTTPException\ndef save(db):\n    db.commit()\n")
    assert {item.rule_id for item in result} == {"C2", "C3"}


def test_api_test_without_should_should_report_c7():
    result = diagnose("tests/test_api/test_tasks.py", "def test_returns_tasks():\n    pass\n")
    assert [item.rule_id for item in result] == ["C7"]
