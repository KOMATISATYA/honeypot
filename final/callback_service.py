# import requests

# async def send_callback(session_id, total_messages, intel):

#     # Handle both dict and Pydantic model safely
#     if hasattr(intel, "model_dump"):
#         extracted_data = intel.model_dump()
#         agent_notes = intel.agentNotes
#     elif isinstance(intel, dict):
#         extracted_data = intel
#         agent_notes = intel.get("agentNotes", "")
#     else:
#         extracted_data = {}
#         agent_notes = ""

#     payload = {
#         "sessionId": session_id,
#         "scamDetected": True,
#         "totalMessagesExchanged": total_messages,
#         "extractedIntelligence": extracted_data,
#         "agentNotes": agent_notes
#     }

#     try:
#         response = requests.post(
#             "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
#             json=payload,
#             timeout=5
#         )

#         print("Callback Status Code:", response.status_code)
#         print("Callback Response:", response.text)

#     except Exception as e:
#         print("Callback error:", e)

import httpx
import asyncio
import logging
import time
import traceback

GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
CALLBACK_TIMEOUT = 30
CALLBACK_MAX_RETRIES = 5
CALLBACK_RETRY_DELAY = 2

logger = logging.getLogger(__name__)


async def send_callback(payload: dict, max_retries: int = CALLBACK_MAX_RETRIES) -> bool:
    """
    Robust async callback sender with retry + timeout + detailed logging
    Returns True if successful, False otherwise
    """

    logger.info("=" * 70)
    logger.info("📤 INITIATING CALLBACK")
    logger.info(f"URL: {GUVI_CALLBACK_URL}")
    logger.info(f"Payload: {payload}")
    logger.info("=" * 70)

    for attempt in range(max_retries):

        logger.info(f"\n🔄 Attempt {attempt + 1}/{max_retries}")

        try:
            start_time = time.perf_counter()

            async with httpx.AsyncClient(
                timeout=CALLBACK_TIMEOUT,
                follow_redirects=True
            ) as client:

                response = await client.post(
                    GUVI_CALLBACK_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

            end_time = time.perf_counter()

            logger.info(f"📡 Status Code: {response.status_code}")
            logger.info(f"⏱️ Callback Time: {end_time - start_time:.3f} sec")
            logger.info(f"📝 Response: {response.text[:500]}")
            


            if response.status_code in (200, 201, 202):
                logger.info("✅ CALLBACK SUCCESS")
                return True
            else:
                logger.warning(f"⚠️ Unexpected status: {response.status_code}")

        except httpx.TimeoutException as e:
            logger.error(f"❌ Timeout after {CALLBACK_TIMEOUT}s: {e}")

        except httpx.ConnectError as e:
            logger.error(f"❌ Connection error: {e}")

        except Exception as e:
            logger.error(f"❌ Unexpected error: {type(e).__name__}: {e}")
            logger.error(traceback.format_exc())

        if attempt < max_retries - 1:
            wait_time = CALLBACK_RETRY_DELAY * (attempt + 1)
            logger.info(f"⏳ Waiting {wait_time}s before retry...")
            await asyncio.sleep(wait_time)

    logger.error("💥 CALLBACK FAILED AFTER ALL RETRIES")
    return False




