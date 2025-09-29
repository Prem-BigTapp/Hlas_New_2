import logging
import json
import httpx
import os
from datetime import datetime
from app.session_manager import get_session, set_stage, get_collected_info, update_conversation_context

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "https://api-sandbox.hlas.com.sg")
QUOTE_ENDPOINT = "/api/v2/quotation/generate"
TEST_MODE = os.getenv("TEST_MODE", "True").lower() == "false"

def _call_generate_quote_api_mock(quote_request: dict) -> dict:
    """ Mocks the API call with a response containing all plan prices. """
    logger.warning("--- MOCK API CALL to /api/v2/quotation/generate ---")
    mock_response = {
        "timestamp": datetime.now().isoformat(), "success": "true", "warnings": [], "errors": [],
        "data": {
            "premiums": {
                "basic": {"discounted_premium": 21.00},
                "silver": {"discounted_premium": 28.00},
                "gold": {"discounted_premium": 36.50},
                "platinum": {"discounted_premium": 47.00}
            }
        }
    }
    logger.info(f"Mock API Response: {json.dumps(mock_response, indent=2)}")
    return mock_response

def _call_generate_quote_api(quote_request: dict) -> dict:
    """ Calls the REAL quotation API or returns a mock if in Test Mode. """
    if TEST_MODE:
        return _call_generate_quote_api_mock(quote_request)
    
    logger.info(f"--- Calling REAL API: {API_BASE_URL}{QUOTE_ENDPOINT} ---")
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(f"{API_BASE_URL}{QUOTE_ENDPOINT}", json=quote_request)
            response.raise_for_status() 
            response_data = response.json()
            logger.info(f"Real API Response: {json.dumps(response_data, indent=2)}")
            return response_data
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling quote API: {e.response.status_code} - {e.response.text}")
        return {"success": "false", "errors": [f"HTTP error: {e.response.status_code}"]}
    except Exception as e:
        logger.error(f"Unknown error calling quote API: {e}")
        return {"success": "false", "errors": [f"Unknown error: {e}"]}

def run_quote_generation(session_id: str) -> dict:
    """ 
    Retrieves the final payload, gets quotes for ALL plans, and displays them as a comparison.
    """
    try:
        collected_info = get_collected_info(session_id)
        final_payload = collected_info.get("payload")

        if not final_payload:
            set_stage(session_id, "payload_collection") 
            return {"output": "I seem to have lost your details. Let's start over."}

        quote_response = _call_generate_quote_api(final_payload)
        
        if quote_response.get("success") not in ["ok", "true"]:
            errors = quote_response.get("errors", ["Unknown API error"])
            return {"output": f"Sorry, there was an error getting the quote: {errors[0]}"}
        
        # --- NEW PLAN COMPARISON LOGIC ---
        premiums = quote_response.get("data", {}).get("premiums", {})
        
        if not premiums:
            return {"output": "I'm sorry, I couldn't retrieve the price list. Please try again."}

        # Build the comparison message string
        final_message = "Here are the available plans for your trip:\n"
        
        plans_to_show = [('basic', '150,000'), ('silver', '250,000'), ('gold', '500,000'), ('platinum', '750,000')]
        
        for plan_name, med_coverage in plans_to_show:
            plan_info = premiums.get(plan_name)
            if plan_info:
                price = plan_info.get("discounted_premium", 0.0)
                price_str = f"S${price:.2f}"
                
                final_message += f"""
---
**{plan_name.capitalize()} Plan**
*Premium: **{price_str}***
*Med. Coverage (Overseas): up to ${med_coverage}*
"""

        final_message += "\n---\nPlease choose a plan by typing its name (e.g., 'gold'), or type 'cancel' to start over."
        
        # We will wait for the user to choose a plan.
        set_stage(session_id, "plan_selection") 
        update_conversation_context(session_id, official_premiums=premiums)

        return {"output": final_message}

    except Exception as e:
        logger.error(f"Error in run_quote_generation for session {session_id}: {str(e)}")
        set_stage(session_id, "initial") 
        return {"output": "I'm sorry, I ran into an error while generating your quote."}