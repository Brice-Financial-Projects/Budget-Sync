"""Functional tests for authentication views."""
import pytest
from flask import url_for

def test_register_page(client):
    """Test registration page loads."""
    response = client.get('/auth/register')
    assert response.status_code == 200
    assert b'Register' in response.data

def test_login_page(client):
    """Test login page loads."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_register_user(client):
    """Test user registration."""
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Account created successfully' in response.data

def test_login_user(client, test_user):
    """Test user login."""
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'testpass123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome' in response.data

def test_logout(auth_client):
    """Test user logout."""
    response = auth_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data

def test_protected_route(client):
    """Test protected route redirects to login."""
    response = client.get('/budget/create', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data 