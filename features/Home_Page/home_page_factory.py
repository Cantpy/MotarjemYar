# home_page/factory.py

from sqlalchemy.engine import Engine

from features.Home_Page.home_page_controller import HomePageController
from features.Home_Page.home_page_view import HomePageView
from features.Home_Page.home_page_logic import HomePageLogic
from features.Home_Page.home_page_repo import (HomePageRepository, HomePageCustomersRepository,
                                               HomePageServicesRepository, HomePageInvoicesRepository)

from shared.session_provider import ManagedSessionProvider


class HomePageFactory:
    """
    Factory for creating and wiring all components of the home page.
    It accepts pre-configured session makers.
    """

    @staticmethod
    def create(customers_engine: Engine,
               invoices_engine: Engine,
               services_engine: Engine,
               parent=None) -> HomePageController:
        """
        Creates a fully configured Home Page module.

        Args:
            customers_engine: The SQLAlchemy engine for the customers database.
            invoices_engine: The SQLAlchemy engine for the invoices database.
            services_engine: The SQLAlchemy engine for the invoices database.
            parent: The parent widget.

        Returns:
            HomePageController: The main controller which holds the view.
        """

        customer_session_provider = ManagedSessionProvider(engine=customers_engine)
        invoice_session_provider = ManagedSessionProvider(engine=invoices_engine)
        services_session_provider = ManagedSessionProvider(engine=services_engine)

        # 1. Create Data and Logic components
        invoices_repo = HomePageInvoicesRepository()
        customers_repo = HomePageCustomersRepository()
        services_repo = HomePageServicesRepository()
        repository = HomePageRepository(invoices_repo=invoices_repo,
                                        customers_repo=customers_repo,
                                        services_repo=services_repo)
        logic = HomePageLogic(
            repository=repository,
            customer_engine=customer_session_provider,
            invoices_engine=invoice_session_provider,
            services_engine=services_session_provider
        )

        # 2. Create the UI (View)
        view = HomePageView(parent=parent)

        # 4. Create the Controller, injecting its dependencies
        controller = HomePageController(
            view=view,
            logic=logic
        )

        return controller


if __name__ == "__main__":
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=HomePageFactory,
        required_engines={'customers': 'customers_engine', 'invoices': 'invoices_engine'},
        use_memory_db=True
    )
