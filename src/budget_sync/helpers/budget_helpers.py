"""budget_sync/helpers/budget_helpers.py"""

def get_category_name(category_type, item_id):
    """Helper function to map category IDs to names"""
    category_mapping = {
        'housing': {
            'rent': 'Rent/Mortgage',
            'property_tax': 'Property Tax',
            'hoa': 'HOA Fee',
            'home_insurance': 'Home Insurance',
            'home_repairs': 'Home Repairs'
        },
        'utility': {
            'electricity': 'Electricity',
            'water': 'Water',
            'gas': 'Gas',
            'trash': 'Trash',
            'sewer': 'Sewer'
        },
        'bill': {
            'internet': 'Internet',
            'cell_phone': 'Cell Phone',
            'cable': 'Cable/Streaming',
            'insurance': 'Insurance',
            'gym': 'Gym Membership',
            'cloud_storage': 'Cloud Storage'
        },
        'transport': {
            'car_payment': 'Car Payment',
            'car_insurance': 'Car Insurance',
            'fuel': 'Fuel',
            'maintenance': 'Maintenance',
            'public_transport': 'Public Transportation'
        }
        # Add more category types as needed
    }

    # If category type exists in mapping and item_id exists in that type
    if category_type in category_mapping and item_id in category_mapping[category_type]:
        return category_mapping[category_type][item_id]

    # Fallback: return the item_id with spaces and capitalization
    return item_id.replace('_', ' ').title()

