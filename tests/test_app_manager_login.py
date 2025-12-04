from unittest.mock import MagicMock
from core.application_manager import ApplicationManager


def test_transition_to_main_window(app_manager_with_mocks):
    mgr = ApplicationManager()

    # Mock the controller
    fake_controller = MagicMock()
    fake_controller.get_view.return_value = MagicMock()

    # Mock factory
    from features.Main_Window import main_window_factory
    main_window_factory.MainWindowFactory.create = MagicMock(return_value=fake_controller)

    # Mock Qt splash
    mgr._create_splash_screen = MagicMock()

    user = MagicMock(username="testuser")
    mgr.app = MagicMock()

    mgr.transition_to_main_window(user)

    fake_controller.initialize_with_user.assert_called_once_with("testuser")
    fake_controller.get_view().show.assert_called_once()


def test_start_application_auto_login(monkeypatch):
    mgr = ApplicationManager()

    # mock QApplication
    monkeypatch.setattr("core.application_manager.QApplication", MagicMock())

    # mock engines + database initializer
    mgr.engines = {"users": MagicMock(), "licenses": MagicMock()}

    # mock _is_setup_required
    mgr._is_setup_required = MagicMock(return_value=False)

    # mock seeder
    monkeypatch.setattr("core.application_manager.DatabaseSeeder", MagicMock())

    # mock login factory
    fake_login = MagicMock()
    fake_login._logic.check_and_auto_login.return_value = (True, MagicMock(username="john"))
    from features.Login import login_window_factory
    login_window_factory.LoginWindowFactory.create = MagicMock(return_value=fake_login)

    mgr.transition_to_main_window = MagicMock()

    mgr.start_application()

    mgr.transition_to_main_window.assert_called_once()
