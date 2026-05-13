from typing import TypedDict, Literal, Optional
 
class WiperState(TypedDict):
    # Input vom Velocitas-Event
    hood_is_open: bool
    current_wiper_mode: str
    vehicle_speed: float
    # Agent-Outputs
    safety_assessment: Optional[str]
    safety_risk_level: Optional[Literal["LOW", "MEDIUM", "HIGH"]]
    decided_action: Optional[Literal["STOP_WIPER", "KEEP_WIPER", "REDUCE_WIPER"]]
    reasoning_log: list[str]
    # Routing
    next_agent: Optional[str]