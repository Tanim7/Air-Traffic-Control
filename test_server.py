from server import Plane, Runway, Gate, get_index_Landing_Runway, get_index_Gate, Runways, Gates

def test_plane_creation():
    plane = Plane(id=1, size="Large")
    assert plane.Plane_ID == 1
    assert plane.Size == "Large"

def test_set_flight_plan():
    plane = Plane(id=2, size="Small")
    plane.Set_Flight_Plan(LandingRunwayID=3, GateID=2, GateDelay=30, DepartureRunwayID=1)
    assert plane.Planned_LandingRunway_ID == 3
    assert plane.Planned_Gate_ID == 2
    assert plane.Planned_Gate_Delay == 30
    assert plane.Planned_DepartureRunway_ID == 1

def test_set_status():
    plane = Plane(id=3, size="Large")
    plane.Set_Status("Landing")
    assert plane.Current_Status == "Landing"

def test_get_index_landing_runway():
    plane = Plane(id=4, size="Large")
    plane.Planned_LandingRunway_ID = 1
    assert get_index_Landing_Runway(plane) == 0  # Runway 1 is index 0 and Large

def test_get_index_gate():
    plane = Plane(id=5, size="Small")
    plane.Planned_Gate_ID = 1
    assert get_index_Gate(plane) == 0  # Gate 1 is index 0
