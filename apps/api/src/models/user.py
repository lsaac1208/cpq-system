from .base import db, BaseModel
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token

class User(BaseModel):
    """User model for authentication and authorization."""
    
    __tablename__ = 'users'
    
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # user, admin, manager
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_tokens(self):
        """Generate JWT tokens for user."""
        # 🔧 修复：使用用户名作为JWT身份标识，添加必要的claims
        additional_claims = {
            'sub': self.username,  # 添加sub claim
            'role': self.role,
            'user_id': self.id
        }
        return {
            'access_token': create_access_token(
                identity=self.username,
                additional_claims=additional_claims
            ),
            'refresh_token': create_refresh_token(identity=self.username)
        }
    
    @property
    def full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary."""
        data = super().to_dict()
        
        # Remove sensitive information
        if not include_sensitive:
            data.pop('password_hash', None)
        
        # Add computed properties
        data['full_name'] = self.full_name
        
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'