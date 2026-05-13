from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
import json, re
from graph.state import WiperState
 
llm = ChatOllama(
    model="llama3.1:8b",
    temperature=0.0,
    base_url="http://localhost:11434"
)
 
SAFETY_PROMPT = """You are a vehicle Safety Agent. Assess risk based on VSS signals.
 
Context: Wipers moving while the hood is open can DAMAGE the wiper motor
and the open hood (mechanical collision). This is a HIGH risk situation.
 
Given the state, return a JSON object:
{
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "assessment": "<one-sentence reasoning>",
  "recommended_action": "STOP_WIPER" | "KEEP_WIPER" | "REDUCE_WIPER"
}
 
Return ONLY valid JSON, nothing else.
"""
 
def safety_node(state: WiperState) -> WiperState:
    user = (
        f"hood_is_open={state['hood_is_open']}, "
        f"current_wiper_mode={state['current_wiper_mode']}, "
        f"vehicle_speed={state['vehicle_speed']} km/h"
    )
    response = llm.invoke([
        SystemMessage(content=SAFETY_PROMPT),
        HumanMessage(content=user)
    ]).content
 
    match = re.search(r'\{.*\}', response, re.DOTALL)
    data = json.loads(match.group(0))
 
    state["safety_risk_level"]  = data["risk_level"]
    state["safety_assessment"]  = data["assessment"]
    state["decided_action"]     = data["recommended_action"]
    state["reasoning_log"].append(
        f"[Safety] {data['risk_level']}: {data['assessment']}"
    )
    return state