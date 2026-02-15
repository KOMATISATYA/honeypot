# from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
# from final.session_memory import SessionMemory
# from final.session_context_memory import SessionContextMemory
# from final.callback_service import send_callback
# from final.agents.team_orchestrator import process_message_reply, process_message_extraction
# from final.config import API_KEY
# import time
# import asyncio

# app = FastAPI()

# memory = SessionMemory(max_history=20)
# context_memory = SessionContextMemory()

# MAX_MESSAGES_PER_SESSION = 6
# MIN_MESSAGES_BEFORE_CALLBACK = 4
# callback_sent_tracker = {}


# async def background_processing(session_id, message, previous_intel, persona, action, session_end):
#     """
#     Handles heavy tasks in the background after the user has received the reply.
#     """
#     try:
#         # 1. Extraction & RL Updates
#         intel = await process_message_extraction(message, previous_intel, persona, action)

#         # 2. Store extracted intelligence
#         if intel:
#             context_memory.append_intel(session_id, intel)

#         # 3. Check for Callback
#         cumulative_intel = context_memory.get_intel(session_id)
#         total_messages = len(memory.get_history(session_id))

#         if session_id not in callback_sent_tracker:
#             callback_sent_tracker[session_id] = False

#         if (
#             not callback_sent_tracker[session_id] and
#             (
#                 total_messages >= MAX_MESSAGES_PER_SESSION
#                 or (session_end and total_messages >= MIN_MESSAGES_BEFORE_CALLBACK)
#             )
#         ):
#             print(f"\n🔥 TRIGGERING CALLBACK in Background for {session_id} 🔥")
#             await send_callback(
#                 session_id,
#                 total_messages,
#                 cumulative_intel
#             )
#             callback_sent_tracker[session_id] = True

#         # 4. Clear memory if session end
#         if session_end:
#             await asyncio.sleep(1) # Small delay to ensure no race conditions
#             memory.clear_session(session_id)
#             context_memory.clear_session(session_id)
#             callback_sent_tracker.pop(session_id, None)
#             print(f"� Session {session_id} cleared in background.")

#     except Exception as e:
#         print(f"❌ Background Processing Error for {session_id}: {e}")


# @app.post("/honeypot")
# async def honeypot(payload: dict, background_tasks: BackgroundTasks, x_api_key: str = Header(None)):

#     api_start_time = time.perf_counter()
#     print("\n================ API REQUEST START ================")

#     if x_api_key != API_KEY:
#         raise HTTPException(status_code=403, detail="Invalid API Key")

#     session_id = payload["sessionId"]
#     msg = payload["message"]["text"]

#     # 1. Store scammer message
#     memory.add_message(session_id, "scammer", msg)
    
#     # 2. Get Context
#     history = memory.get_formatted_history(session_id)
#     previous_intel = context_memory.get_intel(session_id)
#     message_count = len(memory.get_history(session_id))

#     # 3. Quick Reply Phase
#     scam, reply, session_end, persona, action = await process_message_reply(
#         msg,
#         history,
#         session_id,
#         previous_intel,
#         message_count
#     )

#     # 4. Store persona reply immediately (critical for history chain)
#     memory.add_message(session_id, "user", reply)

#     # 5. Offload everything else to background
#     if scam:
#         background_tasks.add_task(
#             background_processing,
#             session_id,
#             msg,
#             previous_intel,
#             persona,
#             action,
#             session_end
#         )

#     print(f"🚀 API RESPONSE SENT IN: {time.perf_counter() - api_start_time:.3f}s")
#     print("================ API REQUEST END ==================\n")

#     return {
#         "status": "success",
#         "reply": reply
#     }

from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from final.session_memory import SessionMemory
from final.session_context_memory import SessionContextMemory
from final.callback_service import send_callback
from final.agents.team_orchestrator import process_message_reply, process_message_extraction
from final.config import API_KEY
import time
import asyncio

app = FastAPI()

memory = SessionMemory(max_history=20)
context_memory = SessionContextMemory()

MAX_MESSAGES_PER_SESSION = 6
MIN_MESSAGES_BEFORE_CALLBACK = 4

# 🔐 Session State Manager
session_state = {}


# -------------------------
# Safe Delayed Cleanup
# -------------------------
async def delayed_cleanup(session_id):
    """
    Wait before clearing session to avoid race condition
    when extra messages arrive after callback.
    """
    await asyncio.sleep(30)

    if session_id in session_state and not session_state[session_id]["active"]:
        memory.clear_session(session_id)
        context_memory.clear_session(session_id)
        session_state.pop(session_id, None)
        print(f"🧹 Session {session_id} safely cleaned after delay.")


# -------------------------
# Background Processing
# -------------------------
async def background_processing(session_id, message, previous_intel, persona, action, session_end):
    try:
        # 1. Extraction
        intel = await process_message_extraction(message, previous_intel, persona, action)

        if intel:
            context_memory.append_intel(session_id, intel)

        # 2. Ensure session exists
        if session_id not in session_state:
            session_state[session_id] = {
                "callback_sent": False,
                "active": True
            }

        cumulative_intel = context_memory.get_intel(session_id)
        total_messages = len(memory.get_history(session_id))

        # 3. Trigger Callback ONLY once
        if (
            session_state[session_id]["active"]
            and not session_state[session_id]["callback_sent"]
            and (
                total_messages >= MAX_MESSAGES_PER_SESSION
                or (session_end and total_messages >= MIN_MESSAGES_BEFORE_CALLBACK)
            )
        ):
            print(f"\n🔥 TRIGGERING CALLBACK in Background for {session_id} 🔥")

            await send_callback(
                session_id,
                total_messages,
                cumulative_intel
            )

            session_state[session_id]["callback_sent"] = True

        # 4. Soft close session (DO NOT DELETE immediately)
        if session_end:
            print(f"🟡 Session {session_id} marked inactive.")
            session_state[session_id]["active"] = False

            # Cleanup later safely
            asyncio.create_task(delayed_cleanup(session_id))

    except Exception as e:
        print(f"❌ Background Processing Error for {session_id}: {e}")


# -------------------------
# Honeypot API
# -------------------------
@app.post("/honeypot")
async def honeypot(payload: dict, background_tasks: BackgroundTasks, x_api_key: str = Header(None)):

    api_start_time = time.perf_counter()
    print("\n================ API REQUEST START ================")

    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    session_id = payload["sessionId"]
    msg = payload["message"]["text"]

    # Ensure session state exists
    if session_id not in session_state:
        session_state[session_id] = {
            "callback_sent": False,
            "active": True
        }

    # 1. Store scammer message
    memory.add_message(session_id, "scammer", msg)

    # 2. Get Context
    history = memory.get_formatted_history(session_id)
    previous_intel = context_memory.get_intel(session_id)
    message_count = len(memory.get_history(session_id))

    # 3. Quick Reply Phase (FAST)
    scam, reply, session_end, persona, action = await process_message_reply(
        msg,
        history,
        session_id,
        previous_intel,
        message_count
    )

    # 4. Store persona reply immediately
    memory.add_message(session_id, "user", reply)

    # 5. Run heavy tasks in background
    if scam:
        background_tasks.add_task(
            background_processing,
            session_id,
            msg,
            previous_intel,
            persona,
            action,
            session_end
        )

    print(f"🚀 API RESPONSE SENT IN: {time.perf_counter() - api_start_time:.3f}s")
    print("================ API REQUEST END ==================\n")

    return {
        "status": "success",
        "reply": reply
    }

