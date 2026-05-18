from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Any, Dict
import asyncio
import time
import re
from services.supabase_client import get_supabase
from services.ai_service import get_ai_service
from core.config import settings

router = APIRouter(prefix="/api/chat", tags=["AI Chatbot"])

# Initialize AI Service
ai_service = get_ai_service()

# --- Schemas ---

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    role: Literal["donor", "hospital", "admin"]
    user_id: str
    page_context: str
    conversation_history: List[dict] = []

class ChatResponse(BaseModel):
    reply: str
    source: Literal["gemini", "neural_engine", "safety_intercept"]
    advisory: Optional[str] = None
    action_button: Optional[Dict[str, str]] = None
    suggestions: List[str] = []

# In-memory caches
context_cache: Dict[str, Any] = {}
CACHE_TTL = 300

response_cache: Dict[str, Any] = {}
RESPONSE_CACHE_TTL = 600 # 10 minutes

# --- DB Context Fetchers ---

def fetch_match_context(hospital_user_id: str) -> str:
    """Fetch a summary of the hospital's most recent AI matching results for chatbot context."""
    try:
        supabase = get_supabase()
        # Find hospital record
        hosp_res = supabase.table("hospitals").select("id, name").eq("user_id", hospital_user_id).limit(1).execute()
        if not hosp_res.data:
            return ""
        
        hosp_id = hosp_res.data[0]['id']
        hosp_name = hosp_res.data[0].get('name', 'Your hospital')

        # Fetch the 3 most recent requests for this hospital
        req_res = supabase.table("organ_requests") \
            .select("patient_blood_type, urgency_level, required_organs, status, created_at") \
            .eq("hospital_id", hosp_id) \
            .order("created_at", desc=True) \
            .limit(3) \
            .execute()
        
        if not req_res.data:
            return f"{hosp_name} has no recent match requests."
        
        lines = [f"Recent match requests for {hosp_name}:"]
        for r in req_res.data:
            organs = ", ".join(r.get("required_organs") or ["N/A"])
            lines.append(
                f"  • Blood: {r.get('patient_blood_type','?')} | Organ: {organs} "
                f"| Urgency: {r.get('urgency_level','?')} | Status: {r.get('status','?')}"
            )
        return "\n".join(lines)
    except Exception as e:
        print(f"[CHAT-MATCH-CONTEXT-ERROR] {str(e)}")
        return ""

def fetch_db_context(role: str, user_id: str) -> str:
    cache_key = f"{role}:{user_id}"
    if cache_key in context_cache:
        cached = context_cache[cache_key]
        if time.time() - cached['timestamp'] < CACHE_TTL:
            return cached['context']

    db_context = "System running 🟢"
    
    try:
        if role == "admin":
            supabase = get_supabase()
            donors = supabase.table("donors").select("id", count="exact").eq("status", "active").execute()
            hospitals = supabase.table("hospitals").select("id", count="exact").execute()
            db_context = f"Global Stats: {donors.count or 0} donors active. {hospitals.count or 0} Hospitals verified."
        elif role == "hospital":
            match_ctx = fetch_match_context(user_id)
            db_context = f"OPAL-AI is online and ready 🏥\n{match_ctx}" if match_ctx else "OPAL-AI is online and ready 🏥"
        else:
            db_context = "OPAL-AI is online and ready 🏥"
    except Exception as e:
        print(f"[CHAT-CONTEXT-ERROR] Database fetch failed: {str(e)}")
        db_context = "Data protocols standing by 🛡️"

    context_cache[cache_key] = {"context": db_context, "timestamp": time.time()}
    return db_context

# --- Neural Knowledge Base (SOCIAL + CLINICAL) ---

