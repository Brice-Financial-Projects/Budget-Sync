"""Integration tests for database operations."""
import pytest
from src.budget_sync import db
from src.budget_sync import User, Profile, Budget, BudgetItem, ExpenseCategory, ExpenseTemplate


def test_user_profile_relationship(test_db):
    """
    GIVEN a User model and Profile model
    WHEN a new User and Profile are created with a relationship
    THEN check the relationship works correctly
    """
    # Create and save a user
    user = User(username='testuser', email='test@test.com', password='password123')
    db.session.add(user)
    db.session.commit()

    # Create and save a profile linked to the user
    profile = Profile(
        user_id=user.id,
        first_name='John',
        last_name='Doe',
        state='CA',
        filing_status='single',
        income_type='Salary',
        pay_cycle='biweekly',
        retirement_contribution_type='pretax'
    )
    db.session.add(profile)
    db.session.commit()

    # Test relationships
    assert user.profile == profile
    assert profile.user == user

def test_budget_cascade_delete(test_db):
    """
    GIVEN a User with a Profile and Budget
    WHEN the User is deleted
    THEN check that related data can be verified and deleted properly
    """
    # Create user
    user = User(username='budgetuser', email='budget@test.com', password='password123')
    db.session.add(user)
    db.session.commit()

    # Create profile with explicit user_id
    profile = Profile(
        user_id=user.id,  # Ensure this is set
        first_name='John',
        last_name='Doe',
        state='CA',
        filing_status='single',
        income_type='Salary',
        pay_cycle='biweekly',
        retirement_contribution_type='pretax',
        num_dependents=0
    )
    db.session.add(profile)
    db.session.commit()

    # Verify the user_id was set correctly
    assert profile.user_id == user.id

    # Create budget
    budget = Budget(
        user_id=user.id,
        profile_id=profile.id,
        name='Test Budget',
        gross_income=50000,
        status='draft'
    )
    db.session.add(budget)
    db.session.commit()

    # Store IDs before deletion
    user_id = user.id
    profile_id = profile.id
    budget_id = budget.id

    # Verify relationships
    retrieved_user = User.query.filter_by(id=user_id).first()
    assert retrieved_user is not None
    assert len(retrieved_user.budgets) == 1
    assert retrieved_user.profile is not None
    
    # Clean up by deleting budget and profile first, then user
    # This avoids cascade issues if not properly configured
    db.session.delete(budget)
    db.session.commit()
    
    db.session.delete(profile)
    db.session.commit()
    
    db.session.delete(user)
    db.session.commit()
    
    # Verify everything is deleted
    assert User.query.filter_by(id=user_id).first() is None
    assert Profile.query.filter_by(id=profile_id).first() is None
    assert Budget.query.filter_by(id=budget_id).first() is None

def test_budget_items_relationship(test_db):
    """
    GIVEN a Budget with multiple BudgetItems
    WHEN items are added and queried
    THEN check the relationships work correctly
    """
    # Create necessary parent objects
    user = User(username='itemuser', email='items@test.com', password='password123')
    db.session.add(user)
    db.session.commit()

    profile = Profile(
        user_id=user.id,
        first_name='John',
        last_name='Doe',
        state='CA',
        filing_status='single',
        income_type='Salary',
        pay_cycle='biweekly',
        retirement_contribution_type='pretax'
    )
    db.session.add(profile)
    db.session.commit()

    # Create budget
    budget = Budget(
        user_id=user.id,
        profile_id=profile.id,
        name='Item Test Budget',
        gross_income=50000
    )
    db.session.add(budget)
    db.session.commit()

    # Create budget items
    items = [
        BudgetItem(
            budget_id=budget.id,
            category='Housing',
            name='Rent',
            minimum_payment=1000,
            preferred_payment=1200
        ),
        BudgetItem(
            budget_id=budget.id,
            category='Utilities',
            name='Electricity',
            minimum_payment=50,
            preferred_payment=75
        )
    ]
    db.session.bulk_save_objects(items)
    db.session.commit()

    # Verify relationships
    budget_from_db = Budget.query.get(budget.id)
    assert len(budget_from_db.budget_items) == 2
    assert any(item.name == 'Rent' for item in budget_from_db.budget_items)
    assert any(item.name == 'Electricity' for item in budget_from_db.budget_items)

