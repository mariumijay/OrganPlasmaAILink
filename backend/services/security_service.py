import re
from typing import Any, Dict, List

class SecurityService:
    """
    Security Layer implementation matching the Architecture Diagram.
    Handles PII Masking and Prompt Injection detection.
    """
    
    @staticmethod
    def mask_pii(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Masks Personally Identifiable Information (PII) before returning to the frontend.
        Matches 'PII Masker' component in the diagram.
        """
        masked = data.copy()
        
        # Mask Phone Numbers (e.g. +92 300 1234567 -> +92 300 *******)
        if "phone" in masked and masked["phone"]:
            phone = str(masked["phone"])
            if len(phone) > 7:
                masked["phone"] = phone[:-7] + "*******"
        
        # Mask Names if not verified
        if "full_name" in masked and masked["full_name"]:
            name = str(masked["full_name"])
            parts = name.split()
            if len(parts) > 1:
                masked["full_name"] = f"{parts[0]} {parts[1][0]}."
            else:
                masked["full_name"] = f"{name[0]}..."
                
        return masked

    @staticmethod
    def detect_injection(text: str) -> bool:
        """
        Simple heuristic for prompt injection detection.
        Matches 'Prompt Injection Detector' component in the diagram.
        """
        patterns = [
            r"ignore previous instructions",
            r"disregard all previous",
            r"new system prompt",
            r"acting as a",
            r"system bypass"
        ]
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

_security_service = SecurityService()

def get_security_service():
    return _security_service
