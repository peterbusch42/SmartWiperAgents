"""
Mock Vehicle implementation for SmartWiper testing without KUKSA databroker.
Uses in-memory mock for all vehicle signals.
"""


class MockResult:
    """Simple result with a .value attribute, mimics TypedDataPointResult."""

    def __init__(self, value):
        self.value = value


class MockDataPoint:
    """Mock implementation of a vehicle datapoint"""

    def __init__(self, name: str, initial_value=None):
        self.name = name
        self._value = initial_value
        self._subscribers = []

    async def get(self):
        """Return current value as a MockResult."""
        return MockResult(self._value)

    async def set(self, value):
        """Set value and notify subscribers."""
        print(f"[Mock Vehicle] {self.name} = {value}")
        self._value = value
        for callback in self._subscribers:
            await callback(MockReply({self: MockResult(value)}))

    async def subscribe(self, callback):
        """Subscribe to value changes."""
        self._subscribers.append(callback)
        print(f"[Mock Vehicle] Subscribed to {self.name}")

    @property
    def value(self):
        return self._value


class MockReply:
    """Mock reply object returned to subscription callbacks."""

    def __init__(self, datapoints: dict):
        self._datapoints = datapoints

    def get(self, datapoint):
        """Return MockResult for the given datapoint."""
        return self._datapoints.get(datapoint)


class Vehicle:
    """Mock Vehicle with VSS signal structure for SmartWiper demo"""
    
    def __init__(self):
        # Build the VSS-like structure
        self.Speed = MockDataPoint("Vehicle.Speed", 0.0)
        
        # Body.Windshield.Front.Wiping.Mode
        class WipingMode:
            def __init__(self):
                self.Mode = MockDataPoint("Vehicle.Body.Windshield.Front.Wiping.Mode", "OFF")
        
        class FrontWindshield:
            def __init__(self):
                self.Wiping = WipingMode()
        
        class Windshield:
            def __init__(self):
                self.Front = FrontWindshield()
        
        # Body.Hood.IsOpen
        class Hood:
            def __init__(self):
                self.IsOpen = MockDataPoint("Vehicle.Body.Hood.IsOpen", False)
        
        class Body:
            def __init__(self):
                self.Hood = Hood()
                self.Windshield = Windshield()
        
        self.Body = Body()


# Global vehicle instance
vehicle = Vehicle()
