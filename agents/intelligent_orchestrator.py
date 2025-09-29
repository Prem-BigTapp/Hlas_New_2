import logging
from app.session_manager import update_session, get_stage, set_stage, clear_session_for_global_reset
from .travel_payload_agent import run_travel_payload_agent
from .quote_manager import run_quote_generation

logger = logging.getLogger(__name__)

def orchestrate_chat(user_message: str, session_id: str) -> str:
    """Orchestrator for the new, multi-path travel agent."""
    try:
        # On "hi", reset everything and start the conversation
        if user_message.strip().lower() in ["hi", "hello"]:
            clear_session_for_global_reset(session_id)
            agent_response_dict = run_travel_payload_agent(user_message, [], session_id)
            agent_response = agent_response_dict.get("output", "Hello! How can I help you today?")
            update_session(session_id, user_message, agent_response)
            return agent_response

        stage = get_stage(session_id)
        logger.info(f"Current stage for session {session_id}: {stage}")

        if stage == "payload_collection" or not stage:
            set_stage(session_id, "payload_collection")
            response_data = run_travel_payload_agent(user_message, [], session_id)
            agent_response = response_data.get("output")
        elif stage == "quote_generation":
            response_data = run_quote_generation(session_id)
            agent_response = response_data.get("output")
        else:
            # Fallback to starting a new collection
            set_stage(session_id, "payload_collection")
            response_data = run_travel_payload_agent(user_message, [], session_id)
            agent_response = response_data.get("output")

        update_session(session_id, user_message, agent_response)
        return agent_response
        
    except Exception as e:
        logger.error(f"Critical error in orchestrate_chat for session {session_id}: {str(e)}")
        return "I'm sorry, a critical error occurred. Please start over by saying 'hi'."