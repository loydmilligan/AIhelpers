"""
Base model classes for SQLAlchemy models.

Provides common functionality and fields for all database models.
"""

from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Column, Integer, DateTime, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column


# Create metadata instance with naming convention for constraints
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

# Create the base class
Base = declarative_base(metadata=metadata)


class BaseModel(Base):
    """
    Base model class with common fields and functionality.
    
    Provides:
    - Primary key (id)
    - Timestamps (created_at, updated_at)
    - Serialization methods
    """
    
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            Dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Update model instance from dictionary.
        
        Args:
            data: Dictionary with field values to update
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """String representation of the model."""
        class_name = self.__class__.__name__
        return f"<{class_name}(id={self.id})>"