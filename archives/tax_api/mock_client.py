"""Mock client for the tax rate API that uses sample data."""

# budget_sync/api/tax_rates/mock_client.py

import logging
from typing import Dict, Any, List

from .models import (
    TaxBracket, 
    FederalTaxData, 
    StateTaxData, 
    FICATaxData,
    TaxCalculationRequest, 
    TaxCalculationResponse
)
from .data.federal_tax_data import get_federal_tax_brackets
from .data.state_tax_data import get_state_tax_brackets

from .data.fica_tax_data import get_fica_tax_brackets

logger = logging.getLogger(__name__)


class MockTaxRateClient:
    """Mock client for the tax rate API that uses sample data."""
    
    def __init__(self):
        """Initialize the mock tax rate client."""
        logger.info("Initializing mock tax rate client")
    
    def get_federal_tax_data(self, year: int, filing_status: str = "single") -> FederalTaxData:
        """
        Get federal tax data using sample data.
        
        Args:
            year: The tax year
            filing_status: The filing status (single, married_joint, etc.)
            
        Returns:
            FederalTaxData object
        """
        logger.debug(f"Getting mock federal tax data for {year}, {filing_status}")
        data = self.get_federal_tax_data(year, filing_status)
        
        # Convert bracket dictionaries to TaxBracket objects
        brackets = []
        for bracket_dict in data["brackets"]:
            brackets.append(TaxBracket(
                min_income=bracket_dict["min_income"],
                max_income=bracket_dict["max_income"],
                rate=bracket_dict["rate"]
            ))
        
        return FederalTaxData(
            year=data["year"],
            brackets=brackets,
            standard_deduction=data["standard_deduction"]
        )
    
    def get_state_tax_data(self, state: str, year: int, filing_status: str = "single") -> StateTaxData:
        """
        Get state tax data using sample data.
        
        Args:
            state: Two-letter state code
            year: The tax year
            filing_status: The filing status
            
        Returns:
            StateTaxData object
        """
        logger.debug(f"Getting mock state tax data for {state}, {year}, {filing_status}")
        data = self.get_state_tax_data(state, year, filing_status)
        
        # Convert bracket dictionaries to TaxBracket objects
        brackets = []
        for bracket_dict in data["brackets"]:
            brackets.append(TaxBracket(
                min_income=bracket_dict["min_income"],
                max_income=bracket_dict["max_income"],
                rate=bracket_dict["rate"]
            ))
        
        return StateTaxData(
            state=data["state"],
            year=data["year"],
            brackets=brackets,
            has_flat_tax=data["has_flat_tax"],
            flat_tax_rate=data["flat_tax_rate"]
        )
    
    def get_fica_data(self, year: int) -> FICATaxData:
        """
        Get FICA tax data using sample data.
        
        Args:
            year: The tax year
            
        Returns:
            FICATaxData object
        """
        logger.debug(f"Getting mock FICA tax data for {year}")
        data = self.get_fica_data(year)
        
        return FICATaxData(
            year=data["year"],
            social_security_rate=data["social_security_rate"],
            social_security_wage_base=data["social_security_wage_base"],
            medicare_rate=data["medicare_rate"],
            additional_medicare_rate=data["additional_medicare_rate"],
            additional_medicare_threshold=data["additional_medicare_threshold"]
        )
    
    def calculate_taxes(self, request: TaxCalculationRequest) -> TaxCalculationResponse:
        """
        Calculate taxes using sample data.
        
        Args:
            request: TaxCalculationRequest with income, state, and filing parameters
            
        Returns:
            TaxCalculationResponse with calculated tax amounts and rates
        """
        logger.debug(f"Calculating mock taxes for {request.income} in state {request.state}")
        
        # Get tax data from the mock data sources
        federal_data = self.get_federal_tax_data(request.year, request.filing_status)
        state_data = self.get_state_tax_data(request.state, request.year, request.filing_status)
        fica_data = self.get_fica_data(request.year)
        
        # Calculate federal tax
        federal_tax = self._calculate_federal_tax(request.income, federal_data)
        
        # Calculate state tax
        state_tax = self._calculate_state_tax(request.income, state_data)
        
        # Calculate FICA tax based on income type
        fica_tax = self._calculate_fica_tax(request.income, fica_data, request.income_type)
        
        # Calculate net income
        total_tax = federal_tax + state_tax + fica_tax
        net_income = request.income - total_tax
        
        # Calculate effective tax rate
        effective_tax_rate = total_tax / request.income if request.income > 0 else 0
        
        # Get marginal rates
        marginal_federal_rate = federal_data.get_rate_for_income(request.income)
        marginal_state_rate = state_data.get_rate_for_income(request.income)
        
        # Create response
        response = TaxCalculationResponse(
            income=request.income,
            federal_tax=federal_tax,
            state_tax=state_tax,
            fica_tax=fica_tax,
            net_income=net_income,
            effective_tax_rate=effective_tax_rate,
            marginal_federal_rate=marginal_federal_rate,
            marginal_state_rate=marginal_state_rate,
            federal_brackets=federal_data.brackets,
            state_brackets=state_data.brackets
        )
        
        return response
    
    def _calculate_federal_tax(self, income: float, federal_data: FederalTaxData) -> float:
        """Calculate federal tax using progressive tax brackets."""
        # Apply standard deduction
        taxable_income = max(0, income - federal_data.standard_deduction)
        
        # Calculate tax using brackets
        tax = 0.0
        remaining_income = taxable_income
        
        # Sort brackets by min_income
        sorted_brackets = sorted(federal_data.brackets, key=lambda b: b.min_income)
        
        for i, bracket in enumerate(sorted_brackets):
            if remaining_income <= 0:
                break
                
            if i < len(sorted_brackets) - 1:
                # Not the highest bracket
                next_bracket = sorted_brackets[i + 1]
                bracket_income = min(remaining_income, next_bracket.min_income - bracket.min_income)
            else:
                # Highest bracket
                bracket_income = remaining_income
            
            tax += bracket_income * bracket.rate
            remaining_income -= bracket_income
        
        return tax
    
    def _calculate_state_tax(self, income: float, state_data: StateTaxData) -> float:
        """Calculate state tax based on brackets or flat rate."""
        if state_data.has_flat_tax:
            return income * state_data.flat_tax_rate
        
        # Calculate using progressive brackets
        tax = 0.0
        remaining_income = income
        
        # Sort brackets by min_income
        sorted_brackets = sorted(state_data.brackets, key=lambda b: b.min_income)
        
        for i, bracket in enumerate(sorted_brackets):
            if remaining_income <= 0:
                break
                
            if i < len(sorted_brackets) - 1:
                # Not the highest bracket
                next_bracket = sorted_brackets[i + 1]
                bracket_income = min(remaining_income, next_bracket.min_income - bracket.min_income)
            else:
                # Highest bracket
                bracket_income = remaining_income
            
            tax += bracket_income * bracket.rate
            remaining_income -= bracket_income
        
        return tax
    
    def _calculate_fica_tax(self, income: float, fica_data: FICATaxData, income_type: str) -> float:
        """Calculate FICA tax based on income type."""
        # Social Security tax (up to wage base)
        ss_tax = min(income, fica_data.social_security_wage_base) * fica_data.social_security_rate
        
        # Medicare tax (no income limit)
        medicare_tax = income * fica_data.medicare_rate
        
        # Additional Medicare tax for high incomes
        if income > fica_data.additional_medicare_threshold:
            medicare_tax += (income - fica_data.additional_medicare_threshold) * fica_data.additional_medicare_rate
        
        # Self-employed individuals pay both employee and employer portions
        if income_type == "Self-Employed":
            ss_tax *= 2
            medicare_tax *= 2
        
        # Other income types (like rentals, investments) might not pay FICA
        if income_type not in ["W2", "Self-Employed"]:
            return 0.0
        
        return ss_tax + medicare_tax


# Create a singleton instance
client = MockTaxRateClient() 