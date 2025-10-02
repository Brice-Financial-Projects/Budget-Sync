"""Cache mechanism for tax rate API responses."""

import time
from typing import Any, Dict, Optional
from dataclasses import asdict

from .models import TaxBracket
from .config import config


class TaxRateCache:
    """Cache for tax rate API responses to reduce API calls."""
    
    def __init__(self):
        """Initialize the cache."""
        self._federal_cache: Dict[str, Dict[str, Any]] = {}
        self._state_cache: Dict[str, Dict[str, Any]] = {}
        self._fica_cache: Dict[str, Dict[str, Any]] = {}
    
    def _cache_key(self, year: int, state: Optional[str] = None, filing_status: str = "single") -> str:
        """Generate a cache key."""
        if state:
            return f"{year}_{state}_{filing_status}"
        return f"{year}_{filing_status}"
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cache entry is expired."""
        if not config.enable_cache:
            return True
        return (time.time() - timestamp) > config.cache_expiry_seconds
    
    def get_federal_data(self, year: int, filing_status: str = "single") -> Optional[FederalTaxData]:
        """Get federal tax data from cache if available and not expired."""
        key = self._cache_key(year, filing_status=filing_status)
        
        if key in self._federal_cache and not self._is_expired(self._federal_cache[key]["timestamp"]):
            data = self._federal_cache[key]["data"]
            brackets = [TaxBracket(**b) for b in data["brackets"]]
            return FederalTaxData(
                year=data["year"],
                brackets=brackets,
                standard_deduction=data["standard_deduction"]
            )
        
        return None
    
    def set_federal_data(self, federal_data: FederalTaxData, filing_status: str = "single") -> None:
        """Store federal tax data in cache."""
        key = self._cache_key(federal_data.year, filing_status=filing_status)
        
        # Convert to dictionary for storage
        data_dict = asdict(federal_data)
        
        self._federal_cache[key] = {
            "data": data_dict,
            "timestamp": time.time()
        }
    
    def get_state_data(self, year: int, state: str, filing_status: str = "single") -> Optional[StateTaxData]:
        """Get state tax data from cache if available and not expired."""
        key = self._cache_key(year, state, filing_status)
        
        if key in self._state_cache and not self._is_expired(self._state_cache[key]["timestamp"]):
            data = self._state_cache[key]["data"]
            brackets = [TaxBracket(**b) for b in data["brackets"]]
            return StateTaxData(
                state=data["state"],
                year=data["year"],
                brackets=brackets,
                has_flat_tax=data["has_flat_tax"],
                flat_tax_rate=data["flat_tax_rate"]
            )
        
        return None
    
    def set_state_data(self, state_data: StateTaxData, filing_status: str = "single") -> None:
        """Store state tax data in cache."""
        key = self._cache_key(state_data.year, state_data.state, filing_status)
        
        # Convert to dictionary for storage
        data_dict = asdict(state_data)
        
        self._state_cache[key] = {
            "data": data_dict,
            "timestamp": time.time()
        }
    
    def get_fica_data(self, year: int) -> Optional[FICATaxData]:
        """Get FICA tax data from cache if available and not expired."""
        key = self._cache_key(year)
        
        if key in self._fica_cache and not self._is_expired(self._fica_cache[key]["timestamp"]):
            data = self._fica_cache[key]["data"]
            return FICATaxData(
                year=data["year"],
                social_security_rate=data["social_security_rate"],
                social_security_wage_base=data["social_security_wage_base"],
                medicare_rate=data["medicare_rate"],
                additional_medicare_rate=data["additional_medicare_rate"],
                additional_medicare_threshold=data["additional_medicare_threshold"]
            )
        
        return None
    
    def set_fica_data(self, fica_data: FICATaxData) -> None:
        """Store FICA tax data in cache."""
        key = self._cache_key(fica_data.year)
        
        # Convert to dictionary for storage
        data_dict = asdict(fica_data)
        
        self._fica_cache[key] = {
            "data": data_dict,
            "timestamp": time.time()
        }
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._federal_cache.clear()
        self._state_cache.clear()
        self._fica_cache.clear()
    
    def clear_expired(self) -> None:
        """Clear expired cache entries."""
        for cache in [self._federal_cache, self._state_cache, self._fica_cache]:
            keys_to_remove = []
            
            for key, entry in cache.items():
                if self._is_expired(entry["timestamp"]):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del cache[key]


# Singleton instance
cache = TaxRateCache() 