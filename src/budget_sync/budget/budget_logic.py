"""
A calculator class for handling budget-related financial calculations.

This class provides comprehensive functionality for calculating various aspects of a budget,
including gross income, deductions, taxes, and net income across different payment schedules
(annual, monthly, biweekly).

Attributes:
    budget: Budget instance containing the base financial data
    tax_client: TaxRateClient instance for tax-related calculations
    schedule_multipliers: Dictionary mapping payment schedules to their multipliers

Methods:
    calculate_gross_income: Computes total gross income from all sources
    calculate_pre_tax_deductions: Determines all pre-tax deductions
    calculate_taxable_income: Computes income subject to taxation
    calculate_tax_withholdings: Calculates tax withholdings
    calculate_net_income: Determines final net income across payment periods

Example:
    calculator = BudgetCalculator(budget_id=1)
    net_income = calculator.calculate_net_income()
    annual_net = net_income['annual']['net']
    monthly_net = net_income['monthly']['net']

Notes:
    - All monetary calculations are performed using Decimal for precision
    - Supports various payment schedules defined in PaymentSchedule enum
    - Integrates with tax calculation service for accurate withholding estimates
"""

# budget_sync/budget/budget_logic.py

import logging
from enum import Enum
from typing import TypedDict, Dict, Any
from decimal import Decimal, InvalidOperation, DivisionByZero
from dataclasses import dataclass
from src.budget_sync.models import Budget, GrossIncome, Profile
from flask import current_app

logger = logging.getLogger(__name__)

class PaymentSchedule(Enum):
    """
    Represents various payment schedules.

    This enumeration defines several payment schedule intervals, providing options for
    defining how frequently payments occur. It can be used in financial applications
    to standardize and categorize payment frequencies.
    """
    ANNUALLY = "annually"
    MONTHLY = "monthly"
    BIMONTHLY = "bimonthly"
    BIWEEKLY = "biweekly"
    WEEKLY = "weekly"


