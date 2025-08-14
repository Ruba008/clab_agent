from google.cloud import dialogflow_v2 as dialogflow
from google.api_core.exceptions import NotFound

PROJECT_ID = "intent-classifier-dhrd"
SESSION_ID = "teste1"
LANG = "en"

def detect_intent(user_input: str) -> str:
    agent = dialogflow.AgentsClient().get_agent(request={"parent": f"projects/{PROJECT_ID}"})
    client = dialogflow.SessionsClient()
    session = client.session_path(PROJECT_ID, SESSION_ID)
    text_input = dialogflow.TextInput(text=user_input, language_code=LANG)
    query_input = dialogflow.QueryInput(text=text_input)
    resp = client.detect_intent(request={"session": session, "query_input": query_input})
    
    return resp.query_result.intent.display_name