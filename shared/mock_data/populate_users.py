# shared/mock_data/populate_users.py

import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from shared.orm_models.users_models import UsersModel, UserProfileModel, LoginLogsModel
from shared.mock_data.mock_data_source import MOCK_PEOPLE_DATA


def populate_users_db(users_session: Session):
    """Populates the Users.db with mock users, profiles, and login logs."""
    if users_session.query(UsersModel).first():
        return  # Data already exists

    print("Populating Users.db with mock users, profiles, and logs...")
    placeholder_hash = b'$2b$12$DGIqO2yVkvk.eI0J4d5J5.iJz8.AS2hH7m7dI6Co.5gLw24LmcG.K'  # Placeholder

    # --- Define User Data ---
    users_info = {
        'admin': {'full_name': 'آرش مدیر', 'role_fa': 'مدیر', 'role': 'admin'},
        'clerk1': {'full_name': 'سارا کارمند', 'role_fa': 'کارمند', 'role': 'clerk'},
        'rezaei': {'full_name': 'رضا رضایی', 'role_fa': 'مترجم', 'role': 'translator'},
        'hosseini': {'full_name': 'مریم حسینی', 'role_fa': 'مترجم', 'role': 'translator'},
        'ahmadi': {'full_name': 'احمد احمدی', 'role_fa': 'حسابدار', 'role': 'accountant'}
    }

    created_users = []
    for person in MOCK_PEOPLE_DATA:
        user = UsersModel(
            username=person['username'],
            password_hash=placeholder_hash,
            role=person['role']
        )
        users_session.add(user)
        users_session.flush()

        profile = UserProfileModel(
            user_id=user.id,
            full_name=f"{person['first']} {person['last']}",
            # --- The national_id now comes from the shared source ---
            national_id=person['nid'],
            role_fa=f"نقش {person['role']}"  # Placeholder for role_fa
        )
        users_session.add(profile)
        created_users.append(user)

    # --- Create Login Logs ---
    login_logs = []
    for _ in range(25):
        user = random.choice(created_users)
        login_time = datetime.now() - timedelta(hours=random.randint(1, 72))
        status = random.choice(['success', 'failed', 'auto_login_success'])
        log = LoginLogsModel(user_id=user.id, login_time=login_time.strftime('%Y-%m-%d %H:%M:%S'), status=status)
        login_logs.append(log)
    users_session.add_all(login_logs)

    users_session.commit()