class BudgetCalculator:
    def __init__(self, budget: Budget):
        """
        Initialize the BudgetCalculator with a budget instance.

        Args:
            budget: Budget instance containing the financial data
        """
        self.budget = budget
        self.validate_budget(budget)
        self.schedule_multipliers = {
            PaymentSchedule.ANNUALLY.value: Decimal('1'),
            PaymentSchedule.MONTHLY.value: Decimal('12'),
            PaymentSchedule.BIMONTHLY.value: Decimal('24'),
            PaymentSchedule.BIWEEKLY.value: Decimal('26'),
            PaymentSchedule.WEEKLY.value: Decimal('52')
        }

    def validate_budget(self, budget: Budget) -> None:
        """
        Validate the budget instance has required attributes and relationships.
        
        Args:
            budget: Budget instance to validate
            
        Raises:
            ValueError: If budget is invalid or missing required data
        """
        if not budget:
            raise ValueError("Budget instance is required")
            
        if not budget.profile:
            raise ValueError("Budget must have an associated profile")
            
        if not budget.gross_income_sources:
            raise ValueError("Budget must have at least one income source")

    def calculate_gross_income(self) -> Dict[str, Any]:
        """Calculate total gross income from all sources."""
        try:
            total_annual = Decimal('0')
            total_monthly = Decimal('0')
            income_details = []
            
            for income in self.budget.gross_income_sources:
                # Convert amount to Decimal for precise calculations
                amount = Decimal(str(income.gross_income))
                
                # For all frequencies, amount is already annual
                annual_amount = amount
                
                # Calculate per-paycheck amount for display
                if income.frequency == 'biweekly':
                    per_paycheck = annual_amount / Decimal('26')  # 26 pay periods per year
                    monthly_amount = per_paycheck * Decimal('2')  # Standard monthly amount (2 paychecks)
                elif income.frequency == 'weekly':
                    per_paycheck = annual_amount / Decimal('52')
                    monthly_amount = per_paycheck * Decimal('4')  # Standard monthly amount (4 paychecks)
                elif income.frequency == 'monthly':
                    per_paycheck = annual_amount / Decimal('12')
                    monthly_amount = per_paycheck
                elif income.frequency == 'bimonthly':
                    per_paycheck = annual_amount / Decimal('24')
                    monthly_amount = per_paycheck * Decimal('2')
                else:  # annually
                    per_paycheck = annual_amount / Decimal('26')  # Show as biweekly equivalent
                    monthly_amount = annual_amount / Decimal('12')
                
                # Add to totals
                total_annual += annual_amount
                total_monthly += monthly_amount
                
                # Add to income details
                income_details.append({
                    'source': income.source,
                    'amount': float(amount),
                    'frequency': income.frequency,
                    'per_paycheck': float(per_paycheck),
                    'annual': float(annual_amount),
                    'monthly': float(monthly_amount)
                })
            
            return {
                'annual': float(total_annual),
                'monthly': float(total_monthly),  # Use the sum of monthly amounts
                'details': income_details
            }
        except Exception as e:
            current_app.logger.error(f"Error calculating gross income: {str(e)}")
            raise ValueError(f"Error calculating gross income: {str(e)}")

    def _convert_to_annual(self, amount: Decimal, frequency: str) -> Decimal:
        """Convert an amount to annual based on its frequency."""
        try:
            # For all frequencies, the amount is already annual
            return amount
        except Exception as e:
            current_app.logger.error(f"Error converting to annual: {str(e)}")
            raise ValueError(f"Error converting to annual: {str(e)}")

    def calculate_pre_tax_deductions(self) -> Dict[str, Decimal]:
        """Calculate pre-tax deductions including retirement, health insurance, etc."""
        try:
            # Get gross income data
            gross_income_data = self.calculate_gross_income()
            total_annual_gross = Decimal(str(gross_income_data['annual']))

            # Get profile data
            profile = Profile.query.filter_by(id=self.budget.profile_id).first()
            if not profile:
                raise ValueError("No profile found for this budget")

            # Calculate retirement contribution (as percentage of gross income)
            retirement_contribution = Decimal('0')
            if profile.retirement_contribution and profile.retirement_contribution > 0:
                # Convert percentage to decimal and calculate annual amount
                retirement_percentage = Decimal(str(profile.retirement_contribution)) / Decimal('100')
                retirement_contribution = total_annual_gross * retirement_percentage

            # Get other pre-tax deductions
            health_insurance = Decimal(str(profile.health_insurance_premium or 0)) * Decimal('12')  # Convert monthly to annual
            fsa_hsa = Decimal(str((profile.hsa_contribution or 0) + (profile.fsa_contribution or 0))) * Decimal('12')  # Convert monthly to annual
            other_benefits = Decimal(str(profile.other_pretax_benefits or 0)) * Decimal('12')  # Convert monthly to annual

            # Calculate total pre-tax deductions
            total_pre_tax = retirement_contribution + health_insurance + fsa_hsa + other_benefits

            return {
                'retirement': retirement_contribution,
                'health_insurance': health_insurance,
                'fsa_hsa': fsa_hsa,
                'other_benefits': other_benefits,
                'total': total_pre_tax
            }

        except Exception as e:
            current_app.logger.error(f"Error calculating pre-tax deductions: {str(e)}")
            raise

    def calculate_taxable_income(self) -> Dict[str, Any]:
        """Calculate taxable income after pre-tax deductions."""
        try:
            # Get gross income and pre-tax deductions
            gross_income = self.calculate_gross_income()
            pre_tax_deductions = self.calculate_pre_tax_deductions()
            
            # Convert all values to Decimal for calculation
            gross_annual = Decimal(str(gross_income['annual']))
            deductions_total = Decimal(str(pre_tax_deductions['total']))
            
            # Calculate taxable income
            taxable_income = gross_annual - deductions_total
            
            return {
                'annual': float(taxable_income),
                'monthly': float(taxable_income / Decimal('12')),
                'gross_income': gross_income,
                'pre_tax_deductions': pre_tax_deductions
            }
        except Exception as e:
            current_app.logger.error(f"Error calculating taxable income: {str(e)}")
            raise ValueError(f"Error calculating taxable income: {str(e)}")

    def calculate_tax_withholdings(self) -> Dict[str, Any]:
        """Calculate tax withholdings based on taxable income."""
        try:
            # Get taxable income
            taxable_info = self.calculate_taxable_income()
            
            # Convert values to Decimal for calculation
            gross_annual = Decimal(str(taxable_info['gross_income']['annual']))
            taxable_annual = Decimal(str(taxable_info['annual']))
            
            # Calculate FICA tax (7.65% of gross income)
            fica_tax = gross_annual * Decimal('0.0765')
            
            # Calculate federal tax
            federal_tax = self._calculate_federal_tax(taxable_annual)
            
            # Calculate state tax (simplified - 5% of taxable income)
            state_tax = taxable_annual * Decimal('0.05')
            
            # Calculate total tax
            total_tax = fica_tax + federal_tax + state_tax
            
            return {
                'fica': float(fica_tax),
                'federal': float(federal_tax),
                'state': float(state_tax),
                'total': float(total_tax),
                'monthly': {
                    'fica': float(fica_tax / Decimal('12')),
                    'federal': float(federal_tax / Decimal('12')),
                    'state': float(state_tax / Decimal('12')),
                    'total': float(total_tax / Decimal('12'))
                }
            }
        except Exception as e:
            current_app.logger.error(f"Error in calculate_tax_withholdings: {str(e)}")
            raise ValueError(f"Error calculating tax withholdings: {str(e)}")

    def _calculate_federal_tax(self, taxable_income: Decimal) -> Decimal:
        """Calculate federal tax using 2023 tax brackets"""
        brackets = [
            (Decimal('0'), Decimal('11000'), Decimal('0.10')),
            (Decimal('11000'), Decimal('44725'), Decimal('0.12')),
            (Decimal('44725'), Decimal('95375'), Decimal('0.22')),
            (Decimal('95375'), Decimal('182100'), Decimal('0.24')),
            (Decimal('182100'), Decimal('231250'), Decimal('0.32')),
            (Decimal('231250'), Decimal('578125'), Decimal('0.35')),
            (Decimal('578125'), Decimal('999999999'), Decimal('0.37'))
        ]
        
        tax = Decimal('0')
        remaining_income = taxable_income
        
        for lower, upper, rate in brackets:
            if remaining_income <= 0:
                break
                
            bracket_income = min(remaining_income, upper - lower)
            tax += bracket_income * rate
            remaining_income -= bracket_income
            
        return tax

    def _calculate_state_tax(self, taxable_income: Decimal, state: str) -> Decimal:
        """Calculate state tax based on state"""
        # Simple state tax calculation - should be expanded for accurate state-specific rules
        state_tax_rates = {
            'CA': Decimal('0.093'),  # 9.3% for California
            'NY': Decimal('0.0685'),  # 6.85% for New York
            'TX': Decimal('0'),      # No state income tax
            'FL': Decimal('0'),      # No state income tax
            # Add more states as needed
        }
        
        rate = state_tax_rates.get(state, Decimal('0.05'))  # Default 5% for other states
        return taxable_income * rate

    def _calculate_fica_tax(self, taxable_income: Decimal) -> Decimal:
        """Calculate FICA taxes (Social Security and Medicare)"""
        ss_limit = Decimal('160200')  # 2023 Social Security wage base
        ss_rate = Decimal('0.062')    # 6.2%
        medicare_rate = Decimal('0.0145')  # 1.45%
        
        # Calculate Social Security (up to limit)
        ss_taxable = min(taxable_income, ss_limit)
        ss_tax = ss_taxable * ss_rate
        
        # Calculate Medicare (no limit)
        medicare_tax = taxable_income * medicare_rate
        
        return ss_tax + medicare_tax

    def calculate_budget(self) -> Dict[str, Any]:
        """Calculate the final budget with all components."""
        try:
            # Get all components
            gross_income = self.calculate_gross_income()
            pre_tax_deductions = self.calculate_pre_tax_deductions()
            taxable_info = self.calculate_taxable_income()
            tax_data = self.calculate_tax_withholdings()
            
            # Convert all values to Decimal for calculations
            total_annual_gross = Decimal(str(gross_income['annual']))
            total_annual_deductions = Decimal(str(pre_tax_deductions['total']))
            total_annual_tax = Decimal(str(tax_data['total']))
            
            # Calculate net income
            total_annual_net = total_annual_gross - total_annual_deductions - total_annual_tax
            
            # Calculate total expenses
            total_expenses = Decimal('0')
            expenses_by_category = {}
            
            for item in self.budget.budget_items:
                amount = Decimal(str(item.minimum_payment))
                total_expenses += amount
                
                if item.category not in expenses_by_category:
                    expenses_by_category[item.category] = Decimal('0')
                expenses_by_category[item.category] += amount
            
            # Calculate remaining money
            remaining_money = total_annual_net - total_expenses
            
            # Convert all final values to float for JSON serialization
            return {
                'gross_income': {
                    'annual': float(total_annual_gross),
                    'monthly': float(total_annual_gross / Decimal('12')),
                    'details': gross_income['details']
                },
                'deductions': {
                    'annual': float(total_annual_deductions),
                    'monthly': float(total_annual_deductions / Decimal('12')),
                    'details': pre_tax_deductions
                },
                'taxable_income': {
                    'annual': float(taxable_info['annual']),
                    'monthly': float(taxable_info['monthly'])
                },
                'tax_withholdings': {
                    'annual': float(total_annual_tax),
                    'monthly': float(total_annual_tax / Decimal('12')),
                    'details': tax_data
                },
                'net_income': {
                    'annual': float(total_annual_net),
                    'monthly': float(total_annual_net / Decimal('12'))
                },
                'expenses': {
                    'total': float(total_expenses),
                    'monthly': float(total_expenses / Decimal('12')),
                    'by_category': {k: float(v) for k, v in expenses_by_category.items()}
                },
                'remaining_money': {
                    'annual': float(remaining_money),
                    'monthly': float(remaining_money / Decimal('12'))
                }
            }
        except Exception as e:
            current_app.logger.error(f"Error calculating budget: {str(e)}")
            raise ValueError(f"Error calculating budget: {str(e)}")

    @property
    def primary_income(self):
        return GrossIncome.query.filter_by(budget_id=self.id, category="W2 Job").first()

    @property
    def other_incomes(self):
        return GrossIncome.query.filter_by(budget_id=self.id).filter(GrossIncome.category != "W2 Job").all()

    @staticmethod
    def validate_budget(budget):
        if not budget.gross_income_sources:
            raise ValueError("Budget must have at least one income source")
        if not budget.profile:
            raise ValueError("Budget must have an associated profile")




