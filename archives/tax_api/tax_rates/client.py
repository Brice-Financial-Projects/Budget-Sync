"""Tax rate API client for fetching tax data from external service."""

import requests
import json
import logging
from typing import Dict, Any, Optional

from .models import (
    TaxBracket, 
    FederalTaxData, 
    StateTaxData, 
    FICATaxData,
    TaxCalculationRequest, 
    TaxCalculationResponse
)
from .config import config
from .cache import cache


# Set up logging
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Exception raised for API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class TaxRateClient:
    """Client for interacting with the tax rate API."""
    
    def __init__(self):
        """Initialize the tax rate API client."""
        self.api_key = config.api_key
        self.api_secret = config.api_secret
        self.base_url = config.base_url
        self.timeout = config.timeout_seconds
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.get(
                url, 
                headers=headers, 
                params=params, 
                timeout=self.timeout
            )
            
            # Log the request for debugging
            logger.debug(f"API request: {url} with params {params}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            return data
            
        except requests.exceptions.HTTPError as e:
            # Handle HTTP errors
            error_message = f"HTTP error occurred: {e}"
            try:
                response_data = response.json()
                logger.error(f"{error_message}. Response: {response_data}")
                raise APIError(error_message, response.status_code, response_data)
            except json.JSONDecodeError:
                logger.error(f"{error_message}. Raw response: {response.text}")
                raise APIError(error_message, response.status_code)
                
        except requests.exceptions.ConnectionError:
            error_message = "Connection error occurred. Please check your internet connection."
            logger.error(error_message)
            raise APIError(error_message)
            
        except requests.exceptions.Timeout:
            error_message = f"Request timed out after {self.timeout} seconds."
            logger.error(error_message)
            raise APIError(error_message)
            
        except requests.exceptions.RequestException as e:
            error_message = f"An error occurred during the request: {e}"
            logger.error(error_message)
            raise APIError(error_message)
            
        except json.JSONDecodeError:
            error_message = "Error decoding JSON response."
            logger.error(f"{error_message} Raw response: {response.text}")
            raise APIError(error_message)
    
    def get_federal_tax_data(self, year: int, filing_status: str = "single") -> FederalTaxData:
        """
        Get federal tax data for the specified year and filing status.
        
        Args:
            year: The tax year
            filing_status: The filing status (single, married_joint, married_separate, head_of_household)
            
        Returns:
            FederalTaxData object containing the tax brackets and standard deduction
        """
        # Check cache first
        cached_data = cache.get_federal_data(year, filing_status)
        if cached_data:
            logger.debug(f"Using cached federal tax data for {year}, {filing_status}")
            return cached_data
        
        # Make API request
        params = {
            "year": year,
            "filing_status": filing_status
        }
        
        data = self._make_request(config.federal_endpoint, params)
        
        # Parse response into FederalTaxData
        brackets = []
        for bracket_data in data.get("brackets", []):
            brackets.append(TaxBracket(
                min_income=bracket_data["min_income"],
                max_income=bracket_data.get("max_income"),
                rate=bracket_data["rate"]
            ))
        
        federal_data = FederalTaxData(
            year=year,
            brackets=brackets,
            standard_deduction=data.get("standard_deduction", 0.0)
        )
        
        # Update cache
        cache.set_federal_data(federal_data, filing_status)
        
        return federal_data
    
    def get_state_tax_data(self, state: str, year: int, filing_status: str = "single") -> StateTaxData:
        """
        Get state tax data for the specified state, year, and filing status.
        
        Args:
            state: Two-letter state code
            year: The tax year
            filing_status: The filing status
            
        Returns:
            StateTaxData object containing the state tax brackets and rates
        """
        # Check cache first
        cached_data = cache.get_state_data(year, state, filing_status)
        if cached_data:
            logger.debug(f"Using cached state tax data for {state}, {year}, {filing_status}")
            return cached_data
        
        # Make API request
        params = {
            "state": state,
            "year": year,
            "filing_status": filing_status
        }
        
        data = self._make_request(config.state_endpoint, params)
        
        # Parse response into StateTaxData
        brackets = []
        for bracket_data in data.get("brackets", []):
            brackets.append(TaxBracket(
                min_income=bracket_data["min_income"],
                max_income=bracket_data.get("max_income"),
                rate=bracket_data["rate"]
            ))
        
        state_data = StateTaxData(
            state=state,
            year=year,
            brackets=brackets,
            has_flat_tax=data.get("has_flat_tax", False),
            flat_tax_rate=data.get("flat_tax_rate", 0.0)
        )
        
        # Update cache
        cache.set_state_data(state_data, filing_status)
        
        return state_data
    
    def get_fica_data(self, year: int) -> FICATaxData:
        """
        Get FICA tax data for the specified year.
        
        Args:
            year: The tax year
            
        Returns:
            FICATaxData object containing Social Security and Medicare tax rates
        """
        # Check cache first
        cached_data = cache.get_fica_data(year)
        if cached_data:
            logger.debug(f"Using cached FICA tax data for {year}")
            return cached_data
        
        # Make API request
        params = {
            "year": year
        }
        
        data = self._make_request(config.fica_endpoint, params)
        
        # Parse response into FICATaxData
        fica_data = FICATaxData(
            year=year,
            social_security_rate=data.get("social_security_rate", 0.062),
            social_security_wage_base=data.get("social_security_wage_base", 160200.0),  # 2023 value
            medicare_rate=data.get("medicare_rate", 0.0145),
            additional_medicare_rate=data.get("additional_medicare_rate", 0.009),
            additional_medicare_threshold=data.get("additional_medicare_threshold", 200000.0)
        )
        
        # Update cache
        cache.set_fica_data(fica_data)
        
        return fica_data
    
    def calculate_taxes(self, request: TaxCalculationRequest) -> TaxCalculationResponse:
        """
        Calculate taxes based on income, state, and filing status.
        
        Args:
            request: TaxCalculationRequest with income, state, and filing parameters
            
        Returns:
            TaxCalculationResponse with calculated tax amounts and rates
        """
        # Get tax data
        federal_data = self.get_federal_tax_data(request.year, request.filing_status)
        state_data = self.get_state_tax_data(request.state, request.year, request.filing_status)
        fica_data = self.get_fica_data(request.year)
        
        # Calculate federal tax (simplified)
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
client = TaxRateClient() 