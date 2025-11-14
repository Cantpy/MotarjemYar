# features/Admin_Panel/user_info/user_info_factory.py

from features.Admin_Panel.user_info.user_info_controller import UserInfoController
from features.Admin_Panel.user_info.user_info_view import UserInfoView


class UserInfoFactory:
    """
    Factory for creating the User Info feature.
    """
    @staticmethod
    def create(parent=None) -> UserInfoController:
        """
        Creates and returns a fully assembled User Info controller.
        """
        view = UserInfoView(parent=parent)
        controller = UserInfoController(view=view)
        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test

    launch_feature_for_ui_test(
        factory_class=UserInfoFactory
    )
