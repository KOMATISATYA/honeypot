import requests

async def send_callback(session_id, total_messages, intel, duration_seconds):

    if hasattr(intel, "model_dump"):
        extracted_data = intel.model_dump()
        agent_notes = intel.agentNotes
    elif isinstance(intel, dict):
        extracted_data = intel
        agent_notes = intel.get("agentNotes", "")
    else:
        extracted_data = {}
        agent_notes = ""
        
    scam = extracted_data.get("scamDetected", False)
    extracted_data.pop("scamDetected", None)
    
    engagement_metrics ={
        "engagementDurationSeconds":duration_seconds,
        "totalMessagesExchanged":total_messages
    }
    payload = {
        "sessionId": session_id,
        "scamDetected": scam,
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": extracted_data,
        "engagementMetrics":engagement_metrics,
        "agentNotes": agent_notes
    }
    print("payload",payload)
    try:
        response = requests.post(
            "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
            json=payload,
            timeout=5
        )

    except Exception as e:
        print("Callback error:", e)