def populate_expense_categories(db):
    """Populate the database with predefined expense categories and templates."""
    from flask import current_app
    from budget_sync.models import ExpenseCategory, ExpenseTemplate

    
    with current_app.app_context():
        # Check if categories already exist
        existing = db.session.query(ExpenseCategory.id).first()
        if existing:
            return  # already populated
        # Check if categories already exist
        if ExpenseCategory.query.first():
            return  # Categories already populated

        # Define categories and their expenses
        categories = [
            {
                'name': 'Housing',
                'description': 'Housing related expenses',
                'priority': 1,
                'expenses': [
                    {'name': 'Rent', 'description': 'Monthly rent payment', 'priority': 1},
                    {'name': 'Mortgage', 'description': 'Monthly mortgage payment', 'priority': 2},
                    {'name': 'Property Tax', 'description': 'Property tax payments', 'priority': 3},
                    {'name': 'HOA Fee', 'description': 'Homeowners association fees', 'priority': 4},
                    {'name': 'Home Insurance', 'description': 'Home insurance premiums', 'priority': 5},
                    {'name': 'Home Repairs', 'description': 'Home maintenance and repairs', 'priority': 6},
                    {'name': 'Renters Insurance', 'description': 'Renters insurance premiums', 'priority': 7}
                ]
            },
            {
                'name': 'Utilities',
                'description': 'Utility bills',
                'priority': 2,
                'expenses': [
                    {'name': 'Electricity', 'description': 'Electricity bill', 'priority': 1},
                    {'name': 'Water', 'description': 'Water bill', 'priority': 2},
                    {'name': 'Gas', 'description': 'Natural gas bill', 'priority': 3},
                    {'name': 'Trash', 'description': 'Trash collection service', 'priority': 4},
                    {'name': 'Sewer', 'description': 'Sewer service', 'priority': 5},
                    {'name': 'Internet', 'description': 'Internet service', 'priority': 6},
                    {'name': 'Cable/Satellite TV', 'description': 'Cable or satellite television', 'priority': 7},
                    {'name': 'Phone', 'description': 'Landline phone service', 'priority': 8}
                ]
            },
            {
                'name': 'Transportation',
                'description': 'Transportation expenses',
                'priority': 3,
                'expenses': [
                    {'name': 'Car Payment', 'description': 'Vehicle loan or lease payment', 'priority': 1},
                    {'name': 'Car Insurance', 'description': 'Auto insurance premiums', 'priority': 2},
                    {'name': 'Fuel', 'description': 'Gasoline or charging costs', 'priority': 3},
                    {'name': 'Public Transportation', 'description': 'Bus, subway, train fares', 'priority': 4},
                    {'name': 'Car Maintenance', 'description': 'Vehicle repairs and maintenance', 'priority': 5},
                    {'name': 'Parking', 'description': 'Parking fees', 'priority': 6},
                    {'name': 'Tolls', 'description': 'Road and bridge tolls', 'priority': 7},
                    {'name': 'Rideshare', 'description': 'Uber, Lyft, etc.', 'priority': 8}
                ]
            },
            {
                'name': 'Food',
                'description': 'Food expenses',
                'priority': 4,
                'expenses': [
                    {'name': 'Groceries', 'description': 'Food purchased for home', 'priority': 1},
                    {'name': 'Dining Out', 'description': 'Restaurant meals', 'priority': 2},
                    {'name': 'Coffee Shops', 'description': 'Coffee shops and cafes', 'priority': 3},
                    {'name': 'Food Delivery', 'description': 'Food delivery services', 'priority': 4},
                    {'name': 'Meal Kits', 'description': 'Meal subscription services', 'priority': 5}
                ]
            },
            {
                'name': 'Health & Wellness',
                'description': 'Health and wellness expenses',
                'priority': 5,
                'expenses': [
                    {'name': 'Health Insurance', 'description': 'Health insurance premiums', 'priority': 1},
                    {'name': 'Dental Insurance', 'description': 'Dental insurance premiums', 'priority': 2},
                    {'name': 'Vision Insurance', 'description': 'Vision insurance premiums', 'priority': 3},
                    {'name': 'Prescriptions', 'description': 'Prescription medications', 'priority': 4},
                    {'name': 'Gym Membership', 'description': 'Fitness club fees', 'priority': 5},
                    {'name': 'Therapy', 'description': 'Mental health counseling', 'priority': 6},
                    {'name': 'Medical Bills', 'description': 'Medical expenses not covered by insurance', 'priority': 7}
                ]
            },
            {
                'name': 'Debt Payments',
                'description': 'Debt payment expenses',
                'priority': 6,
                'expenses': [
                    {'name': 'Credit Card 1', 'description': 'Credit card minimum payment', 'priority': 1},
                    {'name': 'Credit Card 2', 'description': 'Credit card minimum payment', 'priority': 2},
                    {'name': 'Credit Card 3', 'description': 'Credit card minimum payment', 'priority': 3},
                    {'name': 'Student Loan', 'description': 'Student loan payment', 'priority': 4},
                    {'name': 'Personal Loan', 'description': 'Personal loan payment', 'priority': 5},
                    {'name': 'Medical Debt', 'description': 'Medical debt payment', 'priority': 6},
                    {'name': 'Other Loan', 'description': 'Other loan payment', 'priority': 7}
                ]
            },
            {
                'name': 'Subscriptions & Services',
                'description': 'Recurring subscriptions and services',
                'priority': 7,
                'expenses': [
                    {'name': 'Cell Phone', 'description': 'Mobile phone service', 'priority': 1},
                    {'name': 'Streaming Service 1', 'description': 'Video streaming service', 'priority': 2},
                    {'name': 'Streaming Service 2', 'description': 'Video streaming service', 'priority': 3},
                    {'name': 'Streaming Service 3', 'description': 'Video streaming service', 'priority': 4},
                    {'name': 'Music Streaming', 'description': 'Music streaming service', 'priority': 5},
                    {'name': 'Cloud Storage', 'description': 'Online storage service', 'priority': 6},
                    {'name': 'Software Subscriptions', 'description': 'Software as a service', 'priority': 7},
                    {'name': 'Membership Fees', 'description': 'Club memberships', 'priority': 8}
                ]
            },
            {
                'name': 'Insurance',
                'description': 'Insurance expenses',
                'priority': 8,
                'expenses': [
                    {'name': 'Life Insurance', 'description': 'Life insurance premiums', 'priority': 1},
                    {'name': 'Disability Insurance', 'description': 'Disability insurance premiums', 'priority': 2},
                    {'name': 'Umbrella Insurance', 'description': 'Umbrella liability insurance', 'priority': 3},
                    {'name': 'Pet Insurance', 'description': 'Pet health insurance', 'priority': 4}
                ]
            },
            {
                'name': 'Children & Dependents',
                'description': 'Expenses for children and dependents',
                'priority': 9,
                'expenses': [
                    {'name': 'Childcare', 'description': 'Daycare or babysitting', 'priority': 1},
                    {'name': 'School Tuition', 'description': 'School fees', 'priority': 2},
                    {'name': 'School Supplies', 'description': 'Educational supplies', 'priority': 3},
                    {'name': 'Extracurricular Activities', 'description': 'Sports, music lessons, etc.', 'priority': 4},
                    {'name': 'Child Support', 'description': 'Child support payments', 'priority': 5},
                    {'name': 'Adult Dependent Care', 'description': 'Care for adult dependents', 'priority': 6}
                ]
            },
            {
                'name': 'Savings & Investments',
                'description': 'Savings and investments',
                'priority': 10,
                'expenses': [
                    {'name': 'Emergency Fund', 'description': 'Savings for emergencies', 'priority': 1},
                    {'name': 'Retirement Contribution', 'description': 'Contribution to retirement accounts', 'priority': 2},
                    {'name': 'Investment Contribution', 'description': 'Contribution to investment accounts', 'priority': 3},
                    {'name': 'Education Savings', 'description': 'College savings plan', 'priority': 4},
                    {'name': 'Sinking Funds', 'description': 'Savings for future expenses', 'priority': 5}
                ]
            },
            {
                'name': 'Discretionary Spending',
                'description': 'Discretionary and entertainment expenses',
                'priority': 11,
                'expenses': [
                    {'name': 'Entertainment', 'description': 'Movies, concerts, events', 'priority': 1},
                    {'name': 'Shopping', 'description': 'Clothing and personal items', 'priority': 2},
                    {'name': 'Hobbies', 'description': 'Hobby-related expenses', 'priority': 3},
                    {'name': 'Gifts', 'description': 'Gifts for others', 'priority': 4},
                    {'name': 'Travel', 'description': 'Vacation and travel expenses', 'priority': 5},
                    {'name': 'Personal Care', 'description': 'Haircuts, salon services, etc.', 'priority': 6},
                    {'name': 'Pet Expenses', 'description': 'Pet food, supplies, and vet care', 'priority': 7}
                ]
            },
            {
                'name': 'Taxes',
                'description': 'Tax payments',
                'priority': 12,
                'expenses': [
                    {'name': 'Income Tax', 'description': 'Additional income tax payments', 'priority': 1},
                    {'name': 'Self-Employment Tax', 'description': 'Self-employment tax payments', 'priority': 2},
                    {'name': 'Estimated Tax Payments', 'description': 'Quarterly estimated tax payments', 'priority': 3}
                ]
            },
            {
                'name': 'Other Expenses',
                'description': 'Other miscellaneous expenses',
                'priority': 13,
                'expenses': [
                    {'name': 'Charitable Donations', 'description': 'Donations to charities', 'priority': 1},
                    {'name': 'Professional Services', 'description': 'Lawyer, accountant, etc.', 'priority': 2},
                    {'name': 'Business Expenses', 'description': 'Business-related costs', 'priority': 3},
                    {'name': 'Other', 'description': 'Other miscellaneous expenses', 'priority': 4}
                ]
            }
        ]
    
    # Create and save categories and their expenses
    for category_data in categories:
        category = ExpenseCategory(
            name=category_data['name'],
            description=category_data['description'],
            priority=category_data['priority']
        )
        db.session.add(category)
        db.session.flush()  # Flush to get the category ID
        
        # Create and save expenses for this category
        for expense_data in category_data['expenses']:
            expense = ExpenseTemplate(
                category_id=category.id,
                name=expense_data['name'],
                description=expense_data['description'],
                priority=expense_data['priority'],
                is_default=False  # Default all to off
            )
            db.session.add(expense)
    
    # Commit all changes
    db.session.commit()