def calculate_budget(budget_id: int) -> Dict:
    """
    Standalone function that uses BudgetCalculator to calculate budget details.

    Args:
        budget_id: ID of the budget to calculate

    Returns:
        Dictionary containing all budget calculations based on user input
    """
    logger.info(f"Calculating final budget for budget_id: {budget_id}")

    try:
        budget = Budget.query.get_or_404(budget_id)
        calculator = BudgetCalculator(budget)
        return calculator.calculate_budget()
    except Exception as e:
        logger.error(f"Error calculating budget: {str(e)}")
        raise ValueError(f"Error calculating budget: {str(e)}")


def create_excel(budget_data: Dict) -> bytes:
    """
    Standalone function that uses BudgetCalculator to create Excel file.

    Args:
        budget_data: Dictionary containing budget data

    Returns:
        Excel file as bytes
    """
    try:
        calculator = BudgetCalculator(budget_data['budget'])
        return calculator.create_excel()
    except Exception as e:
        raise ValueError(f"Error creating Excel file: {str(e)}")


@dataclass
class IncomeComponents:
    gross: Decimal
    deductions: Decimal
    taxable: Decimal
    withholdings: Decimal
    net: Decimal


class IncomeBreakdown(TypedDict):
    gross: Decimal
    pre_tax_deductions: Decimal
    taxable_income: Decimal
    tax_withholdings: Decimal
    net: Decimal


