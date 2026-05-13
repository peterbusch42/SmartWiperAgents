import asyncio, signal, warnings, sys, os
warnings.filterwarnings("ignore", category=DeprecationWarning)

from velocitas_sdk.vehicle_app import VehicleApp
from vehicle import Vehicle, vehicle
from graph.wiper_graph import build_graph
from agents.actuator_agent import set_vehicle

class SmartWiperApp(VehicleApp):

    def __init__(self, vehicle_client: Vehicle):
        super().__init__()
        self.Vehicle = vehicle_client
        self.graph   = build_graph()
        self._done   = asyncio.Event()
        self._current_wiper_mode = "OFF"
        set_vehicle(vehicle_client)

    async def on_start(self):

        

        async def on_hood_changed(reply):
            
            hood_dp = reply.get(self.Vehicle.Body.Hood.IsOpen)
            hood_open: bool = bool(hood_dp.value)
            
            mode_reply  = await self.Vehicle.Body.Windshield.Front.Wiping.Mode.get()
            speed_reply = await self.Vehicle.Speed.get()
            mode  = str(mode_reply.value) if mode_reply.value else "OFF"
            speed = float(speed_reply.value or 0.0)

            print(f"[DEBUG] hood_open={hood_open!r}  mode={mode!r}  speed={speed!r}")

            initial_state = {
                "hood_is_open":       hood_open,
                "current_wiper_mode": mode,
                "vehicle_speed":      speed,
                "safety_assessment":  None,
                "safety_risk_level":  None,
                "decided_action":     None,
                "reasoning_log":      [],
                "next_agent":         None,
            }


            print("[Velocitas → Agents] Invoking LangGraph...")
            final = await self.graph.ainvoke(initial_state)

            print("\n=== AGENT REASONING TRACE ===")
            for line in final["reasoning_log"]:
                print(" ", line)
            print(f"  Final action: {final['decided_action']}")
            print("=============================\n")

            self._done.set()
        
        print("[Velocitas] Scheibenwischer auf MEDIUM schalten")
        self._current_wiper_mode = "MEDIUM"
        await self.Vehicle.Body.Windshield.Front.Wiping.Mode.set("MEDIUM")

        await self.Vehicle.Body.Hood.IsOpen.subscribe(on_hood_changed)
        print("[Velocitas] Listener registriert")

        print("[Velocitas] Motorhaube öffnen")
        await self.Vehicle.Body.Hood.IsOpen.set(True)

        #start of the demo:
        

        await self._done.wait()                # ← wartet bis Agent-Trace fertig
        print("[Velocitas] Demo abgeschlossen — App beendet.")
        sys.exit(0)                            # ← sauber, kein RuntimeError

async def main():
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, loop.stop)
    app = SmartWiperApp(vehicle)
    if os.getenv("MOCK_VEHICLE"):
        await app.on_start()
    else:
        await app.run()

asyncio.run(main())