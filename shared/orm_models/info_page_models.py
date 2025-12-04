# shared/orm_models/info_page_models.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

BaseInfoPage = declarative_base()


class Version(BaseInfoPage):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_number = Column(String, nullable=False)
    release_date = Column(String, nullable=False)

    # Relationships
    changelog_entries = relationship("Changelog", back_populates="version", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Version(id={self.id}, version_number='{self.version_number}', release_date='{self.release_date}')>"


class Changelog(BaseInfoPage):
    __tablename__ = "changelog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey("versions.id"))
    change_description = Column(Text, nullable=False)

    # Relationship
    version = relationship("Version", back_populates="changelog_entries")

    def __repr__(self):
        return f"<Changelog(id={self.id}, version_id={self.version_id}, change_description='{self.change_description[:30]}...')>"


class FAQ(BaseInfoPage):
    __tablename__ = "faq"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

    def __repr__(self):
        return f"<FAQ(id={self.id}, question='{self.question[:30]}...')>"
