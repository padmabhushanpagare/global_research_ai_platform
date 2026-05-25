from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import List, Optional

# --- Custom Pipeline Exceptions ---
class ExtractionError(Exception):
    """Raised when PDF text extraction completely fails or returns empty."""
    pass

class AnalysisError(Exception):
    """Raised when the LLM fails to return parsable data after all defensive checks."""
    pass

from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import List, Optional

# --- Custom Pipeline Exceptions ---
class ExtractionError(Exception):
    pass

class AnalysisError(Exception):
    pass

# --- Strict Data Schema ---
class FinancialMetrics(BaseModel):
    ticker: Optional[str] = Field("UNKNOWN", description="The stock ticker symbol (e.g., TSLA)")
    quarter: Optional[str] = Field("UNKNOWN", description="The fiscal quarter and year")
    
    revenue_billions: Optional[float] = Field(None, description="Total revenue reported in billions USD")
    eps: Optional[float] = Field(None, description="Earnings Per Share (EPS) reported")
    guidance: Optional[str] = Field(None, description="Future guidance provided by management")
    
    sentiment: str = Field(..., description="Sentiment of the text")
    key_takeaways: List[str] = Field(..., description="Top critical takeaways")
    
    # 🔴 NEW: Enterprise Confidence Scoring
    confidence_score: float = Field(..., description="Rate your confidence in this extraction from 0.0 to 1.0 based ONLY on the provided context.")

    # ... (Keep your existing @field_validators below) ...

    @field_validator('sentiment', mode='before')
    def enforce_valid_sentiment(cls, value):
        if not value:
            return "Neutral"
        val_lower = str(value).lower()
        if "bull" in val_lower: return "Bullish"
        if "bear" in val_lower: return "Bearish"
        return "Neutral"
    
    # 🔴 NEW: If the LLM passes 'null', this ensures our HTML reporter gets a safe fallback string
    @field_validator('ticker', 'quarter', mode='before')
    def handle_null_strings(cls, value):
        if value is None:
            return "UNKNOWN"
        return value