class NetIncomeResult(TypedDict):
    annual: IncomeBreakdown
    monthly: IncomeBreakdown
    biweekly: IncomeBreakdown


def calculate_net_income(self) -> NetIncomeResult:
    """
    Calculate net income across different payment periods.

    Returns:
        NetIncomeResult: Dictionary containing income breakdowns for annual,
                        monthly, and biweekly periods.

    Raises:
        ValueError: If any of the required income calculations return invalid data
        decimal.DivisionByZero: If there's an attempt to divide by zero
        decimal.InvalidOperation: If there's an invalid decimal operation
    """
    try:
        # Get all components with safe dictionary access
        gross_info = self.calculate_gross_income()
        deductions = self.calculate_pre_tax_deductions()
        taxable_info = self.calculate_taxable_income()
        withholdings = self.calculate_tax_withholdings()

        # Validate and extract required values
        annual_gross = Decimal(str(gross_info.get('annual', 0)))
        total_deductions = Decimal(str(deductions.get('total', 0)))
        taxable_income = Decimal(str(taxable_info.get('taxable_income', 0)))
        total_withholdings = Decimal(str(withholdings.get('total_withholdings', 0)))

        # Validate inputs
        if annual_gross < 0 or total_deductions < 0 or total_withholdings < 0:
            raise ValueError("Negative values found in income calculations")

        # Calculate net income
        net_income = annual_gross - total_deductions - total_withholdings

        # Create base annual breakdown
        annual: IncomeBreakdown = {
            'gross': annual_gross,
            'pre_tax_deductions': total_deductions,
            'taxable_income': taxable_income,
            'tax_withholdings': total_withholdings,
            'net': net_income
        }

        # Calculate periodic breakdowns
        monthly_divisor = Decimal('12')
        biweekly_divisor = Decimal('26')

        def calculate_periodic(amount: Decimal, divisor: Decimal) -> Decimal:
            return (amount / divisor).quantize(Decimal('.01'))

        monthly: IncomeBreakdown = {
            'gross': calculate_periodic(annual_gross, monthly_divisor),
            'pre_tax_deductions': calculate_periodic(total_deductions, monthly_divisor),
            'taxable_income': calculate_periodic(taxable_income, monthly_divisor),
            'tax_withholdings': calculate_periodic(total_withholdings, monthly_divisor),
            'net': calculate_periodic(net_income, monthly_divisor)
        }

        biweekly: IncomeBreakdown = {
            'gross': calculate_periodic(annual_gross, biweekly_divisor),
            'pre_tax_deductions': calculate_periodic(total_deductions, biweekly_divisor),
            'taxable_income': calculate_periodic(taxable_income, biweekly_divisor),
            'tax_withholdings': calculate_periodic(total_withholdings, biweekly_divisor),
            'net': calculate_periodic(net_income, biweekly_divisor)
        }

        return {
            'annual': annual,
            'monthly': monthly,
            'biweekly': biweekly
        }

    except KeyError as e:
        raise ValueError(f"Missing required income data: {str(e)}")
    except (InvalidOperation, DivisionByZero) as e:
        raise ValueError(f"Invalid calculation: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error calculating net income: {str(e)}")



# Explicitly export these functions
__all__ = ['calculate_budget', 'create_excel']
