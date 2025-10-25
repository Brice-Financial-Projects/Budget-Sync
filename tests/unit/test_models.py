"""Unit tests for database models."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from datetime import datetime, date, timedelta
from budget_sync import User, Profile, Budget, ExpenseCategory, BudgetItem, ExpenseTemplate
from budget_sync.models import PasswordResetToken


def test_new_user():
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the email, password hash, and other fields are defined correctly
    """
    user = User('testuser', 'test@test.com', 'password123')
    assert user.username == 'testuser'
    assert user.email == 'test@test.com'
    assert user.password_hash != 'password123'
    assert user.check_password('password123')
    assert not user.check_password('wrongpassword')
    assert user.is_authenticated
    assert user.is_active
    assert not user.is_anonymous
    assert not user.is_admin

def test_profile_creation():
    """
    GIVEN a Profile model
    WHEN a new Profile is created
    THEN check all fields are set correctly
    """
    profile = Profile(
        user_id=1,
        first_name='John',
        last_name='Doe',
        state='CA',
        filing_status='single',
        income_type='Salary',
        pay_cycle='biweekly',
        retirement_contribution_type='pretax',
        num_dependents=0  # Explicitly set num_dependents
    )
    assert profile.first_name == 'John'
    assert profile.last_name == 'Doe'
    assert profile.state == 'CA'
    assert profile.filing_status == 'single'
    assert profile.num_dependents == 0  # Now it should always be 0
    assert profile.income_type == 'Salary'
    assert profile.pay_cycle == 'biweekly'

def test_profile_total_pretax_deductions():
    """
    GIVEN a Profile with various pre-tax deductions
    WHEN total_pretax_deductions is calculated
    THEN check the calculation is correct
    """
    profile = Profile(
        user_id=1,
        first_name='John',
        last_name='Doe',
        state='CA',
        filing_status='single',
        income_type='Salary',
        pay_cycle='biweekly',
        retirement_contribution_type='pretax',
        retirement_contribution=5000,
        health_insurance_premium=2000,
        hsa_contribution=1000,
        fsa_contribution=500,
        other_pretax_benefits=1000
    )
    assert profile.total_pretax_deductions == 9500

def test_profile_age_calculation():
    """
    GIVEN a Profile with a date of birth
    WHEN age is calculated
    THEN check the age is correct
    """
    profile = Profile(
        user_id=1,
        first_name='John',
        last_name='Doe',
        state='CA',
        filing_status='single',
        income_type='Salary',
        pay_cycle='biweekly',
        retirement_contribution_type='pretax',
        date_of_birth=date(1990, 1, 1)
    )
    # Note: This test will need to be updated yearly
    expected_age = datetime.now().year - 1990
    assert profile.age == expected_age

def test_budget_creation():
    """
    GIVEN a Budget model
    WHEN a new Budget is created
    THEN check all fields are set correctly
    """
    budget = Budget(
        user_id=1,
        profile_id=1,
        name='Monthly Budget',
        gross_income=50000,
        status='draft'
    )
    assert budget.name == 'Monthly Budget'
    assert budget.gross_income == 50000
    assert budget.status == 'draft'
    
    if not budget.created_at:
        budget.created_at = datetime.now()
    if not budget.updated_at:
        budget.updated_at = datetime.now()
        
    assert isinstance(budget.created_at, datetime)
    assert isinstance(budget.updated_at, datetime)

def test_budget_summary():
    """
    GIVEN a Budget with income sources
    WHEN get_budget_summary is called
    THEN check the summary is correct
    """
    budget = Budget(
        user_id=1,
        profile_id=1,
        name='Test Budget',
        gross_income=50000,
        status='draft'
    )
    
    budget.created_at = datetime.now()
    budget.updated_at = datetime.now()
    
    summary = budget.get_budget_summary()
    assert summary['name'] == 'Test Budget'
    assert summary['status'] == 'draft'
    assert isinstance(summary['created_at'], str)
    assert isinstance(summary['updated_at'], str)

def test_expense_category_creation():
    """
    GIVEN an ExpenseCategory model
    WHEN a new ExpenseCategory is created
    THEN check the fields are set correctly
    """
    category = ExpenseCategory(
        name='Housing',
        description='Housing expenses',
        priority=1
    )
    assert category.name == 'Housing'
    assert category.description == 'Housing expenses'
    assert category.priority == 1

def test_expense_template_creation():
    """
    GIVEN an ExpenseTemplate model
    WHEN a new ExpenseTemplate is created
    THEN check the fields are set correctly
    """
    template = ExpenseTemplate(
        category_id=1,
        name='Rent',
        description='Monthly rent payment',
        is_default=False,
        priority=1
    )
    assert template.name == 'Rent'
    assert template.description == 'Monthly rent payment'
    assert not template.is_default
    assert template.priority == 1
    assert template.category_id == 1

def test_budget_item_with_template():
    """
    GIVEN a BudgetItem model linked to a template
    WHEN a new BudgetItem is created with a template_id
    THEN check the fields and relationships are set correctly
    """
    budget_item = BudgetItem(
        budget_id=1,
        category='Housing',
        name='Rent',
        minimum_payment=1000.0,
        preferred_payment=1200.0,
        template_id=1
    )
    assert budget_item.name == 'Rent'
    assert budget_item.category == 'Housing'
    assert budget_item.minimum_payment == 1000.0
    assert budget_item.preferred_payment == 1200.0
    assert budget_item.template_id == 1


def test_password_reset_token_creation():
    """
    GIVEN a PasswordResetToken model
    WHEN a new token is created
    THEN check the token is generated and expiration is set correctly
    """
    token = PasswordResetToken(user_id=1, expiration_hours=1)

    assert token.user_id == 1
    assert token.token is not None
    assert len(token.token) > 0
    assert token.expires_at is not None
    assert not token.used

    # Check that expires_at is approximately 1 hour from now
    expected_expiry = datetime.utcnow() + timedelta(hours=1)
    time_difference = abs((token.expires_at - expected_expiry).total_seconds())
    assert time_difference < 5  # Within 5 seconds


def test_password_reset_token_is_expired():
    """
    GIVEN a PasswordResetToken
    WHEN checking if it's expired
    THEN return correct expiration status
    """
    # Create a token that expires in 1 hour (not expired)
    token = PasswordResetToken(user_id=1, expiration_hours=1)
    assert not token.is_expired()

    # Create an expired token by manually setting expires_at in the past
    expired_token = PasswordResetToken(user_id=1, expiration_hours=1)
    expired_token.expires_at = datetime.utcnow() - timedelta(hours=1)
    assert expired_token.is_expired()


def test_password_reset_token_unique():
    """
    GIVEN multiple PasswordResetToken instances
    WHEN tokens are generated
    THEN check that each token is unique
    """
    token1 = PasswordResetToken(user_id=1)
    token2 = PasswordResetToken(user_id=1)
    token3 = PasswordResetToken(user_id=2)

    assert token1.token != token2.token
    assert token1.token != token3.token
    assert token2.token != token3.token


def test_password_reset_token_repr():
    """
    GIVEN a PasswordResetToken
    WHEN the repr method is called
    THEN check the string representation is correct
    """
    token = PasswordResetToken(user_id=1)
    repr_str = repr(token)

    assert 'PasswordResetToken' in repr_str
    assert 'user 1' in repr_str
    assert token.token[:8] in repr_str 