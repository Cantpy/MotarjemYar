# features/Services/repositories/services_repo.py

from typing import Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from shared.orm_models.services_models import ServicesModel, ServiceDynamicPrice, ServiceAlias, ServiceDynamicPriceAlias


class ServiceRepository:
    """Repository for ServicesModel model operations."""

    def get_all(self, session: Session) -> list[type(ServicesModel)]:
        """
        Get all services and EAGERLY LOAD their related dynamic prices
        to prevent the N+1 query problem.
        """
        return (
            session.query(ServicesModel)
            .options(
                joinedload(ServicesModel.dynamic_prices).
                joinedload(ServiceDynamicPrice.aliases),
                joinedload(ServicesModel.aliases)
            )
            .order_by(ServicesModel.name)
            .all()
        )

    def get_by_id_with_aliases(self, session: Session, service_id: int) -> ServicesModel | None:
        """Get a single service by ID, eagerly loading all aliases."""
        return (
            session.query(ServicesModel)
            .options(
                joinedload(ServicesModel.dynamic_prices).joinedload(ServiceDynamicPrice.aliases),
                joinedload(ServicesModel.aliases)
            )
            .filter(ServicesModel.id == service_id)
            .first()
        )

    def update_aliases(self, session: Session, service_id: int, aliases_data: dict) -> bool:
        """
        Efficiently updates all aliases for a given service and its dynamic prices.
        """
        service = self.get_by_id_with_aliases(session, service_id)
        if not service:
            return False

        # --- Update Service Aliases ---
        existing_aliases = {alias.alias for alias in service.aliases}
        new_aliases = set(aliases_data.get("service_aliases", []))

        # Remove old, add new
        service.aliases = [ServiceAlias(alias=name) for name in new_aliases]

        # --- Update Dynamic Price Aliases ---
        dp_aliases_map = {item['id']: set(item['aliases']) for item in aliases_data.get("dynamic_price_aliases", [])}

        for dp in service.dynamic_prices:
            if dp.id in dp_aliases_map:
                new_dp_aliases = dp_aliases_map[dp.id]
                dp.aliases = [ServiceDynamicPriceAlias(alias=name) for name in new_dp_aliases]

        return True

    def update_service_properties(self, session: Session, service_id: int, data: dict) -> ServicesModel | None:
        """
        Efficiently updates properties for a service and returns the updated model.
        """
        service = self.get_by_id_with_aliases(session, service_id)
        if not service:
            return None # Return None if not found

        # --- Update Service Properties ---
        service.default_page_count = data.get('default_page_count', service.default_page_count)

        # --- Update Service Aliases ---
        if 'service_aliases' in data:
            service.aliases = [ServiceAlias(alias=name) for name in data["service_aliases"]]

        # --- Update Dynamic Price Aliases ---
        if 'dynamic_price_aliases' in data:
            dp_aliases_map = {item['id']: set(item['aliases']) for item in data["dynamic_price_aliases"]}
            for dp in service.dynamic_prices:
                if dp.id in dp_aliases_map:
                    dp.aliases = [ServiceDynamicPriceAlias(alias=name) for name in dp_aliases_map[dp.id]]

        return service

    def get_by_id(self, session: Session, service_id: int) -> ServicesModel | None:
        return session.query(ServicesModel).filter(ServicesModel.id == service_id).first()

    def get_by_name(self, session: Session, name: str) -> ServicesModel | None:
        return session.query(ServicesModel).filter(ServicesModel.name == name).first()

    def create_service_with_prices(self, session: Session, data: dict) -> ServicesModel:
        """
        Creates a new service and its associated dynamic prices in one go.
        SQLAlchemy's relationship management handles the foreign keys.
        """
        # Create the list of child ServiceDynamicFee objects
        fee_objects = [
            ServiceDynamicPrice(name=fee['name'], unit_price=fee['unit_price'])
            for fee in data.get('dynamic_prices', [])
        ]

        # Create the parent ServicesModel object
        new_service = ServicesModel(
            name=data['name'],
            base_price=data['base_price'],
            dynamic_prices=fee_objects
        )

        session.add(new_service)
        session.flush()
        print(f'new services created in repo: {new_service}')
        return new_service

    def update(self, session: Session, service_id: int, service_data: dict) -> type(ServicesModel) | None:
        """
        Updates a service and its dynamic prices.
        """
        service = session.query(ServicesModel).options(joinedload(ServicesModel.dynamic_prices)).filter(
            ServicesModel.id == service_id).first()

        if not service:
            return None

        service.name = service_data.get('name', service.name)
        service.base_price = service_data.get('base_price', service.base_price)

        if "dynamic_prices" in service_data:
            service.dynamic_prices.clear()

            new_prices_data = service_data["dynamic_prices"]
            for fee_data in new_prices_data:
                new_fee = ServiceDynamicPrice(
                    name=fee_data['name'],
                    unit_price=fee_data['unit_price']
                )
                service.dynamic_prices.append(new_fee)

        return service

    def delete(self, session: Session, service_id: int) -> bool:
        service = session.query(ServicesModel).filter(ServicesModel.id == service_id).first()
        if not service:
            return False
        session.delete(service)
        return True

    def delete_multiple(self, session: Session, service_ids: list[int]) -> int:
        # 1. Load all the parent objects you intend to delete.
        services_to_delete = session.query(ServicesModel).filter(
            ServicesModel.id.in_(service_ids)
        ).all()

        if not services_to_delete:
            return 0

        # 2. Loop through and delete them. SQLAlchemy will manage the cascade for each.
        for service in services_to_delete:
            session.delete(service)

        return len(services_to_delete)

    def delete_all(self, session: Session) -> int:
        return session.query(ServicesModel).delete()

    def search(self, session: Session, search_term: str) -> list[type(ServicesModel)]:
        return session.query(ServicesModel).filter(
            ServicesModel.name.ilike(f"%{search_term}%")
        ).order_by(ServicesModel.name).all()

    def exists_by_name(self, session: Session, name: str, exclude_id: int | None = None) -> bool:
        query = session.query(ServicesModel).filter(ServicesModel.name == name)
        if exclude_id:
            query = query.filter(ServicesModel.id != exclude_id)
        return query.first() is not None

    def bulk_create(self, session: Session, services_data: list[dict[str, Any]]) -> int:
        if not services_data:
            return 0
        try:
            for data in services_data:
                dynamic_prices_data = data.pop("dynamic_prices", [])
                service = ServicesModel(**data)
                for fee in dynamic_prices_data:
                    service.dynamic_prices.append(ServiceDynamicPrice(**fee))
                session.add(service)
            session.flush()
            return len(services_data)
        except SQLAlchemyError as e:
            raise Exception(f"Database bulk insert failed: {e}")
