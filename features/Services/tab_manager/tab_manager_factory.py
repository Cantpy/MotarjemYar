# services_management/factory.py

from sqlalchemy.engine import Engine

from features.Services.tab_manager.tab_manager_view import ServicesManagementView
from features.Services.tab_manager.tab_manager_controller import ServicesManagementController
from features.Services.tab_manager.tab_manager_logic import ExcelImportLogic

from features.Services.documents.documents_factory import ServicesDocumentFactory
from features.Services.other_services.other_services_factory import OtherServicesFactory


class ServicesManagementFactory:
    """
    The main factory for creating the entire Services Management module.
    It builds and returns the main controller, which holds the final _view.
    """

    @staticmethod
    def create(business_engine: Engine, parent=None) -> ServicesManagementController:
        """
        Builds the complete, interactive Services Management module.
        """
        container_view = ServicesManagementView(parent)

        documents_controller = ServicesDocumentFactory.create(business_engine=business_engine,
                                                              parent=container_view)
        other_services_controller = OtherServicesFactory.create(business_engine=business_engine,
                                                                parent=container_view)

        # 3. Get the VIEW from each sub-controller and add it to the container's tab widget.
        container_view.add_tab(documents_controller.get_view(), "مدارک")
        container_view.add_tab(other_services_controller.get_view(), "خدمات دیگر")

        import_logic = ExcelImportLogic(
            services_logic=documents_controller._logic,
            other_services_logic=other_services_controller._logic,
        )

        # 4. Create the main controller, INJECTING the container _view AND all the sub-controllers.
        main_controller = ServicesManagementController(
            view=container_view,
            import_logic=import_logic,
            documents_controller=documents_controller,
            other_services_controller=other_services_controller
        )

        # 5. Return the final, assembled main controller.
        return main_controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=ServicesManagementFactory,
        required_engines={'business': 'business_engine'},
        use_memory_db=True
    )
