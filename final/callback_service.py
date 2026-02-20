import requests

async def send_callback(session_id, total_messages, intel):

    if hasattr(intel, "model_dump"):
        extracted_data = intel.model_dump()
        agent_notes = intel.agentNotes
    elif isinstance(intel, dict):
        extracted_data = intel
        agent_notes = intel.get("agentNotes", "")
    else:
        extracted_data = {}
        agent_notes = ""

    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": extracted_data,
        "agentNotes": agent_notes
    }

    try:
        response = requests.post(
            "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
            json=payload,
            timeout=5
        )

    except Exception as e:
        print("Callback error:", e)
