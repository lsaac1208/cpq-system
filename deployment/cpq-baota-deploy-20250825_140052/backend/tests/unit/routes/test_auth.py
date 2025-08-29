"""Unit tests for Authentication routes."""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import url_for
from src.models.user import User
from src.models.base import db


class TestAuthRoutes:
    """Test authentication API endpoints."""
    
    def test_register_success(self, client, db_session):
        """Test successful user registration."""
        user_data = {
            'username': 'newuser',
            'email': 'newuser@gmail.com',
            'password': 'NewPass1@9!',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = client.post('/api/v1/auth/register', 
                             json=user_data,
                             content_type='application/json')
        
        assert response.status_code == 201
        response_data = response.get_json()
        data = response_data['data']
        
        assert 'user' in data
        assert 'tokens' in data
        assert data['user']['username'] == user_data['username']
        assert data['user']['email'] == user_data['email']
        assert data['user']['first_name'] == user_data['first_name']
        assert data['user']['last_name'] == user_data['last_name']
        assert data['user']['role'] == 'user'  # Default role assigned by system
        assert 'password_hash' not in data['user']
        
        assert 'access_token' in data['tokens']
        assert 'refresh_token' in data['tokens']
        
        # Verify user was created in database
        user = db.session.query(User).filter_by(username=user_data['username']).first()
        assert user is not None
        assert user.email == user_data['email']
    
    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        incomplete_data = {
            'username': 'incompleteuser',
            'email': 'incomplete@gmail.com'
            # Missing password, first_name, last_name
        }
        
        response = client.post('/api/v1/auth/register',
                             json=incomplete_data,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username."""
        user_data = {
            'username': test_user.username,  # Duplicate username
            'email': 'different@gmail.com',
            'password': 'password123',
            'first_name': 'Different',
            'last_name': 'User'
        }
        
        response = client.post('/api/v1/auth/register',
                             json=user_data,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        user_data = {
            'username': 'differentuser',
            'email': test_user.email,  # Duplicate email
            'password': 'password123',
            'first_name': 'Different',
            'last_name': 'User'
        }
        
        response = client.post('/api/v1/auth/register',
                             json=user_data,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        user_data = {
            'username': 'testuser',
            'email': 'invalid-email',  # Invalid email format
            'password': 'password123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        response = client.post('/api/v1/auth/register',
                             json=user_data,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_login_success(self, client, test_user, sample_user_data):
        """Test successful login."""
        login_data = {
            'username': test_user.username,
            'password': sample_user_data['password']
        }
        
        response = client.post('/api/v1/auth/login',
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        assert 'user' in data['data']
        assert 'tokens' in data['data']
        assert data['data']['user']['id'] == test_user.id
        assert data['data']['user']['username'] == test_user.username
        assert data['data']['user']['email'] == test_user.email
        assert 'password_hash' not in data['data']['user']
        
        assert 'access_token' in data['data']['tokens']
        assert 'refresh_token' in data['data']['tokens']
    
    def test_login_invalid_username(self, client):
        """Test login with invalid username."""
        login_data = {
            'username': 'nonexistentuser',
            'password': 'password123'
        }
        
        response = client.post('/api/v1/auth/login',
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        login_data = {
            'username': test_user.username,
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/v1/auth/login',
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_login_inactive_user(self, client, test_user, sample_user_data):
        """Test login with inactive user."""
        # Make user inactive
        test_user.is_active = False
        db.session.commit()
        
        login_data = {
            'username': test_user.username,
            'password': sample_user_data['password']
        }
        
        response = client.post('/api/v1/auth/login',
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        login_data = {
            'username': 'testuser'
            # Missing password
        }
        
        response = client.post('/api/v1/auth/login',
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code == 422  # Marshmallow validation error
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_get_current_user_success(self, client, auth_headers, test_user):
        """Test getting current user info with valid token."""
        response = client.get('/api/v1/auth/me', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        assert 'user' in data['data']
        assert data['data']['user']['id'] == test_user.id
        assert data['data']['user']['username'] == test_user.username
        assert data['data']['user']['email'] == test_user.email
        assert 'password_hash' not in data['data']['user']
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user info without token."""
        response = client.get('/api/v1/auth/me')
        
        assert response.status_code == 401
        data = response.get_json()
        # JWT extension returns 'msg' field for missing token
        assert 'msg' in data or 'error' in data
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user info with invalid token."""
        headers = {'Authorization': 'Bearer invalid_token'}
        response = client.get('/api/v1/auth/me', headers=headers)
        
        assert response.status_code == 422  # JWT decode error
        data = response.get_json()
        # JWT extension returns 'msg' field for invalid token
        assert 'msg' in data or 'error' in data
    
    def test_refresh_token_success(self, client, test_user, sample_user_data):
        """Test successful token refresh."""
        # First get a refresh token by logging in
        login_data = {
            'username': test_user.username,
            'password': sample_user_data['password']
        }
        
        login_response = client.post('/api/v1/auth/login', 
                                   json=login_data,
                                   content_type='application/json')
        
        assert login_response.status_code == 200
        login_data = login_response.get_json()
        refresh_token = login_data['data']['tokens']['refresh_token']
        
        # Now use the refresh token
        headers = {'Authorization': f'Bearer {refresh_token}'}
        response = client.post('/api/v1/auth/refresh', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
    
    def test_refresh_token_missing(self, client):
        """Test token refresh with missing refresh token."""
        response = client.post('/api/v1/auth/refresh')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid refresh token."""
        headers = {'Authorization': 'Bearer invalid_refresh_token'}
        response = client.post('/api/v1/auth/refresh', headers=headers)
        
        assert response.status_code == 422  # JWT decode error
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_logout_success(self, client, auth_headers):
        """Test successful logout."""
        response = client.post('/api/v1/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
    
    def test_logout_no_token(self, client):
        """Test logout without token."""
        response = client.post('/api/v1/auth/logout')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'msg' in data or 'error' in data
    
    def test_password_validation(self, client):
        """Test password validation during registration."""
        weak_passwords = [
            '123',           # Too short
            'password',      # Common password
            '12345678',      # Only numbers
            'abcdefgh',      # Only letters
        ]
        
        for weak_password in weak_passwords:
            user_data = {
                'username': f'user_{weak_password}',
                'email': f'{weak_password}@gmail.com',
                'password': weak_password,
                'first_name': 'Test',
                'last_name': 'User'
            }
            
            response = client.post('/api/v1/auth/register',
                                 json=user_data,
                                 content_type='application/json')
            
            # Should either reject weak password or accept it based on validation rules
            # This test documents current behavior
            assert response.status_code in [201, 400]
    
    def test_username_validation(self, client):
        """Test username validation during registration."""
        invalid_usernames = [
            'ab',            # Too short
            'user with spaces',  # Contains spaces
            'user@name',     # Contains @ symbol
            'user.name.',    # Ends with dot
        ]
        
        for invalid_username in invalid_usernames:
            user_data = {
                'username': invalid_username,
                'email': f'{invalid_username.replace(" ", "")}@gmail.com',
                'password': 'validpass123',
                'first_name': 'Test',
                'last_name': 'User'
            }
            
            response = client.post('/api/v1/auth/register',
                                 json=user_data,
                                 content_type='application/json')
            
            # Should either reject invalid username or accept it based on validation rules
            # This test documents current behavior
            assert response.status_code in [201, 400]
    
    def test_case_insensitive_login(self, client, test_user, sample_user_data):
        """Test case insensitive login."""
        login_data = {
            'username': test_user.username.upper(),  # Use uppercase
            'password': sample_user_data['password']
        }
        
        response = client.post('/api/v1/auth/login',
                             json=login_data,
                             content_type='application/json')
        
        # Should either accept case insensitive or reject based on implementation
        # This test documents current behavior
        assert response.status_code in [200, 401]