INTENT_MAP = [
    # 1. SOCIAL/CONVERSATIONAL
    {
        "triggers": ["nice", "good", "great", "cool", "wow", "amazing", "shukriya", "thanks", "thank you"],
        "reply": "😊 I'm glad I could help! Is there anything else about the matching logic or donor registration you'd like to know?",
        "suggestions": ["How to register?", "View matches", "Safety info"]
    },
    {
        "triggers": ["ok", "okay", "understand", "got it", "fine", "theek", "acha", "sahi"],
        "reply": "Perfect! 👍 Just let me know if you need any more clinical details or help with the dashboard.",
        "suggestions": ["Tell me about OPAL", "Register as donor"]
    },
    
    # 2. SPECIFIC CLINICAL FLOWS
    {
        "triggers": ["become a donor", "donor register", "donor signup", "join as donor", "register as donor"],
        "reply": "📝 Becoming a donor is easy! Just click the 'Register as Donor' button. You'll fill out a quick form with your blood type and details. [ACTION:donor_register]",
        "suggestions": ["What organs can I donate?", "Is it safe?"]
    },
    {
        "triggers": ["hospital register", "hospital signup", "register as hospital", "join as hospital", "coordinator"],
        "reply": "🏥 For medical centers, please use our Hospital Registration portal. You will need to provide your facility details for verification. [ACTION:hospital_register]",
        "suggestions": ["How matching works", "Submit a request"]
    },
    {
        "triggers": ["register", "signup", "join"],
        "reply": "📝 Would you like to register as a **Donor** or a **Hospital**? Donors can save lives by providing organs/blood, while Hospitals can use our AI to find matches.",
        "suggestions": ["Register as donor", "Register as hospital"]
    },
    {
        "triggers": ["organ", "can i donate", "available organs"],
        "reply": "🫀 You can donate various organs such as Kidneys, Liver (parts), and Lungs. You can also register for blood donation. Each donor is matched based on biological compatibility.",
        "suggestions": ["Blood donation info", "How matching works"]
    },
    {
        "triggers": ["request", "submit", "create", "new match", "find donor", "view my matches", "view matches", "my matches"],
        "reply": "🏥 To submit a new request or view your AI matches, go to your Hospital Dashboard and click 'Launch AI Matchmaker'. [ACTION:hospital_dashboard]",
        "suggestions": ["Matching logic", "Contact support"]
    },
    {
        "triggers": ["matching", "logic", "how it works", "calculate", "matches", "score", "ai", "meaning", "percentage"],
        "reply": "🧬 We use smart logic and XGBoost AI to match blood types and OSRM distance. A score > 80% indicates high clinical compatibility. We even check traffic to ensure the organ arrives safely!",
        "suggestions": ["Submit a request", "Safety info"]
    },
    {
        "triggers": ["activity", "status", "unusual", "security", "safe"],
        "reply": "🛡️ The system is 100% secure. We use end-to-end encryption for donor data and monitor clinical transport routes constantly to ensure data integrity.",
        "suggestions": ["What is OPAL AI?", "Register donor"]
    },
    {
        "triggers": ["blood", "type", "compatibility", "group"],
        "reply": "🩸 We match donors based on blood groups (A+, B-, O+ etc.) to ensure safety. O- is our universal donor node. The system automatically filters incompatible groups.",
        "suggestions": ["What organs can I donate?", "How to register?"]
    },
    {
        "triggers": ["cit", "time", "window", "viability"],
        "reply": "⏳ 'Time is Life'. Cold Ischemia Time (CIT) is critical. We ensure organs travel within safe windows to keep them healthy for the recipient.",
        "suggestions": ["How matching works", "View dashboard"]
    },
    {
        "triggers": ["what is", "opal ai", "about", "tell me", "how does it work", "explain", "everything"],
        "reply": "🏥 OPAL-AI is an intelligent platform for organ and blood procurement. We use XGBoost AI to match donors with recipients based on blood type, distance (OSRM), and urgency. We synchronize life-saving logistics across Pakistan to ensure 'Time is Life'!",
        "suggestions": ["How to register?", "How matching works", "Safety info"]
    },
    {
        "triggers": ["availability", "update", "change status", "toggle"],
        "reply": "🔄 You can update your availability directly from your Donor Dashboard. Just use the toggle switch to change your status between 'Available' and 'Unavailable'. [ACTION:donor_dashboard]",
        "suggestions": ["How to register?", "Safety info"]
    },
    {
        "triggers": ["support", "contact", "help", "email", "phone", "talk to human"],
        "reply": "📞 We're here to help! You can reach the OPAL-AI support team at support@opal-ai.com or call our 24/7 clinical helpline at +92 300 1234567. We usually respond within 1 hour.",
        "suggestions": ["Tell me about OPAL", "How matching works"]
    }
]

# --- Logic ---

