from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from decimal import Decimal
import json

# Initialize SQLAlchemy
db = SQLAlchemy()

class BaseModel(db.Model):
    """Base model class with common fields and methods."""
    
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def save(self):
        """Save the model to the database."""
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete(self):
        """Delete the model from the database."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
    
    def to_dict(self):
        """Convert model to dictionary with proper serialization."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            
            # Handle different data types
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif isinstance(value, Decimal):
                result[column.name] = float(value)
            elif hasattr(value, '__dict__'):
                # Handle complex objects
                result[column.name] = str(value)
            else:
                result[column.name] = value
                
        return result