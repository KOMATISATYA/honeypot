from fastapi import FastAPI, Header, HTTPException
from final.session_memory import SessionMemory
from final.session_context_memory import SessionContextMemory
from final.callback_service import send_callback
from final.agents.team_orchestrator import process_message
from final.config import API_KEY
import time  # ✅ ADD THIS

app = FastAPI()

memory = SessionMemory(max_history=20)
context_memory = SessionContextMemory()

# -------------------------
# CONFIG
# -------------------------
MAX_MESSAGES_PER_SESSION = 10

# Track callback status per session
callback_sent_tracker = {}


@app.post("/honeypot")
async def honeypot(payload: dict, x_api_key: str = Header(None)):

    # ⏱️ Start total API timer
    api_start_time = time.perf_counter()

    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    session_id = payload["sessionId"]
    msg = payload["message"]["text"]

    # -------------------------
    # Store scammer message
    # -------------------------
    memory.add_message(session_id, "scammer", msg)

    history = memory.get_formatted_history(session_id)
    previous_intel = context_memory.get_intel(session_id)

    # -------------------------
    # Process Message (Measure LLM time)
    # -------------------------
    llm_start = time.perf_counter()

    scam, reply, intel, session_end = await process_message(
        msg,
        history,
        session_id,
        previous_intel
    )

    llm_end = time.perf_counter()
    print(f"🤖 process_message() time: {llm_end - llm_start:.3f} seconds")

    # -------------------------
    # Store persona reply
    # -------------------------
    memory.add_message(session_id, "user", reply)

    total_messages = len(memory.get_history(session_id))

    # -------------------------
    # Store extracted intelligence
    # -------------------------
    if intel:
        context_memory.append_intel(session_id, intel)

    cumulative_intel = context_memory.get_intel(session_id)

    # -------------------------
    # CALLBACK LOGIC
    # -------------------------
    MIN_MESSAGES_BEFORE_CALLBACK = 4

    if session_id not in callback_sent_tracker:
        callback_sent_tracker[session_id] = False

    # if (
    #     not callback_sent_tracker[session_id] and
    #     (
    #         total_messages >= MAX_MESSAGES_PER_SESSION
    #         or (session_end and total_messages >= MIN_MESSAGES_BEFORE_CALLBACK)
    #     )
    # ):

    #     print("\n🔥 TRIGGERING CALLBACK 🔥")
    #     print("Total Messages:", total_messages)
    #     print("Cumulative Intel:", cumulative_intel)

    #     callback_start = time.perf_counter()

    #     await send_callback(
    #         session_id,
    #         total_messages,
    #         cumulative_intel
    #     )

    #     callback_end = time.perf_counter()
    #     print(f"📡 send_callback() time: {callback_end - callback_start:.3f} seconds")

    #     callback_sent_tracker[session_id] = True
    if (
        not callback_sent_tracker[session_id] and
        (
            total_messages >= MAX_MESSAGES_PER_SESSION
            or (session_end and total_messages >= MIN_MESSAGES_BEFORE_CALLBACK)
        )
    ):
    
        print("\n🔥 TRIGGERING CALLBACK 🔥")
    
        payload = {
            "sessionId": session_id,
            "scamDetected": scam,
            "totalMessagesExchanged": total_messages,
            "extractedIntelligence": cumulative_intel,
            "agentNotes": f"Turns:{total_messages}"
        }
    
        callback_success = await send_callback(payload)
    
        print("📡 Callback sent:", callback_success)
    
        callback_sent_tracker[session_id] = True


    # -------------------------
    # Clear memory if session closed
    # -------------------------
    if session_end:
        memory.clear_session(session_id)
        context_memory.clear_session(session_id)
        callback_sent_tracker.pop(session_id, None)

    # ⏱️ End total API timer
    api_end_time = time.perf_counter()
    print(f"🚀 TOTAL API Response Time: {api_end_time - api_start_time:.3f} seconds")

    return {
        "status": "success",
        "reply": reply
    }

