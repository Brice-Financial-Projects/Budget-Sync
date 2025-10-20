"""Interface for tax rate calculations in the budget module."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.budget_sync import client as tax_client
from src.budget_sync import TaxCalculationRequest, TaxCalculationResponse
from src.budget_sync.api.errors import APIError, handle_api_error
from src.budget_sync.api.services import retry_on_failure, memoize_with_expiry
from src.budget_sync import Budget, GrossIncome, Profile

logger = logging.getLogger(__name__)


@retry_on_failure(max_retries=3)
@memoize_with_expiry(ttl_seconds=3600)  # Cache for 1 hour
def calculate_taxes_for_income(
    income: float,
    income_type: str,
    state: str,
    filing_status: str = "single",
    year: Optional[int] = None
) -> TaxCalculationResponse:
    """
    Calculate taxes for a single income source.
    
    Args:
        income: Annual gross income amount
        income_type: Type of income (W2, Self-Employed, Other)
        state: Two-letter state code
        filing_status: Tax filing status (single, married_joint, etc.)
        year: Tax year (defaults to current year)
        
    Returns:
        TaxCalculationResponse with calculated tax amounts
    """
    if year is None:
        year = datetime.now().year
    
    try:
        # Create tax calculation request
        request = TaxCalculationRequest(
            income=income,
            income_type=income_type,
            state=state,
            year=year,
            filing_status=filing_status
        )
        
        # Call tax API client
        response = tax_client.calculate_taxes(request)
        return response
        
    except APIError as e:
        logger.error(f"Error calculating taxes: {str(e)}")
        error_data = handle_api_error(e)
        # Create a default response with zeros for all tax values
        return TaxCalculationResponse(
            income=income,
            federal_tax=0.0,
            state_tax=0.0,
            fica_tax=0.0,
            net_income=income,
            effective_tax_rate=0.0,
            marginal_federal_rate=0.0,
            marginal_state_rate=0.0,
            federal_brackets=[],
            state_brackets=[]
        )


def calculate_tax_data_for_budget(
    budget: Budget,
    income_sources: List[GrossIncome],
    profile: Profile,
    filing_status: str = "single"
) -> Dict[str, Any]:
    """
    Calculate tax data for all income sources in a budget.
    
    Args:
        budget: Budget object
        income_sources: List of GrossIncome objects
        profile: User profile containing state information
        filing_status: Tax filing status
        
    Returns:
        Dictionary with detailed tax data for all income sources
    """
    # Initialize tax data structure
    tax_data = {
        'state': profile.state,
        'income_details': [],
        'total_annual_gross': 0.0,
        'total_annual_federal_tax': 0.0,
        'total_annual_state_tax': 0.0,
        'total_annual_fica_tax': 0.0,
        'total_annual_net': 0.0,
        'total_monthly_gross': 0.0,
        'total_monthly_federal_tax': 0.0,
        'total_monthly_state_tax': 0.0,
        'total_monthly_fica_tax': 0.0,
        'total_monthly_net': 0.0
    }
    
    # Process each income source
    for income_source in income_sources:
        # Convert to annual income based on frequency
        annual_income = convert_to_annual(income_source.gross_income, income_source.frequency)
        tax_data['total_annual_gross'] += annual_income
        
        # Map our tax types to the API's expected format
        api_income_type = map_income_type_to_api(income_source.tax_type)
        
        # Calculate taxes for this income source
        try:
            tax_result = calculate_taxes_for_income(
                income=annual_income,
                income_type=api_income_type,
                state=profile.state,
                filing_status=filing_status
            )
            
            # Add to totals
            tax_data['total_annual_federal_tax'] += tax_result.federal_tax
            tax_data['total_annual_state_tax'] += tax_result.state_tax
            tax_data['total_annual_fica_tax'] += tax_result.fica_tax
            tax_data['total_annual_net'] += tax_result.net_income
            
            # Add monthly values to income details
            monthly_gross = annual_income / 12
            monthly_federal = tax_result.federal_tax / 12
            monthly_state = tax_result.state_tax / 12
            monthly_fica = tax_result.fica_tax / 12
            monthly_net = tax_result.net_income / 12
            
            tax_data['income_details'].append({
                'source': income_source.source,
                'gross_income': monthly_gross,
                'federal_tax': monthly_federal,
                'state_tax': monthly_state,
                'fica_tax': monthly_fica,
                'net_income': monthly_net
            })
            
        except Exception as e:
            logger.error(f"Error calculating taxes for {income_source.source}: {str(e)}")
            # Use a simple estimation for tax if the API fails
            federal_tax = annual_income * 0.15  # Simple 15% federal estimate
            state_tax = annual_income * 0.05    # Simple 5% state estimate
            fica_tax = annual_income * 0.0765   # Simple 7.65% FICA estimate
            net_income = annual_income - federal_tax - state_tax - fica_tax
            
            tax_data['total_annual_federal_tax'] += federal_tax
            tax_data['total_annual_state_tax'] += state_tax
            tax_data['total_annual_fica_tax'] += fica_tax
            tax_data['total_annual_net'] += net_income
            
            # Add monthly values to income details
            monthly_gross = annual_income / 12
            monthly_federal = federal_tax / 12
            monthly_state = state_tax / 12
            monthly_fica = fica_tax / 12
            monthly_net = net_income / 12
            
            tax_data['income_details'].append({
                'source': income_source.source,
                'gross_income': monthly_gross,
                'federal_tax': monthly_federal,
                'state_tax': monthly_state,
                'fica_tax': monthly_fica,
                'net_income': monthly_net
            })
    
    # Calculate monthly totals
    tax_data['total_monthly_gross'] = tax_data['total_annual_gross'] / 12
    tax_data['total_monthly_federal_tax'] = tax_data['total_annual_federal_tax'] / 12
    tax_data['total_monthly_state_tax'] = tax_data['total_annual_state_tax'] / 12
    tax_data['total_monthly_fica_tax'] = tax_data['total_annual_fica_tax'] / 12
    tax_data['total_monthly_net'] = tax_data['total_annual_net'] / 12
    
    return tax_data


def convert_to_annual(amount: float, frequency: str) -> float:
    """Convert an amount from its frequency to an annual amount."""
    if frequency == 'weekly':
        return amount * 52
    elif frequency == 'biweekly':
        return amount * 26
    elif frequency == 'monthly':
        return amount * 12
    elif frequency == 'bimonthly':
        return amount * 24
    elif frequency == 'annually':
        return amount
    else:
        # Default to monthly
        return amount * 12


def map_income_type_to_api(tax_type: str) -> str:
    """Map our tax_type field to the API's expected income_type values."""
    mapping = {
        'W2': 'W2',
        'Self-Employed': 'Self-Employed',
        '1099': 'Self-Employed',
        'Rental': 'Other',
        'Investment': 'Other',
        'Other': 'Other'
    }
    return mapping.get(tax_type, 'Other') 