# supervisor.py — Regel-basiert, kein LLM-Halluzinations-Risiko
from graph.state import WiperState

def supervisor_node(state: WiperState) -> WiperState:
    if state["safety_assessment"] is None:
        decision = "safety_agent"
    elif state["decided_action"] is None:
        decision = "actuator_agent"
    else:
        decision = "END"

    state["next_agent"] = decision
    state["reasoning_log"].append(f"[Supervisor] → {decision}")
    return state