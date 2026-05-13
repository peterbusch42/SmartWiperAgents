from langgraph.graph import StateGraph, END
from graph.state import WiperState
from agents.supervisor import supervisor_node
from agents.safety_agent import safety_node
from agents.actuator_agent import actuator_node
 
def route(state: WiperState) -> str:
    return state["next_agent"]
 
def build_graph():
    g = StateGraph(WiperState)
 
    g.add_node("supervisor",      supervisor_node)
    g.add_node("safety_agent",    safety_node)
    g.add_node("actuator_agent",  actuator_node)
 
    g.set_entry_point("supervisor")
    g.add_conditional_edges("supervisor", route, {
        "safety_agent":   "safety_agent",
        "actuator_agent": "actuator_agent",
        "END":            END,
    })
 
    # Nach Spezialisten zurück zum Supervisor (Feedback-Loop)
    g.add_edge("safety_agent",   "supervisor")
    g.add_edge("actuator_agent", "supervisor")
 
    return g.compile()