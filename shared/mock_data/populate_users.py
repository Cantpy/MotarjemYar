"""
Production-ready seeder for Users.db.
Creates users and login logs from mock data sources.

- Idempotent (won’t duplicate)
- Includes centralized session handling
- Compatible with test and demo environments
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.orm import Session

from shared.orm_models.users_models import UsersModel, LoginLogsModel
from shared.mock_data.mock_data_source import MOCK_PEOPLE_DATA


class UsersSeeder:
    """Encapsulates logic for populating Users.db with mock data."""

    PLACEHOLDER_HASH: bytes = (
        b"$2b$12$DGIqO2yVkvk.eI0J4d5J5.iJz8.AS2hH7m7dI6Co.5gLw24LmcG.K"
    )

    def __init__(self, session: Session):
        self.session = session

    def run(self) -> None:
        """Main entry point."""
        if self._has_existing_data():
            print("⚙️  Users.db already populated. Skipping mock user seeding.")
            return

        print("🚀 Populating Users.db with mock users and logs...")

        try:
            created_users = self._create_users()
            self._create_login_logs(created_users)
            self._commit()
            print(f"✅ {len(created_users)} mock users seeded successfully.")
        except Exception as e:
            self.session.rollback()
            print(f"❌ Failed to seed Users.db: {e}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _has_existing_data(self) -> bool:
        return self.session.query(UsersModel).count() > 0

    def _create_users(self) -> List[UsersModel]:
        users: List[UsersModel] = []

        for i, person in enumerate(MOCK_PEOPLE_DATA[:10]):
            user = UsersModel(
                employee_id=f"EMP-{i+1:04d}",
                username=person["username"],
                password_hash=self.PLACEHOLDER_HASH,
                role=random.choice(["translator", "clerk", "accountant"]),
                active=1,
                display_name=person["full_name"],
                avatar_path=None,
                created_at=str(datetime.now(timezone.utc)),
                updated_at=str(datetime.now(timezone.utc)),
            )
            users.append(user)
            self.session.add(user)

        return users

    def _create_login_logs(self, users: List[UsersModel]) -> None:
        """Create mock login/logout logs for each user."""
        for user in users:
            for _ in range(random.randint(1, 3)):
                login_time = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))
                logout_time = login_time + timedelta(hours=random.randint(1, 8))
                log = LoginLogsModel(
                    user_id=user.id,
                    login_time=str(login_time),
                    logout_time=str(logout_time),
                    time_on_app=int((logout_time - login_time).total_seconds()),
                    status=random.choice(["success", "auto_login_success"]),
                    ip_address=f"192.168.1.{random.randint(1, 255)}",
                    user_agent="MockAgent/1.0",
                )
                self.session.add(log)

    def _commit(self) -> None:
        self.session.commit()
