# features/Services/tab_manager/tab_manager_models.py

from dataclasses import dataclass, field


@dataclass
class ImportResult:
    """Data Transfer Object for the results of an import operation."""
    source: str
    success_count: int = 0
    failed_count: int = 0
    added_services_names: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
