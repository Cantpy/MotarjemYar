# features/Info_Page/info_page_models.py

from dataclasses import dataclass
from typing import List


@dataclass
class VersionInfoDTO:
    """DTO for version information."""
    version_number: str
    release_date: str


@dataclass
class ChangelogEntryDTO:
    """DTO for a single changelog entry."""
    description: str


@dataclass
class FAQItemDTO:
    """DTO for a single FAQ item."""
    question: str
    answer: str


@dataclass
class InfoPageDataDTO:
    """DTO to hold all data for the info page."""
    version_info: VersionInfoDTO
    changelog: List[ChangelogEntryDTO]
    faq_items: List[FAQItemDTO]
