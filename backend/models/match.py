from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from uuid import UUID

class MatchRequest(BaseModel):
    hospital_id: UUID
    required_organs: List[str]
    required_blood_products: List[str] = []
    patient_blood_type: Literal["A+","A-","B+","B-","AB+","AB-","O+","O-"]
    urgency_level: Literal["low", "medium", "critical"] = "medium"
    donor_type: Literal["blood", "organ"] = "organ"
    search_radius_km: float = Field(default=20.0, ge=1, le=500)
    max_results: int = Field(default=10, ge=1, le=50)

class ScoreBreakdown(BaseModel):
    compatibility_score: float
    distance_score: float
    urgency_score: float
    total_score: float

class MatchResult(BaseModel):
    donor_id: UUID
    name: str
    blood_type: str
    available_organs: List[str]
    distance_km: float
    ai_score: float
    score_breakdown: ScoreBreakdown
    ai_explanation: str
    explanation_source: str
    donating_items: List[str] = []
    travel_time_human: str = ""

class MatchResponse(BaseModel):
    matches: List[MatchResult]
    filter_stats: dict
    message: str = ""