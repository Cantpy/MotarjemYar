import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.application_manager import ApplicationManager
from shared.orm_models.license_models import LicenseModel, BaseLicense
from shared.orm_models.users_models import UsersModel, BaseUsers


@pytest.fixture
def app_manager():
    return ApplicationManager()


@pytest.fixture
def engines():
    eng_l = create_engine("sqlite:///:memory:")
    eng_u = create_engine("sqlite:///:memory:")
    BaseLicense.metadata.create_all(eng_l)
    BaseUsers.metadata.create_all(eng_u)
    return {"licenses": eng_l, "users": eng_u}


def test_setup_required_when_no_license_no_admin(app_manager, engines):
    app_manager.engines = engines
    assert app_manager._is_setup_required() is True


def test_setup_not_required(app_manager, engines):
    app_manager.engines = engines

    # create license
    SessionL = sessionmaker(bind=engines["licenses"])
    l = SessionL()
    l.add(LicenseModel(license_key="ABC123"))
    l.commit()
    l.close()

    # create admin user
    SessionU = sessionmaker(bind=engines["users"])
    u = SessionU()
    u.add(UsersModel(username="admin", password="123", role="admin"))
    u.commit()
    u.close()

    assert app_manager._is_setup_required() is False
