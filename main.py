# from fastapi import FastAPI, Header, HTTPException
# from final.session_memory import SessionMemory
# from final.session_context_memory import SessionContextMemory
# from final.callback_service import send_callback
# from final.agents.team_orchestrator import (
#     process_message_reply,
#     process_message_extraction
# )
# from final.config import API_KEY
# import time

# app = FastAPI()

# memory = SessionMemory(max_history=20)
# context_memory = SessionContextMemory()

# MAX_MESSAGES_PER_SESSION = 6
# MIN_MESSAGES_BEFORE_CALLBACK = 4

# # Track completed sessions
# session_completed = {}


# @app.post("/honeypot")
# async def honeypot(payload: dict, x_api_key: str = Header(None)):

#     api_start_time = time.perf_counter()
#     print("\n================ API REQUEST START ================")

#     if x_api_key != API_KEY:
#         raise HTTPException(status_code=403, detail="Invalid API Key")

#     session_id = payload["sessionId"]
#     msg = payload["message"]["text"]

#     # 🔒 Block if already completed
#     # if session_completed.get(session_id, False):
#     #     return {
#     #         "status": "completed",
#     #         "reply": "Session already completed."
#     #     }
#     if session_completed.get(session_id, False):
#         return {
#             "status": "completed"
#         }


#     # 1️⃣ Store scammer message
#     memory.add_message(session_id, "scammer", msg)

#     history = memory.get_formatted_history(session_id)
#     previous_intel = context_memory.get_intel(session_id)
#     message_count = len(memory.get_history(session_id))

#     # 2️⃣ Generate reply
#     scam, reply, session_end, persona, action = await process_message_reply(
#         msg,
#         history,
#         session_id,
#         previous_intel,
#         message_count
#     )

#     # Store reply
#     memory.add_message(session_id, "user", reply)

#     # 3️⃣ If scam → run extraction immediately
#     if scam:
#         intel = await process_message_extraction(
#             msg,
#             previous_intel,
#             persona,
#             action
#         )

#         if intel:
#             context_memory.append_intel(session_id, intel)

#     total_messages = len(memory.get_history(session_id))

#     # 🔥 Hard stop condition
#     if (
#         total_messages >= MAX_MESSAGES_PER_SESSION or
#         (session_end and total_messages >= MIN_MESSAGES_BEFORE_CALLBACK)
#     ):
#         cumulative_intel = context_memory.get_intel(session_id)

#         print(f"\n🔥 TRIGGERING CALLBACK (SYNC) for {session_id} 🔥")

#         await send_callback(
#             session_id,
#             total_messages,
#             cumulative_intel
#         )

#         # Clear session safely
#         memory.clear_session(session_id)
#         context_memory.clear_session(session_id)
#         session_completed[session_id] = True

#         print(f"✅ Session {session_id} completed & cleared.")

#     print(f"🚀 API RESPONSE SENT IN: {time.perf_counter() - api_start_time:.3f}s")
#     print("================ API REQUEST END ==================\n")

#     return {
#         "status": "success",
#         "reply": reply
#     }

from fastapi import FastAPI, Header, HTTPException
from final.session_memory import SessionMemory
from final.session_context_memory import SessionContextMemory
from final.callback_service import send_callback
from final.agents.team_orchestrator import (
    process_message_reply,
    process_message_extraction
)
from final.config import API_KEY
import time

app = FastAPI()

memory = SessionMemory(max_history=20)
context_memory = SessionContextMemory()

MAX_MESSAGES_PER_SESSION = 6
MIN_MESSAGES_BEFORE_CALLBACK = 4

# Track completed sessions
session_completed = {}


@app.post("/honeypot")
async def honeypot(payload: dict, x_api_key: str = Header(None)):

    api_start_time = time.perf_counter()
    print("\n================ API REQUEST START ================")

    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    session_id = payload["sessionId"]
    msg = payload["message"]["text"]

    # If session already completed, return hardcoded final message
    if session_completed.get(session_id, False):
        return {
            "status": "completed",
            "reply": "⚠ Conversation has reached its maximum allowed messages. Please start a new session for further queries."
        }

    # 1️⃣ Store scammer message
    memory.add_message(session_id, "scammer", msg)

    history = memory.get_formatted_history(session_id)
    previous_intel = context_memory.get_intel(session_id)
    message_count = len(memory.get_history(session_id))

    # 2️⃣ Determine if we hit max turns
    max_turn_reached = message_count >= MAX_MESSAGES_PER_SESSION

    # 3️⃣ Generate reply only if max turns not reached
    if not max_turn_reached:
        scam, reply, session_end, persona, action = await process_message_reply(
            msg,
            history,
            session_id,
            previous_intel,
            message_count
        )
    else:
        scam, reply, session_end, persona, action = True, "⚠ Maximum message limit reached. Stopping further replies.", True, None, None

    # Store reply (either persona or hardcoded)
    memory.add_message(session_id, "user", reply)

    # 4️⃣ Always extract intelligence if it's a scam
    if scam:
        intel = await process_message_extraction(
            msg,
            previous_intel,
            persona,
            action
        )
        if intel:
            context_memory.append_intel(session_id, intel)

    # 5️⃣ Trigger callback if max turn or session_end
    cumulative_intel = context_memory.get_intel(session_id)
    total_messages = len(memory.get_history(session_id))
    if max_turn_reached or (session_end and total_messages >= MIN_MESSAGES_BEFORE_CALLBACK):
        print(f"\n🔥 TRIGGERING CALLBACK (FINAL) for {session_id} 🔥")
        await send_callback(
            session_id,
            total_messages,
            cumulative_intel
        )

        # Clear session
        memory.clear_session(session_id)
        context_memory.clear_session(session_id)
        session_completed[session_id] = True
        print(f"✅ Session {session_id} completed & cleared.")

    print(f"🚀 API RESPONSE SENT IN: {time.perf_counter() - api_start_time:.3f}s")
    print("================ API REQUEST END ==================\n")

    return {
        "status": "success",
        "reply": reply
    }
