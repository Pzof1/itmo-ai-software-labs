from datetime import datetime
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.config import Settings


def test_soft_delete_migration_should_preserve_tasks_through_upgrade_and_downgrade(
    tmp_path, monkeypatch
):
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    # Run the real Alembic environment entirely locally, without the configured server.
    monkeypatch.setattr(Settings, "DATABASE_URL", property(lambda self: database_url))
    config = Config()
    config.set_main_option(
        "script_location", str(Path(__file__).resolve().parents[1] / "migrations")
    )
    command.upgrade(config, "5ac38a2052d1")
    engine = sa.create_engine(database_url)
    try:
        metadata = sa.MetaData()
        metadata.reflect(engine)
        tasks = metadata.tables["tasks"]
        original_columns = sa.inspect(engine).get_columns("tasks")
        original_foreign_keys = sa.inspect(engine).get_foreign_keys("tasks")
        rows = [
            {
                "id": 1,
                "owner_id": 1,
                "name": "Existing done task",
                "status": "done",
                "description": "Keep this",
                "priority": "high",
                "due_date": datetime(2020, 1, 2),
                "created_at": datetime(2020, 1, 1),
            },
            {
                "id": 2,
                "owner_id": 1,
                "name": "Existing pending task",
                "status": "pending",
                "description": None,
                "priority": "low",
                "due_date": None,
                "created_at": datetime(2020, 2, 1),
            },
        ]
        with engine.begin() as connection:
            connection.execute(
                metadata.tables["users"].insert(),
                {
                    "id": 1,
                    "login": "migration_user",
                    "hashed_password": "unused",
                },
            )
            connection.execute(tasks.insert(), rows)

        command.upgrade(config, "head")
        upgraded = sa.Table("tasks", sa.MetaData(), autoload_with=engine)
        assert upgraded.c.is_deleted.nullable is False
        with engine.begin() as connection:
            actual = (
                connection.execute(sa.select(upgraded).order_by(upgraded.c.id)).mappings().all()
            )
            assert [dict(row) for row in actual] == [dict(row, is_deleted=False) for row in rows]
            # The server default also protects inserts that omit the new column.
            new_row = dict(rows[0], id=3, name="Created after upgrade")
            connection.execute(upgraded.insert(), new_row)
            assert (
                connection.scalar(sa.select(upgraded.c.is_deleted).where(upgraded.c.id == 3))
                is False
            )
            connection.execute(upgraded.update().where(upgraded.c.id == 1).values(is_deleted=True))

        command.downgrade(config, "5ac38a2052d1")
        downgraded = sa.Table("tasks", sa.MetaData(), autoload_with=engine)
        assert "is_deleted" not in downgraded.c
        with engine.connect() as connection:
            actual = (
                connection.execute(sa.select(downgraded).order_by(downgraded.c.id)).mappings().all()
            )
            assert [dict(row) for row in actual] == [*rows, new_row]
        columns = sa.inspect(engine).get_columns("tasks")
        assert [(c["name"], str(c["type"]), c["nullable"], c["default"]) for c in columns] == [
            (c["name"], str(c["type"]), c["nullable"], c["default"]) for c in original_columns
        ]
        assert sa.inspect(engine).get_foreign_keys("tasks") == original_foreign_keys

        command.upgrade(config, "head")
        with engine.connect() as connection:
            actual = (
                connection.execute(sa.select(upgraded).order_by(upgraded.c.id)).mappings().all()
            )
            assert [dict(row) for row in actual] == [
                dict(row, is_deleted=False) for row in [*rows, new_row]
            ]
    finally:
        engine.dispose()
