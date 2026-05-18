import sys
import os
from pathlib import Path

# Add backend to path so we can import routes.matching
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Mock environment variables for Pydantic validation
os.environ["SUPABASE_URL"] = "http://mock.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "mock-key"
os.environ["GEMINI_API_KEY"] = "mock-gemini"

from routes.matching import (
    calculate_compatibility_score,
    calculate_distance_score,
    get_urgency_score,
    calculate_final_score,
    generate_explanation
)

def test_blood_compatibility_o_negative():
    """O- is the universal donor, should be compatible with everyone."""
    blood_types = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
    for bt in blood_types:
        score = calculate_compatibility_score("O-", bt)
        assert score > 0, f"O- should be compatible with {bt}"
        if bt == "O-":
            assert score == 100.0
        else:
            assert score == 85.0

def test_blood_compatibility_ab_positive():
    """AB+ is the universal recipient, should accept everyone."""
    blood_types = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
    for bt in blood_types:
        score = calculate_compatibility_score(bt, "AB+")
        assert score > 0, f"AB+ should receive from {bt}"

def test_blood_incompatibility():
    """Test clear incompatible cases."""
    assert calculate_compatibility_score("A+", "O-") == 0.0
    assert calculate_compatibility_score("B+", "A+") == 0.0
    assert calculate_compatibility_score("AB+", "A+") == 0.0
    assert calculate_compatibility_score("AB+", "O+") == 0.0

def test_distance_scoring():
    """Test distance score calculations."""
    radius = 100.0
    assert calculate_distance_score(0, radius) == 100.0
    assert calculate_distance_score(50, radius) == 50.0
    assert calculate_distance_score(100, radius) == 0.0
    assert calculate_distance_score(150, radius) == 0.0

def test_urgency_mapping_case_insensitive():
    """
    Urgency scoring must be case-insensitive.
    BUG FIXED: previously 'Emergency' (capital E) and 'Urgent' gave 50 instead of 100/75.
    """
    # Standard lowercase
    assert get_urgency_score("critical") == 100.0
    assert get_urgency_score("medium") == 75.0
    assert get_urgency_score("low") == 50.0
    # Case-insensitive variants — these all must work now
    assert get_urgency_score("Emergency") == 100.0, "Capital E Emergency should give 100"
    assert get_urgency_score("CRITICAL") == 100.0, "ALL_CAPS should give 100"
    assert get_urgency_score("Urgent") == 75.0, "Capital U Urgent should give 75"
    assert get_urgency_score("Routine") == 50.0
    assert get_urgency_score("unknown_value") == 50.0

def test_final_weighted_score():
    """Test the 50/30/20 weighted logic (no-ML fallback path)."""
    assert calculate_final_score(100, 100, 100) == 100.0
    # (50 * 0.5) + (0 * 0.3) + (0 * 0.2) = 25
    assert calculate_final_score(50, 0, 0) == 25.0
    # (100 * 0.5) + (50 * 0.3) + (75 * 0.2) = 50 + 15 + 15 = 80
    assert calculate_final_score(100, 50, 75) == 80.0

def test_universal_donor_explanation():
    """
    O- donating to any other blood type gives compat_score=85.
    BUG FIXED: previously compat_score==95 check was dead code — O- was showing 
    'Compatible blood type' instead of 'Universal donor'.
    """
    explanation = generate_explanation(
        compat_score=85.0, distance_score=80.0, urgency_score=100.0,
        donor_blood="O-", recipient_blood="A+",
        distance_km=5.0, urgency_level="critical", ml_score=0.0
    )
    assert "Universal donor" in explanation, f"Expected 'Universal donor' in: {explanation}"
    assert "O-" in explanation

def test_incompatible_explanation_shows_both_blood_types():
    """Incompatible explanation must name both blood types for clinical clarity."""
    explanation = generate_explanation(
        compat_score=0.0, distance_score=0.0, urgency_score=75.0,
        donor_blood="B+", recipient_blood="A+",
        distance_km=10.0, urgency_level="medium", ml_score=0.0
    )
    assert "B+" in explanation, f"Donor blood type should appear in: {explanation}"
    assert "A+" in explanation, f"Recipient blood type should appear in: {explanation}"
