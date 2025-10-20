"""budget_sync/profile/routes.py"""

from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from budget_sync import db
from budget_sync.profile.forms import ProfileForm
from budget_sync.models import Profile

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_view():
    form = ProfileForm()
    
    if form.validate_on_submit():
        # Get or create profile
        user_profile = Profile.query.filter_by(user_id=current_user.id).first()
        if not user_profile:
            user_profile = Profile(user_id=current_user.id)
            db.session.add(user_profile)

        # Update personal information
        user_profile.first_name = form.first_name.data
        user_profile.last_name = form.last_name.data
        user_profile.date_of_birth = form.date_of_birth.data
        user_profile.is_blind = form.is_blind.data
        user_profile.is_student = form.is_student.data

        # Update location and filing information
        user_profile.state = form.state.data
        user_profile.filing_status = form.filing_status.data
        user_profile.num_dependents = form.num_dependents.data

        # Update employment information
        user_profile.income_type = form.income_type.data
        user_profile.pay_cycle = form.pay_cycle.data

        # Update tax withholdings
        user_profile.federal_additional_withholding = form.federal_additional_withholding.data
        user_profile.state_additional_withholding = form.state_additional_withholding.data

        # Update retirement contributions
        user_profile.retirement_contribution_type = form.retirement_contribution_type.data
        user_profile.retirement_contribution = form.retirement_contribution.data

        # Update pre-tax benefits
        user_profile.health_insurance_premium = form.health_insurance_premium.data
        user_profile.hsa_contribution = form.hsa_contribution.data
        user_profile.fsa_contribution = form.fsa_contribution.data
        user_profile.other_pretax_benefits = form.other_pretax_benefits.data

        # Calculate and update total benefit deductions
        user_profile.benefit_deductions = (
            user_profile.health_insurance_premium +
            user_profile.hsa_contribution +
            user_profile.fsa_contribution +
            user_profile.other_pretax_benefits
        )

        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile. Please try again.', 'danger')
            print(f"Error updating profile: {str(e)}")  # Log the error

    elif request.method == 'GET':
        # Pre-populate form if profile exists
        user_profile = Profile.query.filter_by(user_id=current_user.id).first()
        if user_profile:
            form.first_name.data = user_profile.first_name
            form.last_name.data = user_profile.last_name
            form.date_of_birth.data = user_profile.date_of_birth
            form.is_blind.data = user_profile.is_blind
            form.is_student.data = user_profile.is_student
            form.state.data = user_profile.state
            form.filing_status.data = user_profile.filing_status
            form.num_dependents.data = user_profile.num_dependents
            form.income_type.data = user_profile.income_type
            form.pay_cycle.data = user_profile.pay_cycle
            form.federal_additional_withholding.data = user_profile.federal_additional_withholding
            form.state_additional_withholding.data = user_profile.state_additional_withholding
            form.retirement_contribution_type.data = user_profile.retirement_contribution_type
            form.retirement_contribution.data = user_profile.retirement_contribution
            form.health_insurance_premium.data = user_profile.health_insurance_premium
            form.hsa_contribution.data = user_profile.hsa_contribution
            form.fsa_contribution.data = user_profile.fsa_contribution
            form.other_pretax_benefits.data = user_profile.other_pretax_benefits

    # Get profile for display purposes
    user_profile = Profile.query.filter_by(user_id=current_user.id).first()
    return render_template('profile/profile.html', form=form, profile=user_profile)


