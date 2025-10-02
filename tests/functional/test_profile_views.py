"""Test profile routes and functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_profile_page(auth_client, test_profile):
    """Test profile page loads."""
    response = auth_client.get('/profile')
    assert response.status_code == 200
    assert b'Test User' in response.data
    assert b'CA' in response.data

def test_create_profile(auth_client):
    """Test profile creation."""
    response = auth_client.post('/profile', data={
        'first_name': 'John',
        'last_name': 'Doe',
        'state': 'NY',
        'filing_status': 'single',
        'num_dependents': 0,
        'income_type': 'Salary',
        'pay_cycle': 'monthly',
        'retirement_contribution_type': 'pretax',
        'retirement_contribution': 5000,
        'health_insurance_premium': 2000,
        'hsa_contribution': 1000,
        'fsa_contribution': 500,
        'other_pretax_benefits': 1000,
        'federal_additional_withholding': 100,
        'state_additional_withholding': 50
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'John Doe' in response.data
    assert b'NY' in response.data

def test_update_profile(auth_client, test_profile):
    """Test profile update."""
    response = auth_client.post('/profile', data={
        'first_name': 'Jane',
        'last_name': 'Smith',
        'state': 'CA',
        'filing_status': 'single',
        'num_dependents': 0,
        'income_type': 'Salary',
        'pay_cycle': 'monthly',
        'retirement_contribution_type': 'pretax',
        'retirement_contribution': 6000,
        'health_insurance_premium': 2500,
        'hsa_contribution': 1200,
        'fsa_contribution': 600,
        'other_pretax_benefits': 1200,
        'federal_additional_withholding': 150,
        'state_additional_withholding': 75
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Jane Smith' in response.data
    assert b'CA' in response.data
    assert b'6000' in response.data
    assert b'2500' in response.data

def test_profile_form_validation(auth_client):
    """Test profile form validation."""
    response = auth_client.post('/profile', data={
        'first_name': '',  # Empty first name should fail validation
        'last_name': '',   # Empty last name should fail validation
        'state': 'XXX',   # Invalid state code
        'filing_status': 'invalid',  # Invalid filing status
        'income_type': 'invalid',    # Invalid income type
        'pay_cycle': 'invalid',      # Invalid pay cycle
        'retirement_contribution_type': 'invalid'  # Invalid contribution type
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'First Name' in response.data
    assert b'Last Name' in response.data
    assert b'State Code' in response.data
    assert b'Filing Status' in response.data
    assert b'Income Type' in response.data
    assert b'Pay Cycle' in response.data
    assert b'Retirement Contribution Type' in response.data

def test_profile_required_fields(auth_client):
    """Test that required profile fields are enforced."""
    response = auth_client.post('/profile', data={
        'first_name': 'John',
        'last_name': 'Doe'
        # Missing required fields
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'State is required' in response.data
    assert b'Filing Status is required' in response.data
    assert b'Income Type is required' in response.data
    assert b'Pay Cycle is required' in response.data
    assert b'Retirement Contribution Type is required' in response.data

def test_profile_retirement_contribution_types(auth_client):
    """Test retirement contribution type validation."""
    response = auth_client.post('/profile/create', data={
        'first_name': 'John',
        'last_name': 'Doe',
        'state': 'NY',
        'retirement_contribution': 5000,
        'retirement_contribution_type': 'invalid_type'  # Invalid contribution type
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invalid retirement contribution type' in response.data 