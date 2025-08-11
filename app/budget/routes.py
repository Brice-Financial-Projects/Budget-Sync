"""backend/app/budget/routes.py."""

from flask import Blueprint, render_template, request, redirect, current_app, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Budget, BudgetItem, Profile, GrossIncome, ExpenseCategory, ExpenseTemplate
from app.forms import BudgetForm, IncomeForm
from app.budget.budget_logic import BudgetCalculator
from contextlib import contextmanager
from datetime import datetime
from app.forms import CategorySelectionForm
from app.helpers.budget_helpers import get_category_name
from flask_wtf import FlaskForm
from wtforms import SubmitField
from app.forms import EditBudgetForm




budget_bp = Blueprint('budget', __name__, template_folder='budget')

@budget_bp.route('/input', methods=['GET', 'POST'])
@login_required
def input_budget():
    if not current_user.profile:
        flash("Please complete your profile before creating a budget.", "warning")
        return redirect(url_for('profile.profile'))

    categories = session.get('categories', {})
    print("DEBUG: Retrieved categories from session:", categories)
    
    if not categories:
        flash("No categories found. Please start by creating your budget.", "warning")
        return redirect(url_for('budget.budget_name'))

    form = BudgetForm()

    if request.method == 'POST':
        print("✅ Budget input form submitted!")  

        # Step 1: Collect budget details from form inputs
        budget_details = {}
        for category, items in categories.items():
            budget_details[category] = {}
            for item in items:
                min_payment = request.form.get(f'min_{item}', 0)
                pref_payment = request.form.get(f'pref_{item}', 0)
                budget_details[category][item] = {
                    'min_payment': float(min_payment),
                    'pref_payment': float(pref_payment)
                }
                print(f"DEBUG: Captured {item}: Min={min_payment}, Pref={pref_payment}")

        # Step 2: Create Budget and store it
        try:
            new_budget = Budget(
                user_id=current_user.id,
                profile_id=current_user.profile.id,
                name=session.get('budget_name', "My New Budget"),
                gross_income=(form.income.data if form.income.data is not None else 0),
                retirement_contribution=current_user.profile.retirement_contribution,
                benefit_deductions=current_user.profile.benefit_deductions
            )
            db.session.add(new_budget)
            db.session.commit()  # ✅ FIX: Ensure the budget is actually saved!
            print(f"DEBUG: New Budget Created with ID: {new_budget.id}")
        except Exception as e:
            db.session.rollback()
            print(f"ERROR: Error creating Budget: {e}")
            flash("An error occurred while saving your budget. Please try again.", "danger")
            return redirect(url_for('budget.input_budget'))

        # Step 3: Save Budget Items
        for category, items in budget_details.items():
            for item, payments in items.items():
                try:
                    budget_item = BudgetItem(
                        category=category,
                        name=item,
                        minimum_payment=payments['min_payment'],
                        preferred_payment=payments['pref_payment'],
                        budget_id=new_budget.id
                    )
                    db.session.add(budget_item)
                except Exception as e:
                    print(f"ERROR: Error creating BudgetItem for '{item}': {e}")

        # Step 4: Final commit for Budget Items
        try:
            db.session.commit()
            print("DEBUG: All budget items saved successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"ERROR: Error saving budget items: {e}")
            flash("An error occurred while saving budget items. Please try again.", "danger")
            return redirect(url_for('budget.input_budget'))

        # Step 5: Store for Results Page
        session['budget_details'] = budget_details
        session.modified = True
        flash("Budget details successfully captured. Proceed to income input.", "success")
        return redirect(url_for('budget.income'))  # ✅ Redirecting to Income Entry!

    print("DEBUG: GET request received - Rendering Budget Input Form")
    return render_template('budget/budget_input.html', categories=categories, form=form)


@budget_bp.route('/income', methods=['GET', 'POST'])
@login_required
def income():
    form = IncomeForm()
    profile = Profile.query.filter_by(user_id=current_user.id).first()

    if not profile:
        flash("Please complete your profile before entering income details.", "warning")
        return redirect(url_for('profile.profile'))

    # Get the budget ID from session
    budget_id = session.get('budget_id')
    if not budget_id:
        flash("No active budget found. Please create a budget first.", "warning")
        return redirect(url_for('budget.budget_name'))
        
    # Get the budget using the ID from session
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first()
    
    if not budget:
        flash("Budget not found. Please create a budget first.", "warning")
        return redirect(url_for('budget.budget_name'))

    print(f"Current budget ID: {budget.id if budget else 'None'}")

    # Initialize the income_entries list - prevent UnboundLocalError
    income_entries = []
    
    primary_income = GrossIncome.query.filter_by(budget_id=budget.id, category="W2 Job").first()

    if request.method == 'POST':
        print("Form Data:", request.form)
        
        # Print CSRF tokens for debugging
        form_csrf = request.form.get('csrf_token') 
        expected_csrf = form.csrf_token.current_token
        print(f"CSRF DEBUG - Form token: {form_csrf}")
        print(f"CSRF DEBUG - Expected token: {expected_csrf}")
        
        # Use the proper CSRF validation method
        if form.validate_on_submit():
            try:
                print(f"====== PROCESSING INCOME FORM FOR BUDGET {budget.id} ======")
                
                # STEP 1: Handle primary income (W2 Job)
                if form.gross_income.data and form.gross_income_frequency.data:
                    if not primary_income:
                        primary_income = GrossIncome(
                            budget_id=budget.id,
                            category="W2 Job",
                            source="Primary Job",
                            gross_income=float(form.gross_income.data),  # Store raw amount
                            frequency=form.gross_income_frequency.data,
                            tax_type="W2",
                            state_tax_ref=profile.state
                        )
                        db.session.add(primary_income)
                    else:
                        primary_income.gross_income = float(form.gross_income.data)  # Store raw amount
                        primary_income.frequency = form.gross_income_frequency.data
                
                # STEP 2: Handle "other" income sources
                # Parse form data for other income sources
                other_income_count = int(request.form.get('other_income_count', 0))
                print(f"Other income sources: {other_income_count}")
                
                # Delete existing other income sources to avoid duplicates
                other_income_sources = GrossIncome.query.filter(
                    GrossIncome.budget_id == budget.id,
                    GrossIncome.category != "W2 Job"
                ).all()
                for source in other_income_sources:
                    db.session.delete(source)
                
                # Add new other income sources
                for i in range(other_income_count):
                    category = request.form.get(f'other_income_sources-{i}-category')
                    name = request.form.get(f'other_income_sources-{i}-name')
                    amount = request.form.get(f'other_income_sources-{i}-amount')
                    frequency = request.form.get(f'other_income_sources-{i}-frequency')
                    
                    if category and name and amount and frequency:
                        new_income = GrossIncome(
                            budget_id=budget.id,
                            category=category,
                            source=name,
                            gross_income=float(amount),  # Store raw amount
                            frequency=frequency,
                            tax_type="Other",  # Default tax type for other income
                            state_tax_ref=profile.state
                        )
                        db.session.add(new_income)
                        print(f"Added other income: {category} - {name} - ${amount} ({frequency})")
                
                # Commit all changes
                db.session.commit()
                
                # Update the budget with the income
                budget.gross_income = form.gross_income.data if form.gross_income.data else 0
                db.session.commit()
                
                flash("Income details saved! Now set your payment amounts.", "success")
                # Redirect to payment amounts page instead of preview
                return redirect(url_for('budget.set_payment_amounts', budget_id=budget.id))
            except Exception as e:
                print(f"ERROR: {str(e)}")
                db.session.rollback()
                flash(f"An error occurred while saving your income: {str(e)}", "danger")
                return redirect(url_for('budget.income'))

    # Pre-fill form with existing data
    if primary_income:
        form.gross_income.data = primary_income.gross_income
        form.gross_income_frequency.data = primary_income.frequency

    # Always regenerate a fresh CSRF token before rendering the form
    # This ensures that it matches what Flask-WTF expects
    form.csrf_token.data = form.csrf_token.current_token
    print(f"Generated fresh CSRF token: {form.csrf_token.current_token}")
    
    # Pull fresh data from database for display
    other_income = GrossIncome.query.filter(
        GrossIncome.budget_id == budget.id,
        GrossIncome.category != "W2 Job"
    ).all()

    print(f"Display: Found {len(other_income)} other income sources for budget {budget.id}:")
    for inc in other_income:
        print(f"  - {inc.source}: ${inc.gross_income} ({inc.frequency}) - Tax Type: {inc.tax_type}")
        income_entries.append({
            'category': inc.category,
            'name': inc.source,
            'amount': inc.gross_income,
            'frequency': inc.frequency
        })
    
    # Set main form fields
    if primary_income:
        form.gross_income.data = primary_income.gross_income
        form.gross_income_frequency.data = primary_income.frequency
    
    # Return the form without any empty entries if none exist in the database
    return render_template('budget/income.html', form=form, other_income=income_entries)


@budget_bp.route('/payments/<int:budget_id>', methods=['GET', 'POST'])
@login_required
def set_payment_amounts(budget_id):
    """Allow users to set minimum and preferred payment amounts for each expense."""
    # Check if budget exists and belongs to the current user
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    
    # Get all budget items for this budget
    budget_items = BudgetItem.query.filter_by(budget_id=budget_id).all()
    
    if not budget_items:
        flash("No expenses found for this budget. Please add expenses first.", "warning")
        return redirect(url_for('budget.select_expenses', budget_id=budget_id))
    
    # Simple form for CSRF protection
    class PaymentForm(FlaskForm):
        submit = SubmitField('Review Budget')
    
    form = PaymentForm()
    
    if request.method == 'POST':
        try:
            # Process payment amounts for each budget item
            for item in budget_items:
                min_payment_key = f"min_payment_{item.id}"
                pref_payment_key = f"pref_payment_{item.id}"
                
                # Get minimum payment (required)
                if min_payment_key in request.form:
                    min_payment = float(request.form[min_payment_key])
                    item.minimum_payment = min_payment
                
                # Get preferred payment (optional)
                if pref_payment_key in request.form:
                    pref_payment = float(request.form[pref_payment_key])
                    item.preferred_payment = pref_payment
            
            # Save all changes
            db.session.commit()
            flash("Payment amounts saved! Review your budget.", "success")
            return redirect(url_for('budget.preview'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while saving payment amounts: {str(e)}", "danger")
            return redirect(url_for('budget.set_payment_amounts', budget_id=budget_id))
    
    # Organize budget items by category for display
    items_by_category = {}
    for item in budget_items:
        if item.category not in items_by_category:
            items_by_category[item.category] = []
        items_by_category[item.category].append(item)
    
    # Create sorted categories list for UI
    sorted_categories = sorted(items_by_category.keys())
    
    return render_template('budget/payment_amounts.html',
                          form=form,
                          budget=budget,
                          items_by_category=items_by_category,
                          sorted_categories=sorted_categories)


@budget_bp.route('/view/<int:budget_id>', methods=['GET'])
@login_required
def view_budget(budget_id):
    """View an individual budget and its details."""
    budget = Budget.query.get_or_404(budget_id)
    
    if budget.user_id != current_user.id:
        flash("You are not authorized to view this budget.", "danger")
        return redirect(url_for('main.dashboard'))

    budget_items = BudgetItem.query.filter_by(budget_id=budget.id).all()

    return render_template('budget/view_budget.html', budget=budget, budget_items=budget_items)

@budget_bp.route('/edit/<int:budget_id>', methods=['GET', 'POST'])
@login_required
def edit_budget(budget_id):
    """Allow users to edit an existing budget."""
    budget = Budget.query.get_or_404(budget_id)
    
    if budget.user_id != current_user.id:
        flash("You are not authorized to edit this budget.", "danger")
        return redirect(url_for('main.dashboard'))
    
    # Get all budget items for this budget
    budget_items = BudgetItem.query.filter_by(budget_id=budget.id).all()
    
    # Create the main budget form
    form = EditBudgetForm(obj=budget)
    
    if form.validate_on_submit():
        try:
            # Update budget name
            budget.name = form.budget_name.data
            
            # Process budget item updates
            for item in budget_items:
                item_name_key = f"item_name_{item.id}"
                min_payment_key = f"min_payment_{item.id}"
                pref_payment_key = f"pref_payment_{item.id}"
                
                # Update item name if provided
                if item_name_key in request.form:
                    item.name = request.form[item_name_key]
                
                # Update minimum payment if provided
                if min_payment_key in request.form and request.form[min_payment_key]:
                    try:
                        item.minimum_payment = float(request.form[min_payment_key])
                    except ValueError:
                        flash(f"Invalid minimum payment for {item.name}", "danger")
                        continue
                
                # Update preferred payment if provided
                if pref_payment_key in request.form and request.form[pref_payment_key]:
                    try:
                        item.preferred_payment = float(request.form[pref_payment_key])
                    except ValueError:
                        flash(f"Invalid preferred payment for {item.name}", "danger")
                        continue
            
            db.session.commit()
            flash("Budget updated successfully!", "success")
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating your budget. Please try again.", "danger")
            print(f"Error updating budget: {str(e)}")
    
    return render_template('budget/edit_budget.html', form=form, budget=budget, budget_items=budget_items)


@budget_bp.route('/delete/<int:budget_id>', methods=['POST'])
@login_required
def delete_budget(budget_id):
    """Allow users to delete an existing budget."""
    budget = Budget.query.get_or_404(budget_id)

    if budget.user_id != current_user.id:
        flash("You do not have permission to delete this budget.", "danger")
        return redirect(url_for('main.dashboard'))
    
    try:
        db.session.delete(budget)
        db.session.commit()
        flash("Budget deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while deleting the budget. Please try again.", "danger")

    return redirect(url_for('main.dashboard'))


@budget_bp.route('/name', methods=['GET', 'POST'])
@login_required
def budget_name():
    # Check if user has a profile first
    if not current_user.profile:
        flash("Please complete your profile before creating a budget.", "warning")
        return redirect(url_for('profile.profile'))

    form = BudgetForm()

    # Clear session data related to previous budgets (except for income)
    session.pop('categories', None)
    session.pop('budget_name', None)
    session.pop('selected_expenses', None)  # Clear any previously selected expenses

    # Get all existing budgets for this user
    existing_budgets = Budget.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        budget_name = form.budget_name.data.strip()

        # Check if the budget name is already taken
        existing_budget = Budget.query.filter_by(user_id=current_user.id, name=budget_name).first()
        if existing_budget:
            flash("A budget with this name already exists. Please choose a different name.", "danger")
            return redirect(url_for('budget.budget_name'))

        # Create a new budget object and save it to the database
        try:
            new_budget = Budget(
                user_id=current_user.id,
                profile_id=current_user.profile.id,
                name=budget_name,
                status="draft"
            )
            db.session.add(new_budget)
            db.session.commit()
            
            # Store the budget ID in session
            session['budget_id'] = new_budget.id
            session['budget_name'] = budget_name
            session.modified = True
            
            flash("Budget created! Now select your expenses.", "success")
            # Redirect to the expense selection page
            return redirect(url_for('budget.select_expenses', budget_id=new_budget.id))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while creating your budget: {str(e)}", "danger")
            return redirect(url_for('budget.budget_name'))

    return render_template('budget/name.html', form=form, existing_budgets=existing_budgets)


@budget_bp.route('/select_expenses/<int:budget_id>', methods=['GET', 'POST'])
@login_required
def select_expenses(budget_id):
    """Let users select expenses from predefined templates."""
    # Check if budget exists and belongs to the current user
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    
    # Simple form for CSRF protection
    class ExpenseForm(FlaskForm):
        submit = SubmitField('Review Selections')
    
    form = ExpenseForm()
    
    if request.method == 'POST':
        selected_expense_ids = request.form.getlist('expenses')
        
        if not selected_expense_ids:
            flash("Please select at least one expense.", "warning")
            return redirect(url_for('budget.select_expenses', budget_id=budget_id))
        
        # Store selected expense IDs in session
        session['selected_expenses'] = selected_expense_ids
        session.modified = True
        
        flash("Expenses selected! Now you can personalize them.", "success")
        return redirect(url_for('budget.review_expenses', budget_id=budget_id))
    
    # Get all expense categories and their templates, ordered by priority
    categories = ExpenseCategory.query.order_by(ExpenseCategory.priority).all()
    
    # Prepare data for the template
    categories_data = []
    for category in categories:
        # Get all expense templates for this category, ordered by priority
        expenses = ExpenseTemplate.query.filter_by(category_id=category.id).order_by(ExpenseTemplate.priority).all()
        
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'expenses': expenses
        })
    
    return render_template('budget/expense_selection.html', 
                           form=form,
                           budget_id=budget_id,
                           categories=categories_data)


@budget_bp.route('/review_expenses/<int:budget_id>', methods=['GET', 'POST'])
@login_required
def review_expenses(budget_id):
    """Review and personalize selected expenses."""
    # Check if budget exists and belongs to the current user
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    
    # Get selected expense IDs from session
    selected_expense_ids = session.get('selected_expenses', [])
    
    if not selected_expense_ids:
        flash("No expenses selected. Please select at least one expense.", "warning")
        return redirect(url_for('budget.select_expenses', budget_id=budget_id))
    
    # Simple form for CSRF protection
    class ReviewForm(FlaskForm):
        submit = SubmitField('Next')
    
    form = ReviewForm()
    
    if request.method == 'POST':
        # Process personalized expense names
        expense_names = {}
        for expense_id in selected_expense_ids:
            name_key = f"expense_name_{expense_id}"
            if name_key in request.form:
                expense_names[expense_id] = request.form[name_key]
        
        # Store for use in the next step
        session['expense_names'] = expense_names
        session.modified = True
        
        # Create budget items from the selected expenses
        try:
            for expense_id in selected_expense_ids:
                # Get the expense template
                template = ExpenseTemplate.query.get(expense_id)
                if template:
                    # Use personalized name if provided, otherwise use template name
                    personalized_name = expense_names.get(expense_id, template.name)
                    
                    # Create a new budget item
                    budget_item = BudgetItem(
                        budget_id=budget_id,
                        category=template.category.name,
                        name=personalized_name,
                        minimum_payment=0.0,  # Will be filled in later
                        preferred_payment=0.0,  # Will be filled in later
                        template_id=template.id
                    )
                    db.session.add(budget_item)
            
            db.session.commit()
            flash("Expense selections saved! Now enter your income details.", "success")
            return redirect(url_for('budget.income'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while saving your expenses: {str(e)}", "danger")
            return redirect(url_for('budget.review_expenses', budget_id=budget_id))
    
    # Get the selected expense templates
    selected_expenses = ExpenseTemplate.query.filter(ExpenseTemplate.id.in_(selected_expense_ids)).all()
    
    # Organize expenses by category
    categories_data = []
    categories_dict = {}
    
    # First, create a dictionary of category IDs to categories
    for expense in selected_expenses:
        category = expense.category
        if category.id not in categories_dict:
            categories_dict[category.id] = {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'selected_expenses': []
            }
        categories_dict[category.id]['selected_expenses'].append(expense)
    
    # Convert dictionary to list, sorted by category priority
    for category_id, category_data in categories_dict.items():
        categories_data.append(category_data)
    
    # Sort categories by priority (get priority from ExpenseCategory)
    categories_data.sort(key=lambda c: ExpenseCategory.query.get(c['id']).priority)
    
    return render_template('budget/expense_review.html',
                           form=form,
                           budget_id=budget_id,
                           categories=categories_data)


@budget_bp.route('/preview', methods=['GET', 'POST'])
@login_required
def preview():
    """Display all budget details for review before final submission."""
    # Get the user's profile
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        flash("Please complete your profile before previewing your budget.", "warning")
        return redirect(url_for('profile.profile'))
    
    # Get the budget ID from session
    budget_id = session.get('budget_id')
    if not budget_id:
        flash("No active budget found. Please create a budget first.", "warning")
        return redirect(url_for('budget.budget_name'))
        
    # Get the budget
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first()
    if not budget:
        flash("Budget not found. Please create a budget first.", "warning")
        return redirect(url_for('budget.budget_name'))
    
    print(f"Loading preview for budget: {budget.id} - {budget.name}")
    
    # Get all income sources
    income_sources = GrossIncome.query.filter_by(budget_id=budget.id).all()
    primary_income = next((income for income in income_sources if income.category == "W2 Job"), None)
    other_income = [income for income in income_sources if income.category != "W2 Job"]
    
    # Get all budget items (expenses)
    budget_items = BudgetItem.query.filter_by(budget_id=budget.id).all()
    
    # Organize budget items by category for display
    expenses_by_category = {}
    for item in budget_items:
        if item.category not in expenses_by_category:
            expenses_by_category[item.category] = []
        expenses_by_category[item.category].append(item)
    
    # Create a form for CSRF protection
    from flask_wtf import FlaskForm
    form = FlaskForm()
    
    # Process form submission if this is a POST request
    if request.method == 'POST':
        if form.validate_on_submit() and 'calculate_budget' in request.form:
            # Mark the budget as ready for calculation
            budget.status = 'ready'
            db.session.commit()
            flash("Budget ready for calculation! Proceeding to final budget page.", "success")
            return redirect(url_for('budget.calculate', budget_id=budget.id))
    
    # Return the budget review template with all data
    return render_template(
        'budget/preview.html',
        budget=budget,
        primary_income=primary_income,
        other_income=other_income,
        expenses_by_category=expenses_by_category,
        profile=profile,
        form=form
    )


@budget_bp.route('/calculate/<int:budget_id>', methods=['GET'])
@login_required
def calculate(budget_id):
    """Calculate the final budget with tax estimations and display the results."""
    try:
        current_app.logger.debug(f"Starting budget calculation for budget_id: {budget_id}")

        # Get the budget
        budget = Budget.query.get_or_404(budget_id)
        current_app.logger.debug(f"Retrieved budget with {len(budget.gross_income_sources)} income sources")

        # Check authorization first
        if budget.user_id != current_user.id:
            current_app.logger.warning(f"Unauthorized access attempt for budget {budget_id} by user {current_user.id}")
            flash("You do not have permission to view this budget.", "danger")
            return redirect(url_for('main.dashboard'))

        calculator = BudgetCalculator(budget)
        current_app.logger.debug("Created BudgetCalculator instance")

        # Check if there are any income sources before calculating
        if not budget.gross_income_sources:
            current_app.logger.warning(f"No income sources found for budget {budget_id}")
            flash("Please add income sources before calculating.", "warning")
            return redirect(url_for('budget.income', budget_id=budget_id))

        current_app.logger.debug("Calculating tax withholdings")
        tax_data = calculator.calculate_tax_withholdings()
        current_app.logger.debug(f"Tax withholdings calculated: {tax_data}")

        current_app.logger.debug("Calculating final budget")
        budget_result = calculator.calculate_budget()
        current_app.logger.debug(f"Budget calculation completed: {budget_result}")

        # Transform budget_result to match template expectations
        template_budget_result = {
            'monthly_gross_income': sum(float(detail['monthly']) for detail in budget_result['gross_income']['details']),
            'monthly_net_income': budget_result['net_income']['monthly'],
            'total_expenses': sum(float(item.minimum_payment) for item in budget.budget_items),
            'remaining_money': float(budget_result['net_income']['monthly']) - sum(float(item.minimum_payment) for item in budget.budget_items),
            'expenses_by_category': {}
        }

        # Calculate expenses by category
        for item in budget.budget_items:
            if item.category not in template_budget_result['expenses_by_category']:
                template_budget_result['expenses_by_category'][item.category] = 0
            template_budget_result['expenses_by_category'][item.category] += float(item.minimum_payment)

        # Transform tax_data to match template expectations
        template_tax_data = {
            'state': budget.profile.state,
            'total_monthly_gross': sum(float(detail['monthly']) for detail in budget_result['gross_income']['details']),
            'total_monthly_federal_tax': float(tax_data['federal']) / 12,
            'total_monthly_state_tax': float(tax_data['state']) / 12,
            'total_monthly_fica_tax': float(tax_data['fica']) / 12,
            'total_monthly_net': float(budget_result['net_income']['monthly']),
            'income_details': []
        }

        # Add income source details
        for source in budget.gross_income_sources:
            # Find the corresponding detail in budget_result
            source_detail = next((d for d in budget_result['gross_income']['details'] if d['source'] == source.source), None)
            if source_detail:
                source_tax = {
                    'source': source.source,
                    'gross_income': float(source_detail['monthly']),  # Use monthly amount
                    'federal_tax': float(tax_data['federal']) * (float(source.gross_income) / float(budget_result['gross_income']['annual'])) / 12,
                    'state_tax': float(tax_data['state']) * (float(source.gross_income) / float(budget_result['gross_income']['annual'])) / 12,
                    'fica_tax': float(tax_data['fica']) * (float(source.gross_income) / float(budget_result['gross_income']['annual'])) / 12,
                }
                source_tax['net_income'] = source_tax['gross_income'] - source_tax['federal_tax'] - source_tax['state_tax'] - source_tax['fica_tax']
                template_tax_data['income_details'].append(source_tax)

        # Update budget status to 'finalized'
        budget.status = 'finalized'
        db.session.commit()
        current_app.logger.debug("Budget status updated to finalized")

        return render_template(
            'budget/results.html',
            budget=budget,
            income_sources=budget.gross_income_sources,
            budget_items=budget.budget_items,
            tax_data=template_tax_data,
            budget_result=template_budget_result
        )
    except Exception as e:
        current_app.logger.error(f"Budget calculation failed: {str(e)}", exc_info=True)
        db.session.rollback()
        flash("An error occurred while calculating your budget. Please try again later.", "danger")
        return redirect(url_for('budget.preview'))


@budget_bp.route('/download/<int:budget_id>', methods=['GET'])
@login_required
def download_budget(budget_id):
    """Generate and download an Excel file with the budget details."""
    # Get the budget
    budget = Budget.query.get_or_404(budget_id)
    
    if budget.user_id != current_user.id:
        flash("You do not have permission to download this budget.", "danger")
        return redirect(url_for('main.dashboard'))
    
    # Get the user's profile
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    
    # Get all income sources
    income_sources = GrossIncome.query.filter_by(budget_id=budget.id).all()
    
    # Get all budget items (expenses)
    budget_items = BudgetItem.query.filter_by(budget_id=budget.id).all()
    
    try:
        # Calculate tax withdrawals
        tax_data = calculate_tax_withholdings(budget, income_sources, profile)

        
        # Calculate the final budget
        calculator = BudgetCalculator(budget)
        budget_result = calculator.calculate_final_budget(budget, income_sources, budget_items, tax_data, profile)
        
        # Create Excel file
        from datetime import datetime
        budget_data = {
            'budget_name': budget.name,
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'monthly_income': budget_result['monthly_gross_income'],
            'net_income': budget_result['monthly_net_income'],
            'total_expenses': budget_result['total_expenses'],
            'remaining_money': budget_result['remaining_money'],
            'details': {
                'Income Sources': {source.source: source.gross_income for source in income_sources},
                'Expenses': {f"{item.category} - {item.name}": (item.preferred_payment if item.preferred_payment > 0 else item.minimum_payment) for item in budget_items},
                'Tax Withholdings': {
                    'Federal Tax': tax_data['total_monthly_federal_tax'],
                    'State Tax': tax_data['total_monthly_state_tax'],
                    'FICA Tax': tax_data['total_monthly_fica_tax']
                },
                'Deductions': {
                    'Retirement Contribution': profile.retirement_contribution,
                    'Benefit Deductions': profile.benefit_deductions
                }
            }
        }
        
        # Generate the Excel file
        return create_excel(budget_data)
        
    except Exception as e:
        flash(f"An error occurred while generating the Excel file: {str(e)}", "danger")
        return redirect(url_for('budget.calculate', budget_id=budget_id))


@budget_bp.errorhandler(Exception)
def handle_error(error):
    db.session.rollback()  # Roll back any failed transactions
    current_app.logger.error(f"Error: {str(error)}")
    flash("An error occurred. Please try again.", "danger")
    return redirect(url_for('main.dashboard'))


# Add a context manager for database transactions
@contextmanager
def safe_transaction():
    try:
        yield
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


# @budget_bp.route('/input', methods=['GET', 'POST'])
# def input_budget():
#     form = BudgetForm()
#     if form.validate_on_submit():
#         # Process form data and redirect to /results
#         user_data = {
#             'income': form.income.data or 0,
#             'pay_period': form.pay_period.data,
#             'rent': form.rent.data or 0,
#             'utilities': {
#                 'electricity': form.utilities.electricity.data or 0,
#                 'water': form.utilities.water.data or 0,
#                 'internet': form.utilities.internet.data or 0,
#                 'gas': form.utilities.gas.data or 0,
#             },
#             'debts': {
#                 'card1': form.debts.card1.data or 0,
#                 'card2': form.debts.card2.data or 0,
#                 'card3': form.debts.card3.data or 0,
#                 'card4': form.debts.card4.data or 0,
#                 'card5': form.debts.card5.data or 0,
#             },
#             'loans': {
#                 'vehicle1': form.loans.vehicle1.data or 0,
#                 'vehicle2': form.loans.vehicle2.data or 0,
#                 'vehicle3': form.loans.vehicle3.data or 0,
#                 'boat1': form.loans.boat1.data or 0,
#                 'boat2': form.loans.boat2.data or 0,
#                 'boat3': form.loans.boat3.data or 0,
#             },
#             'groceries': form.groceries.data or 0,
#             'transportation': form.transportation.data or 0,
#         }
#         # Save user_data to the session or pass it to the results page
#         request.form = user_data
#         return redirect(url_for('budget.results'))
#     return render_template('budget/budget_input.html', form=form)



# @budget_bp.route('/results', methods=['POST'])
# def results():
#     # Access user data from the request
#     user_data = {
#         'income': float(request.form.get('income', 0) or 0),
#         'pay_period': request.form.get('pay_period', 'monthly'),
#         'rent': float(request.form.get('rent', 0) or 0),
#         'utilities': {
#             'electricity': float(request.form.get('utilities-electricity', 0) or 0),
#             'water': float(request.form.get('utilities-water', 0) or 0),
#             'internet': float(request.form.get('utilities-internet', 0) or 0),
#             'gas': float(request.form.get('utilities-gas', 0) or 0),
#         },
#         'debts': {
#             'card1': float(request.form.get('debts-card1', 0) or 0),
#             'card2': float(request.form.get('debts-card2', 0) or 0),
#             'card3': float(request.form.get('debts-card3', 0) or 0),
#             'card4': float(request.form.get('debts-card4', 0) or 0),
#             'card5': float(request.form.get('debts-card5', 0) or 0),
#         },
#         'loans': {
#             'vehicle1': float(request.form.get('loans-vehicle1', 0) or 0),
#             'vehicle2': float(request.form.get('loans-vehicle2', 0) or 0),
#             'vehicle3': float(request.form.get('loans-vehicle3', 0) or 0),
#             'boat1': float(request.form.get('loans-boat1', 0) or 0),
#             'boat2': float(request.form.get('loans-boat2', 0) or 0),
#             'boat3': float(request.form.get('loans-boat3', 0) or 0),
#         },
#         'groceries': float(request.form.get('groceries', 0) or 0),
#         'transportation': float(request.form.get('transportation', 0) or 0),
#     }

#     # Calculate the budget
#     budget = calculate_budget(user_data)
#     income_to_debt_ratio = budget['income_to_debt_ratio']

#     if income_to_debt_ratio > 0.43:
#         flash("Your debt to income ratio is considered high risk", 'danger')
#     elif income_to_debt_ratio > 0.35:
#         flash("Your debt to income ratio is considered concerning", 'warning')
#     else:
#         flash("Your debt to income ratio is healthy, keep up the good work", 'success')

#     # Pass the cleaned data to calculate_budget
#     budget = calculate_budget(user_data)

#     # Render the results page
#     return render_template('budget/budget_results.html', budget=budget)




# @budget_bp.route('/download', methods=['POST'])
# def download():
#     from app.budget.budget_logic import create_excel  # Import here to avoid circular dependency
#     budget_data = request.form.get('budget_data')
#     response = create_excel(budget_data)
#     return response