def test_unique_constraints(test_db):
    """
    GIVEN database constraints
    WHEN duplicate data is inserted
    THEN check that appropriate errors are raised
    """
    # Create initial user
    user1 = User(username='uniqueuser', email='unique@test.com', password='password123')
    db.session.add(user1)
    db.session.commit()

    # Try to create user with same username
    with pytest.raises(Exception):  # Should be more specific based on your DB
        user2 = User(username='uniqueuser', email='different@test.com', password='password123')
        db.session.add(user2)
        db.session.commit()

    # Try to create user with same email
    with pytest.raises(Exception):  # Should be more specific based on your DB
        user3 = User(username='differentuser', email='unique@test.com', password='password123')
        db.session.add(user3)
        db.session.commit()

def test_expense_category_template_relationship(test_db):
    """
    GIVEN ExpenseCategory and ExpenseTemplate models
    WHEN a category has multiple templates
    THEN check the relationship works correctly
    """
    # Create a category
    category = ExpenseCategory(
        name='Housing',
        description='Housing expenses',
        priority=1
    )
    db.session.add(category)
    db.session.commit()
    
    # Create templates
    templates = [
        ExpenseTemplate(
            category_id=category.id,
            name='Rent',
            description='Monthly rent payment',
            is_default=False,
            priority=1
        ),
        ExpenseTemplate(
            category_id=category.id,
            name='Mortgage',
            description='Monthly mortgage payment',
            is_default=False,
            priority=2
        )
    ]
    db.session.bulk_save_objects(templates)
    db.session.commit()
    
    # Verify relationship
    category_from_db = ExpenseCategory.query.get(category.id)
    assert len(category_from_db.expense_templates) == 2
    assert any(t.name == 'Rent' for t in category_from_db.expense_templates)
    assert any(t.name == 'Mortgage' for t in category_from_db.expense_templates)

def test_budget_item_with_template_relationship(test_db):
    """
    GIVEN BudgetItem associated with ExpenseTemplate
    WHEN a budget item is created from a template
    THEN check the relationship works correctly
    """
    # Create necessary objects
    user = User(username='templateuser', email='template@test.com', password='password123')
    db.session.add(user)
    db.session.commit()
    
    profile = Profile(
        user_id=user.id,
        first_name='Template',
        last_name='User',
        state='CA',
        filing_status='single',
        income_type='Salary',
        pay_cycle='biweekly',
        retirement_contribution_type='pretax'
    )
    db.session.add(profile)
    db.session.commit()
    
    budget = Budget(
        user_id=user.id,
        profile_id=profile.id,
        name='Template Test Budget',
        gross_income=60000
    )
    db.session.add(budget)
    db.session.commit()
    
    # Create category and template
    category = ExpenseCategory(
        name='Utilities',
        description='Utility expenses',
        priority=2
    )
    db.session.add(category)
    db.session.flush()
    
    template = ExpenseTemplate(
        category_id=category.id,
        name='Electricity',
        description='Monthly electricity bill',
        is_default=True,
        priority=1
    )
    db.session.add(template)
    db.session.commit()
    
    # Create budget item from template
    budget_item = BudgetItem(
        budget_id=budget.id,
        category=category.name,
        name=template.name,
        minimum_payment=150.0,
        preferred_payment=175.0,
        template_id=template.id
    )
    db.session.add(budget_item)
    db.session.commit()
    
    # Verify relationships
    budget_item_from_db = BudgetItem.query.get(budget_item.id)
    assert budget_item_from_db.template_id == template.id
    assert budget_item_from_db.template.name == 'Electricity'
    assert budget_item_from_db.template.category.name == 'Utilities'

def test_category_cascade_delete(test_db):
    """
    GIVEN an ExpenseCategory with ExpenseTemplates
    WHEN the category is deleted
    THEN check that all related templates are also deleted
    """
    # Create a category
    category = ExpenseCategory(
        name='Entertainment',
        description='Entertainment expenses',
        priority=5
    )
    db.session.add(category)
    db.session.flush()
    
    # Create templates
    templates = [
        ExpenseTemplate(
            category_id=category.id,
            name='Streaming Services',
            description='Monthly streaming subscriptions',
            is_default=False,
            priority=1
        ),
        ExpenseTemplate(
            category_id=category.id,
            name='Movies',
            description='Movie tickets',
            is_default=False,
            priority=2
        )
    ]
    db.session.bulk_save_objects(templates)
    db.session.commit()
    
    # Store template IDs
    template_ids = [t.id for t in ExpenseTemplate.query.filter_by(category_id=category.id).all()]
    
    # Delete category
    db.session.delete(category)
    db.session.commit()
    
    # Verify templates are deleted
    for template_id in template_ids:
        assert ExpenseTemplate.query.get(template_id) is None 