async def call_ai_engine(message: str, role: str, db_context: str, history: List[dict]) -> tuple[str, str, List[str]]:
    msg_low = message.lower().strip()

    # 1. CACHE CHECK
    cache_key = f"{role}:{msg_low}"
    if cache_key in response_cache:
        cached = response_cache[cache_key]
        if time.time() - cached['timestamp'] < RESPONSE_CACHE_TTL:
            print(f"[CHAT-CACHE] Serving cached response for: {msg_low}")
            return cached['reply'], cached['source'], cached['suggestions']

    # 2. NEURAL INTENT MAP (Priority — Saves Quota)
    if any(greet in msg_low for greet in ["hello", "hi", "salam", "السلام", "helo"]):
        return "👋 Hi! I'm your OPAL Assistant. Ask me anything about donor registration, matching, or your dashboard!", "neural_engine", ["How to register?", "How matching works"]

    for intent in INTENT_MAP:
        if any(trigger in msg_low for trigger in intent["triggers"]):
            return intent["reply"], "neural_engine", intent.get("suggestions", [])

    # 3. VAGUE/SHORT MESSAGES (Locally handled)
    vague_words = ["what", "huh", "?", "acha", "hmm", "k", "acha theek", "lol", "ok"]
    if msg_low in vague_words or len(msg_low) <= 4:
        return "😊 I'm here to help! You can ask me about:\n• Donor registration\n• Blood type matching\n• Dashboard features", "neural_engine", ["How to register?", "Tell me about OPAL"]

    # 4. COMPLEX QUERIES — CALL GEMINI
    try:
        model = ai_service.get_model(model_name="gemini-1.5-flash") # Stable for free tier
        if model:
            system_prompt = f"""You are OPAL Assistant, an expert AI clinical coordinator for OPAL-AI — Pakistan's organ and blood donor matching platform.

PLATFORM INFO:
- Matches blood/organ donors with hospitals using XGBoost AI, blood type compatibility matrix, and OSRM road-distance routing
- Operates across Pakistan (Lahore, Karachi, Islamabad, Rawalpindi, etc.)
- Current user role: {role}
- Live system data: {db_context}

CLINICAL EXPLAINABILITY RULES (CRITICAL):
When explaining AI match scores or results, you MUST provide specific clinical reasons, for example:
- "High score due to universal donor status (O-) and close proximity (3.2 km)"
- "Score penalized because donor has Hypertension — reduces organ viability"
- "XGBoost model flagged this donor as high-risk due to Diabetes — consider alternative"
- "Perfect blood type match (A+ → A+) with low urgency gives a solid 87% score"

NEVER say just "good match" without citing the blood type, distance, or a medical condition.

RESPONSE RULES:
1. Answer in same language user writes in (Urdu, English, or Roman Urdu)
2. Keep answers short and clear — no long essays
3. For medical advice beyond matching, say "doctor se consult karein"
4. Stay focused on OPAL-AI only
5. At the VERY END of your message, provide 2-3 short "Suggested Questions" in brackets like this: [SUGGESTIONS: question 1 | question 2 | question 3]

ACTION TAG RULE:
End your reply with the correct tag:
- Donor registration/signup → [ACTION:donor_register]
- Hospital registration → [ACTION:hospital_register]  
- Donor dashboard/status/availability → [ACTION:donor_dashboard]
- Hospital matches/results → [ACTION:hospital_dashboard]

Conversation history: {history[-4:] if history else 'None'}
User message: {message}"""

            response = await asyncio.wait_for(
                asyncio.to_thread(model.generate_content, system_prompt),
                timeout=10.0
            )
            if response.text and len(response.text.strip()) > 0:
                text = response.text
                suggestions = []
                sug_match = re.search(r'\[SUGGESTIONS:(.*?)\]', text)
                if sug_match:
                    suggestions = [s.strip() for s in sug_match.group(1).split('|')]
                    text = re.sub(r'\[SUGGESTIONS:.*?\]', '', text).strip()
                
                # Cache Gemini Response
                response_cache[cache_key] = {
                    "reply": text,
                    "source": "gemini",
                    "suggestions": suggestions,
                    "timestamp": time.time()
                }
                return text, "gemini", suggestions
    except Exception as e:
        print(f"[AI-ENGINE-ERROR] Gemini failed: {str(e)}")

    # LAST RESORT
    return "🤔 I'm not quite sure about that. Could you rephrase? You can ask about donor signup, matching, or your dashboard.", "neural_engine", ["How to register?", "Safety info"]

@router.post("/ask", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        db_context = fetch_db_context(request.role, request.user_id)
        reply, source, suggestions = await call_ai_engine(request.message, request.role, db_context, request.conversation_history)

        # action tag detect
        action_map = {
            "donor_register": {"label": "📝 Register as Donor", "url": "/auth/donor/signup"},
            "hospital_register": {"label": "🏥 Register Hospital", "url": "/auth/hospital/signup"},
            "donor_dashboard": {"label": "📊 My Dashboard", "url": "/dashboard/donor"},
            "hospital_dashboard": {"label": "🔍 View Matches", "url": "/dashboard/hospital/matching"},
            "admin_dashboard": {"label": "⚙️ Admin Panel", "url": "/dashboard/admin"},
        }

        action_button = None
        action_match = re.search(r'\[ACTION:(\w+)\]', reply)
        if action_match:
            action_key = action_match.group(1)
            
            # ROLE-BASED ACTION SECURITY
            allowed = False
            if request.role == "admin":
                allowed = True
            elif request.role == "hospital" and action_key in ["hospital_dashboard", "donor_register", "hospital_register"]:
                allowed = True
            elif request.role == "donor" and action_key in ["donor_dashboard", "donor_register", "hospital_register"]:
                allowed = True
            
            if allowed:
                action_button = action_map.get(action_key)
            
            reply = re.sub(r'\[ACTION:\w+\]', '', reply).strip()
        
        medical_topics = ["organ", "blood", "donor", "match", "compatible"]
        advisory = "⚠️ General medical info only." if any(t in request.message.lower() for t in medical_topics) else None
        
        return ChatResponse(
            reply=reply, 
            source=source, 
            advisory=advisory, 
            action_button=action_button,
            suggestions=suggestions
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"CRITICAL ERROR IN CHAT ENDPOINT:\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Python Error: {str(e)}")
