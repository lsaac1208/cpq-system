"""Unit tests for User model."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from src.models.user import User
from src.models.base import db


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, db_session, sample_user_data):
        """Test creating a new user."""
        user = User(
            username=sample_user_data['username'],
            email=sample_user_data['email'],
            first_name=sample_user_data['first_name'],
            last_name=sample_user_data['last_name'],
            role=sample_user_data['role']
        )
        user.set_password(sample_user_data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.username == sample_user_data['username']
        assert user.email == sample_user_data['email']
        assert user.first_name == sample_user_data['first_name']
        assert user.last_name == sample_user_data['last_name']
        assert user.role == sample_user_data['role']
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_password_hashing(self, sample_user_data):
        """Test password hashing and verification."""
        user = User(
            username=sample_user_data['username'],
            email=sample_user_data['email'],
            first_name=sample_user_data['first_name'],
            last_name=sample_user_data['last_name']
        )
        
        # Test password setting
        user.set_password(sample_user_data['password'])
        assert user.password_hash is not None
        assert user.password_hash != sample_user_data['password']
        
        # Test password verification
        assert user.check_password(sample_user_data['password']) is True
        assert user.check_password('wrongpassword') is False
    
    def test_full_name_property(self, sample_user_data):
        """Test full_name property."""
        user = User(
            username=sample_user_data['username'],
            email=sample_user_data['email'],
            first_name=sample_user_data['first_name'],
            last_name=sample_user_data['last_name']
        )
        
        expected_full_name = f"{sample_user_data['first_name']} {sample_user_data['last_name']}"
        assert user.full_name == expected_full_name
    
    def test_get_tokens(self, db_session, test_user):
        """Test JWT token generation."""
        tokens = test_user.get_tokens()
        
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert tokens['access_token'] is not None
        assert tokens['refresh_token'] is not None
        assert isinstance(tokens['access_token'], str)
        assert isinstance(tokens['refresh_token'], str)
    
    def test_to_dict_exclude_sensitive(self, test_user):
        """Test to_dict method excludes sensitive information by default."""
        user_dict = test_user.to_dict()
        
        assert 'password_hash' not in user_dict
        assert 'id' in user_dict
        assert 'username' in user_dict
        assert 'email' in user_dict
        assert 'first_name' in user_dict
        assert 'last_name' in user_dict
        assert 'role' in user_dict
        assert 'full_name' in user_dict
        assert 'is_active' in user_dict
        assert 'created_at' in user_dict
        assert 'updated_at' in user_dict
    
    def test_to_dict_include_sensitive(self, test_user):
        """Test to_dict method includes sensitive information when requested."""
        user_dict = test_user.to_dict(include_sensitive=True)
        
        assert 'password_hash' in user_dict
        assert user_dict['password_hash'] is not None
    
    def test_user_repr(self, test_user):
        """Test user string representation."""
        repr_str = repr(test_user)
        assert repr_str == f'<User {test_user.username}>'
    
    def test_unique_constraints(self, db_session, sample_user_data):
        """Test unique constraints for username and email."""
        # Create first user
        user1 = User(
            username=sample_user_data['username'],
            email=sample_user_data['email'],
            first_name=sample_user_data['first_name'],
            last_name=sample_user_data['last_name']
        )
        user1.set_password(sample_user_data['password'])
        db.session.add(user1)
        db.session.commit()
        
        # Try to create second user with same username
        user2 = User(
            username=sample_user_data['username'],  # Same username
            email='different@example.com',
            first_name='Different',
            last_name='User'
        )
        user2.set_password('differentpass')
        db.session.add(user2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db.session.commit()
        
        db.session.rollback()
        
        # Try to create third user with same email
        user3 = User(
            username='differentuser',
            email=sample_user_data['email'],  # Same email
            first_name='Different',
            last_name='User'
        )
        user3.set_password('differentpass')
        db.session.add(user3)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db.session.commit()
    
    def test_default_role(self, db_session):
        """Test default role assignment."""
        user = User(
            username='testuser2',
            email='test2@example.com',
            first_name='Test',
            last_name='User2'
        )
        user.set_password('testpass')
        
        # Don't set role explicitly
        db.session.add(user)
        db.session.commit()
        
        assert user.role == 'user'  # Should default to 'user'
    
    def test_user_active_status(self, db_session):
        """Test user active status."""
        user = User(
            username='testuser3',
            email='test3@example.com',
            first_name='Test',
            last_name='User3'
        )
        user.set_password('testpass')
        
        # Don't set is_active explicitly
        db.session.add(user)
        db.session.commit()
        
        assert user.is_active is True  # Should default to True
        
        # Test setting to inactive
        user.is_active = False
        db.session.commit()
        assert user.is_active is False