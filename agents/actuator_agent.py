from graph.state import WiperState
# Globale Referenz auf Velocitas Vehicle-Objekt (wird bei App-Start gesetzt)
_vehicle_ref = None
 
def set_vehicle(v):
    global _vehicle_ref
    _vehicle_ref = v
 
async def actuator_node(state: WiperState) -> WiperState:
    action = state["decided_action"]
 
    if action == "STOP_WIPER":
        await _vehicle_ref.Body.Windshield.Front.Wiping.Mode.set("OFF")
        msg = "Executed: Wiper.Mode = OFF via Velocitas SDK"
    elif action == "REDUCE_WIPER":
        await _vehicle_ref.Body.Windshield.Front.Wiping.Mode.set("SLOW")
        msg = "Executed: Wiper.Mode = SLOW"
    else:
        msg = "Executed: no change (KEEP_WIPER)"
 
    state["reasoning_log"].append(f"[Actuator] {msg}")
    return state