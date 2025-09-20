"""Models for tax rate calculations and API requests/responses."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.budget_sync import db


@dataclass
class TaxBracket:
    """Represents a tax bracket with rate and income thresholds."""
    rate: float
    min_income: float
    max_income: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert tax bracket to dictionary."""
        return {
            'rate': self.rate,
            'min_income': self.min_income,
            'max_income': self.max_income if self.max_income is not None else 'No Limit'
        }


@dataclass
class FederalTaxData:
    """Federal tax information for a specific year."""
    year: int
    brackets: List[TaxBracket]
    standard_deduction: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert federal tax data to dictionary."""
        return {
            'year': self.year,
            'brackets': [bracket.to_dict() for bracket in self.brackets],
            'standard_deduction': self.standard_deduction
        }


@dataclass
class StateTaxData:
    """State tax information for a specific state and year."""
    state: str
    year: int
    brackets: List[TaxBracket]
    has_state_tax: bool = True
    standard_deduction: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert state tax data to dictionary."""
        return {
            'state': self.state,
            'year': self.year,
            'has_state_tax': self.has_state_tax,
            'brackets': [bracket.to_dict() for bracket in self.brackets],
            'standard_deduction': self.standard_deduction
        }


@dataclass
class FICATaxData:
    """FICA tax rates and wage bases for a specific year."""
    year: int
    social_security_rate: float
    medicare_rate: float
    additional_medicare_rate: float
    social_security_wage_base: float
    additional_medicare_threshold: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert FICA tax data to dictionary."""
        return {
            'year': self.year,
            'social_security': {
                'rate': self.social_security_rate,
                'wage_base': self.social_security_wage_base
            },
            'medicare': {
                'base_rate': self.medicare_rate,
                'additional_rate': self.additional_medicare_rate,
                'additional_threshold': self.additional_medicare_threshold
            }
        }


@dataclass
class TaxCalculationRequest:
    """Request model for tax calculations."""
    income: float
    year: int = field(default_factory=lambda: datetime.now().year)
    state: str = ''
    filing_status: str = 'single'
    pay_frequency: str = 'annual'
    additional_withholding: float = 0.0
    pretax_deductions: float = 0.0

    VALID_FILING_STATUSES = {
        'single', 'married_joint', 'married_separate',
        'head_household', 'qualifying_widow'
    }

    VALID_PAY_FREQUENCIES = {
        'weekly', 'biweekly', 'semimonthly', 'monthly', 'annual'
    }

    def is_valid(self) -> bool:
        """Validate the tax calculation request."""
        try:
            if not isinstance(self.income, (int, float)) or self.income < 0:
                return False

            if not isinstance(self.year, int) or self.year < 1900:
                return False

            if self.state and len(self.state) != 2:
                return False

            if self.filing_status not in self.VALID_FILING_STATUSES:
                return False

            if self.pay_frequency not in self.VALID_PAY_FREQUENCIES:
                return False

            if not isinstance(self.additional_withholding, (int, float)) or self.additional_withholding < 0:
                return False

            if not isinstance(self.pretax_deductions, (int, float)) or self.pretax_deductions < 0:
                return False

            if self.pretax_deductions > self.income:
                return False

            return True
        except Exception:
            return False

    def validation_errors(self) -> List[str]:
        """Get list of validation errors."""
        errors = []

        if not isinstance(self.income, (int, float)) or self.income < 0:
            errors.append("Income must be a positive number")

        if not isinstance(self.year, int) or self.year < 1900:
            errors.append("Invalid year")

        if self.state and len(self.state) != 2:
            errors.append("State must be a two-letter code")

        if self.filing_status not in self.VALID_FILING_STATUSES:
            errors.append(f"Filing status must be one of: {', '.join(self.VALID_FILING_STATUSES)}")

        if self.pay_frequency not in self.VALID_PAY_FREQUENCIES:
            errors.append(f"Pay frequency must be one of: {', '.join(self.VALID_PAY_FREQUENCIES)}")

        if not isinstance(self.additional_withholding, (int, float)) or self.additional_withholding < 0:
            errors.append("Additional withholding must be a non-negative number")

        if not isinstance(self.pretax_deductions, (int, float)) or self.pretax_deductions < 0:
            errors.append("Pre-tax deductions must be a non-negative number")

        if self.pretax_deductions > self.income:
            errors.append("Pre-tax deductions cannot exceed income")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary."""
        return {
            'year': self.year,
            'income': self.income,
            'state': self.state.upper() if self.state else '',
            'filing_status': self.filing_status,
            'pay_frequency': self.pay_frequency,
            'additional_withholding': self.additional_withholding,
            'pretax_deductions': self.pretax_deductions
        }


@dataclass
class TaxCalculationResponse:
    """Response model for tax calculations."""
    federal_tax: float
    state_tax: float
    social_security_tax: float
    medicare_tax: float
    total_tax: float
    effective_tax_rate: float
    tax_brackets_used: Optional[List[Dict[str, Any]]] = None
    deductions_applied: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        response = {
            'federal_tax': round(self.federal_tax, 2),
            'state_tax': round(self.state_tax, 2),
            'fica_tax': {
                'social_security': round(self.social_security_tax, 2),
                'medicare': round(self.medicare_tax, 2)
            },
            'total_tax': round(self.total_tax, 2),
            'effective_tax_rate': round(self.effective_tax_rate, 2)
        }

        if self.tax_brackets_used:
            response['tax_brackets_used'] = self.tax_brackets_used

        if self.deductions_applied:
            response['deductions_applied'] = {
                k: round(v, 2) for k, v in self.deductions_applied.items()
            }

        return response


@dataclass
class StateInfo(db.Model):
    __tablename__ = 'state_info'

    # Fields to expose in JSON serialization
    id: int
    state_code: str
    state_name: str
    has_state_tax: bool

    # Column definitions
    id = db.Column(db.Integer, primary_key=True)
    state_code = db.Column(db.String(2), unique=True, nullable=False)
    state_name = db.Column(db.String(100), nullable=False)
    has_state_tax = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<StateInfo {self.state_code}>"


@dataclass
class StateTaxBracket(db.Model):
    __tablename__ = 'state_tax_brackets'

    # Fields to expose in JSON serialization
    id: int
    state: str
    tax_year: int
    bracket_floor: float
    rate: float

    # Column definitions
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(2), db.ForeignKey('state_info.state_code'), nullable=False)
    tax_year = db.Column(db.Integer, nullable=False)
    bracket_floor = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    state_info = db.relationship('StateInfo', backref=db.backref('tax_brackets', lazy=True))

    def __repr__(self):
        return f"<StateTaxBracket {self.state} {self.tax_year} - {self.rate}>"
