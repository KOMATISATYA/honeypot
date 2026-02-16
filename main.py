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

# MAX_MESSAGES_PER_SESSION = 10
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
# import logging

# # -------------------------
# # LOGGER SETUP
# # -------------------------
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)s | %(message)s"
# )

# logger = logging.getLogger("honeypot")

# app = FastAPI()

# memory = SessionMemory(max_history=20)
# context_memory = SessionContextMemory()

# MAX_MESSAGES_PER_SESSION = 10
# MIN_MESSAGES_BEFORE_CALLBACK = 4

# # Track completed sessions
# session_completed = {}


# # -------------------------
# # EARLY INTEL CHECK
# # Stop if atleast 2 intel fields are filled
# # -------------------------
# def has_minimum_intel(intel: dict, min_fields):
#     if not intel:
#         return False

#     fields = [
#         "upiIds",
#         "phishingLinks",
#         "phoneNumbers",
#         "bankAccounts",
#         "suspiciousKeywords"
#     ]

#     filled = 0

#     for field in fields:
#         if intel.get(field) and len(intel.get(field)) > 0:
#             filled += 1

#     return filled >= min_fields


# @app.post("/honeypot")
# async def honeypot(payload: dict, x_api_key: str = Header(None)):

#     api_start_time = time.perf_counter()
#     logger.info("========== NEW HONEYPOT REQUEST ==========")

#     if x_api_key != API_KEY:
#         logger.warning("Invalid API Key received")
#         raise HTTPException(status_code=403, detail="Invalid API Key")

#     session_id = payload["sessionId"]
#     msg = payload["message"]["text"]

#     logger.info(f"Session: {session_id}")
#     logger.info(f"Incoming Message: {msg}")

#     # 🔒 Block if already completed
#     if session_completed.get(session_id, False):
#         logger.info(f"Session {session_id} already completed. Ignoring.")
#         return {
#             "status": "completed"
#         }

#     # 1️⃣ Store scammer message
#     memory.add_message(session_id, "scammer", msg)
#     logger.info("Message stored in memory")

#     history = memory.get_formatted_history(session_id)
#     previous_intel = context_memory.get_intel(session_id)
#     message_count = len(memory.get_history(session_id))

#     logger.info(f"Message count: {message_count}")

#     # 2️⃣ Generate reply
#     logger.info("Generating persona reply...")
#     scam, reply, session_end, persona, action = await process_message_reply(
#         msg,
#         history,
#         session_id,
#         previous_intel,
#         message_count
#     )

#     logger.info(f"Reply Generated: {reply}")
#     logger.info(f"Persona: {persona} | Action: {action}")
#     logger.info(f"Session end signal: {session_end}")

#     # Store AI reply
#     memory.add_message(session_id, "user", reply)

#     # 3️⃣ If scam → run extraction immediately
#     if scam:
#         logger.info("Scam detected → running extraction")

#         intel = await process_message_extraction(
#             msg,
#             previous_intel,
#             persona,
#             action
#         )

#         if intel:
#             logger.info("Intel extracted successfully")

#             context_memory.append_intel(session_id, intel)
#             cumulative_intel = context_memory.get_intel(session_id)

#             logger.info(f"Cumulative Intel: {cumulative_intel}")

#             # 🔥 EARLY STOP if atleast 2 intel fields captured
#             if has_minimum_intel(cumulative_intel, min_fields=4):

#                 total_messages = len(memory.get_history(session_id))

#                 logger.info(f"🔥 EARLY INTEL STOP triggered for {session_id}")

#                 await send_callback(
#                     session_id,
#                     total_messages,
#                     cumulative_intel
#                 )

#                 logger.info("Callback sent successfully")

#                 # 🧹 Clear session
#                 memory.clear_session(session_id)
#                 context_memory.clear_session(session_id)
#                 session_completed[session_id] = True

#                 logger.info(f"Session {session_id} cleared after EARLY STOP")

#                 logger.info(f"API time: {time.perf_counter() - api_start_time:.3f}s")
#                 return {
#                     "status": "completed"
#                 }

#     total_messages = len(memory.get_history(session_id))

#     # 🧱 HARD STOP (fallback)
#     if (
#         total_messages >= MAX_MESSAGES_PER_SESSION or
#         (session_end and total_messages >= MIN_MESSAGES_BEFORE_CALLBACK)
#     ):
#         cumulative_intel = context_memory.get_intel(session_id)

#         logger.info(f"🔥 HARD STOP triggered for {session_id}")

#         await send_callback(
#             session_id,
#             total_messages,
#             cumulative_intel
#         )

#         logger.info("Callback sent successfully")

#         # 🧹 Clear session safely
#         memory.clear_session(session_id)
#         context_memory.clear_session(session_id)
#         session_completed[session_id] = True

#         logger.info(f"Session {session_id} cleared after HARD STOP")

#     logger.info(f"API time: {time.perf_counter() - api_start_time:.3f}s")
#     logger.info("========== REQUEST COMPLETE ==========\n")

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

MAX_MESSAGES_PER_SESSION = 2
MIN_MESSAGES_BEFORE_CALLBACK = 4

# Track completed sessions
session_completed = {}
session_start_time = {}

@app.post("/honeypot")
async def honeypot(payload: dict, x_api_key: str = Header(None)):


    api_start_time = time.perf_counter()
    print("\n================ API REQUEST START ================")

    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    session_id = payload["sessionId"]
    msg = payload["message"]["text"]

    if session_id not in session_start_time:
        session_start_time[session_id] = time.time()

    # 🔒 Block if already completed
    # if session_completed.get(session_id, False):
    #     return {
    #         "status": "completed",
    #         "reply": "Session already completed."
    #     }
    if session_completed.get(session_id, False):
        return {
            "status": "completed"
        }


    # 1️⃣ Store scammer message
    memory.add_message(session_id, "scammer", msg)

    history = memory.get_formatted_history(session_id)
    previous_intel = context_memory.get_intel(session_id)
    message_count = len(memory.get_history(session_id))

    # 2️⃣ Generate reply
    scam, reply, session_end, persona, action = await process_message_reply(
        msg,
        history,
        session_id,
        previous_intel,
        message_count
    )

    # Store reply
    memory.add_message(session_id, "user", reply)

    # 3️⃣ If scam → run extraction immediately
    if scam:
        intel = await process_message_extraction(
            msg,
            previous_intel,
            persona,
            action
        )

        if intel:
            context_memory.append_intel(session_id, intel)

    total_messages = len(memory.get_history(session_id))

    # 🔥 Hard stop condition
    if (
        total_messages >= MAX_MESSAGES_PER_SESSION or
        (session_end and total_messages >= MIN_MESSAGES_BEFORE_CALLBACK)
    ):
        cumulative_intel = context_memory.get_intel(session_id)

        start_time = session_start_time.get(session_id, time.time())
        engagement_duration = int(time.time() - start_time)

        cumulative_intel["engagementMetrics"] = {
            "totalMessagesExchanged": total_messages,
            "engagementDurationSeconds": engagement_duration
        }
        print(cumulative_intel)
        print(f"\n🔥 TRIGGERING CALLBACK (SYNC) for {session_id} 🔥")

        await send_callback(
            session_id,
            total_messages,
            cumulative_intel
        )

        # Clear session safely
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
