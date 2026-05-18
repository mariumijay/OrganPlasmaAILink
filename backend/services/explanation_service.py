import hashlib
import time
import logging
from typing import Dict, List, Tuple, Any
import asyncio
from services.ai_service import get_ai_service

# Setup logging for audit trail
logger = logging.getLogger(__name__)

class MatchJustification:
    """
    Deterministic factual verification to prevent LLM hallucinations.
    Uses clinical data to provide a baseline for the AI.
    """
    @staticmethod
    def get_clinical_facts(donor_data: Dict[str, Any], score_breakdown: Dict[str, Any]) -> List[str]:
        facts = []
        # Blood Compatibility Fact
        blood_score = score_breakdown.get('compatibility_score', 100.0) 
        if blood_score >= 100.0:
            facts.append(f"ABO matching ({donor_data.get('blood_type')}) is identical.")
        else:
            facts.append(f"ABO matching ({donor_data.get('blood_type')}) is compatible.")
            
        # Distance/Travel Fact
        distance = donor_data.get('distance_km', 0)
        facts.append(f"Donor is {distance:.1f}km away.")
        
        # Medical History Highlights (Check real donor flags)
        has_conditions = any([
            donor_data.get('diabetes'),
            donor_data.get('hypertension'),
            donor_data.get('heart_disease'),
            donor_data.get('asthma')
        ])
        
        if has_conditions:
            facts.append("Donor record indicates existing medical history (Comorbidities) which AI has factored into the match.")
        else:
            facts.append("Donor record indicates a clean medical history.")

        # ML Score Context
        ml_score = score_breakdown.get('ml_score', 0.0)
        if ml_score > 80:
            facts.append("High biological compatibility score detected.")
        elif ml_score < 40 and ml_score > 0:
            facts.append("Note: AI detected physiological factors that lower the matching priority despite proximity.")
            
        return facts

class ExplanationService:
    def __init__(self):
        self.ai_service = get_ai_service()
        self._cache: Dict[str, Dict] = {}
        self.MAX_CACHE_SIZE = 1000 
        
    @staticmethod
    def _get_cache_key(donor_id: str, patient_blood_type: str, urgency: str) -> str:
        raw = f"{donor_id}:{patient_blood_type}:{urgency}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def explain_match(
        self,
        rank: int,
        total_compatible: int,
        donor_data: Dict[str, Any],
        request_data: Dict[str, Any],
        score_breakdown: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Hybrid Deterministic/LLM Explanation.
        """
        # 1. Deterministic Baseline
        facts = MatchJustification.get_clinical_facts(donor_data, score_breakdown)
        deterministic_intro = " ".join(facts)
        
        # 2. Check Cache
        cache_key = self._get_cache_key(
            donor_data.get('id', 'unknown'), 
            request_data.get('patient_blood_type', 'O+'), 
            request_data.get('urgency_level', 'medium')
        )
        
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached['timestamp'] < 900: 
                return f"{deterministic_intro} {cached['explanation']}", "hybrid-cached"

        # 3. LLM Synthesis
        system_prompt = (
            "You are an OPAL-AI Clinical Auditor. "
            "Synthesize a 2-sentence explanation for a donor match. "
            "Explain WHY the rank was given based on: Distance, Blood Compatibility, and the XGBoost AI Score. "
            "If the AI Score is low (< 40), mention it suggests biological risk. "
            "Keep it professional and scientific. NO EMOJIS."
        )

        model = self.ai_service.get_model(system_instruction=system_prompt)
        if not model:
            return f"{deterministic_intro} Ranking prioritized by clinical utility and proximity score.", "hybrid-no-ai"

        user_prompt = f"""
        Donor: {donor_data.get('full_name', 'Verified Donor')}
        Stats: Age {donor_data.get('age')}, Blood {donor_data.get('blood_type')}, Distance {donor_data.get('distance_km', 0):.1f}km.
        ML Suitability Score: {score_breakdown.get('ml_score', 0.0):.1f}/100.
        Patient Urgency: {request_data.get('urgency_level')}.
        Health Flags: Diabetes={donor_data.get('diabetes')}, Hypertension={donor_data.get('hypertension')}.
        """

        try:
            generation_config = {"temperature": 0.2, "max_output_tokens": 150}
            response = await asyncio.wait_for(
                asyncio.to_thread(model.generate_content, user_prompt, generation_config=generation_config),
                timeout=5.0
            )

            if not response.candidates or response.candidates[0].finish_reason != 1:
                return deterministic_intro, "hybrid-safety-fallback"

            llm_synthesis = response.text.strip()
            self._cache[cache_key] = {"explanation": llm_synthesis, "timestamp": time.time()}
            return f"{deterministic_intro} {llm_synthesis}", "hybrid-gemini"
            
        except Exception as e:
            logger.error(f"Explanation Error: {e}")
            return f"{deterministic_intro} Clinical priority determined by cross-matching and distance metrics.", "hybrid-fallback"


_explanation_service = None

def get_explanation_service():
    global _explanation_service
    if _explanation_service is None:
        _explanation_service = ExplanationService()
    return _explanation_service
