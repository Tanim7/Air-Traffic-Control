import threading
import time
import random
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

ActivePlanes = {}

# Goes in server
class Plane:
    def __init__(self, id: int, size: str): 
        self.Plane_ID = id  # Id of the plane
        self.Size = size
    def Set_Flight_Plan(self, LandingRunwayID: int, GateID: int, GateDelay: int, DepartureRunwayID: int):
        self.Planned_LandingRunway_ID = LandingRunwayID  # The assigned landing runway that the plane should use
        self.Planned_Gate_ID = GateID  # The assigned gate for the plane to use after landing
        self.Planned_Gate_Delay = GateDelay  # Time at gate for refueling, boarding, etc.
        self.Planned_DepartureRunway_ID = DepartureRunwayID  # The assigned departure runway
    def Set_Status(self, status: str):
        self.Current_Status = status  # Ex/ "Landing", "At_Gate", etc.
    def Set_Ring(self, ring: int):
        self.Planned_RingID = ring

# Goes in server
class Runway:
    def __init__(self, id: int, size: str):
        self.Size = size
        self.Runway_ID = id
        self.Available = True
    def Change_Available(self):
        self.Available = True
    def Change_Unavailable(self):
        self.Available = False

class PatrolRing:
    def __init__(self, id: int, altitude: int):
        self.Altitude = altitude
        self.Ring_ID = id
        self.Available = True
    def Change_Available(self):
        self.Available = True
    def Change_Unavailable(self):
        self.Available = False

class Gate:
    def __init__(self, id: int):
        self.Ring_ID = id
        self.Available = True
    def Change_Available(self):
        self.Available = True
    def Change_Unavailable(self):
        self.Available = False

# These are the runways
Runways = [
    Runway(1, "Large"),
    Runway(2, "Large"),
    Runway(3, "Small")
]

# Rings where planes hold in air
Patrol_Rings = [
    PatrolRing(1, 750),
    PatrolRing(2, 1000),
    PatrolRing(3, 1250)
]

# Airport gates
Gates = [
    Gate(1),
    Gate(2),
    Gate(3)
]

# The client should provide the information for the departing airways
# Patrol queue
Patrolling_Planes = []
Waiting_For_Gate_Planes = []
Taxi_Planes = []

# Goes in server, need to do one of these for each type of place that the plane can be at, so airways, rings and gates
def get_index_Landing_Runway(PlaneX: Plane):
    for i in range(len(Runways)):
        if Runways[i].Runway_ID == PlaneX.Planned_LandingRunway_ID:
            if Runways[i].Size == PlaneX.Size:
                return i
            else:
                return 10000
    return 10000

def get_index_Departing_Runway(PlaneX: Plane):
    for i in range(len(Runways)):
        if Runways[i].Runway_ID == PlaneX.Planned_DepartureRunway_ID:
            if Runways[i].Size == PlaneX.Size:
                return i
            else:
                return 10000
    return 10000

def get_index_Gate(PlaneX: Plane):
    for i in range(len(Gates)):
        if Gates[i].Ring_ID == PlaneX.Planned_Gate_ID:
            return i
    return 10000

# Goes in server, contacts client for where plane should go, offer option to generate a new approach airway
def find_available_runway(PlaneX: Plane):
    for i in range(len(Runways)):
        if Runways[i].Available and Runways[i].Size == PlaneX.Size:
            return i
    return 10000

def find_available_gate():
    for i in range(len(Gates)):
        if Gates[i].Available:
            return i
    return 10000

def find_landing_order(plane_ID):
    for i in range(len(Patrolling_Planes)):
        if Patrolling_Planes[i].Plane_ID == plane_ID:
            return i
    return 10000

def find_gate_awaiting_order(plane_ID):
    for i in range(len(Waiting_For_Gate_Planes)):
        if Waiting_For_Gate_Planes[i].Plane_ID == plane_ID:
            return i
    return 10000

def find_taxi_order(plane_ID):
    for i in range(len(Taxi_Planes)):
        if Taxi_Planes[i].Plane_ID == plane_ID:
            return i
    return 10000

# Method goes in server, is responsible for keeping track of a plane, a thread of this method is spawned for each plane
def Track_Plane(PlaneX: Plane):
    # Fill out a random flight plan (since Radar sends only size & ID)
    PlaneX.Set_Flight_Plan(
        LandingRunwayID=random.choice([r.Runway_ID for r in Runways if r.Size == PlaneX.Size]),
        GateID=random.choice([g.Ring_ID for g in Gates]),
        GateDelay=random.randint(20, 40),  # Short for test purposes
        DepartureRunwayID=random.choice([r.Runway_ID for r in Runways if r.Size == PlaneX.Size])
    )

    print(f"[SERVER] Plane {PlaneX.Plane_ID} ({PlaneX.Size}) incoming → Landing: {PlaneX.Planned_LandingRunway_ID}, Gate: {PlaneX.Planned_Gate_ID}, Depart: {PlaneX.Planned_DepartureRunway_ID}")

    # Plane is trying to land
    index = get_index_Landing_Runway(PlaneX)
    if index != 10000 and Runways[index].Available:
        print(f"[SERVER] Plane {PlaneX.Plane_ID} cleared to land on Runway {Runways[index].Runway_ID}")
        Runways[index].Change_Unavailable()
        PlaneX.Set_Status("Landing")
        ActivePlanes[PlaneX.Plane_ID] = {
            "status": PlaneX.Current_Status,
            "landing_runway": PlaneX.Planned_LandingRunway_ID,
            "gate": PlaneX.Planned_Gate_ID,
            "departure_runway": PlaneX.Planned_DepartureRunway_ID,
            "size": PlaneX.Size
        }
        time.sleep(random.randint(6, 9))
    else:
        PlaneX.Set_Status("Patrolling")
        ActivePlanes[PlaneX.Plane_ID] = {
            "status": PlaneX.Current_Status,
            "landing_runway": PlaneX.Planned_LandingRunway_ID,
            "gate": PlaneX.Planned_Gate_ID,
            "departure_runway": PlaneX.Planned_DepartureRunway_ID,
            "size": PlaneX.Size
        }
        Patrolling_Planes.append(PlaneX)
        print(f"[SERVER] Plane {PlaneX.Plane_ID} is patrolling...")
        while PlaneX.Current_Status == "Patrolling":
            time.sleep(2)
            index = find_available_runway(PlaneX)
            if index != 10000 and find_landing_order(PlaneX.Plane_ID) == 0:
                print(f"[SERVER] Plane {PlaneX.Plane_ID} now cleared to land after holding")
                Runways[index].Change_Unavailable()
                PlaneX.Set_Status("Landing")
                ActivePlanes[PlaneX.Plane_ID] = {
                    "status": PlaneX.Current_Status,
                    "landing_runway": PlaneX.Planned_LandingRunway_ID,
                    "gate": PlaneX.Planned_Gate_ID,
                    "departure_runway": PlaneX.Planned_DepartureRunway_ID,
                    "size": PlaneX.Size
                }
                Patrolling_Planes.remove(PlaneX)
                time.sleep(random.randint(6, 9))

    Runways[index].Change_Available()
    print(f"[SERVER] Plane {PlaneX.Plane_ID} has landed.")

    # Plane is trying to acquire a gate
    PlaneX.Set_Status("Awaiting_Gate")
    ActivePlanes[PlaneX.Plane_ID] = {
        "status": PlaneX.Current_Status,
        "landing_runway": PlaneX.Planned_LandingRunway_ID,
        "gate": PlaneX.Planned_Gate_ID,
        "departure_runway": PlaneX.Planned_DepartureRunway_ID,
        "size": PlaneX.Size
    }

    indexGate = get_index_Gate(PlaneX)
    if indexGate != 10000 and Gates[indexGate].Available:
        print(f"[SERVER] Plane {PlaneX.Plane_ID} taxiing to Gate {Gates[indexGate].Ring_ID}")
        Gates[indexGate].Change_Unavailable()
        PlaneX.Set_Status("At_Gate")
        ActivePlanes[PlaneX.Plane_ID] = {
            "status": PlaneX.Current_Status,
            "landing_runway": PlaneX.Planned_LandingRunway_ID,
            "gate": PlaneX.Planned_Gate_ID,
            "departure_runway": PlaneX.Planned_DepartureRunway_ID,
            "size": PlaneX.Size
        }

        time.sleep(PlaneX.Planned_Gate_Delay)
    else:
        Waiting_For_Gate_Planes.append(PlaneX)
        print(f"[SERVER] Plane {PlaneX.Plane_ID} is waiting for a gate.")
        while PlaneX.Current_Status == "Awaiting_Gate":
            time.sleep(2)
            indexGate = find_available_gate()
            if indexGate != 10000 and find_gate_awaiting_order(PlaneX.Plane_ID) == 0:
                PlaneX.Planned_Gate_ID = Gates[indexGate].Ring_ID
                Gates[indexGate].Change_Unavailable()
                Waiting_For_Gate_Planes.remove(PlaneX)
                PlaneX.Set_Status("At_Gate")
                ActivePlanes[PlaneX.Plane_ID] = {
                    "status": PlaneX.Current_Status,
                    "landing_runway": PlaneX.Planned_LandingRunway_ID,
                    "gate": PlaneX.Planned_Gate_ID,
                    "departure_runway": PlaneX.Planned_DepartureRunway_ID,
                    "size": PlaneX.Size
                }
                print(f"[SERVER] Plane {PlaneX.Plane_ID} assigned to Gate {PlaneX.Planned_Gate_ID}")
                time.sleep(PlaneX.Planned_Gate_Delay)

    Gates[indexGate].Change_Available()
    print(f"[SERVER] Plane {PlaneX.Plane_ID} done at gate.")

    # Departing
    PlaneX.Set_Status("Departing")
    ActivePlanes[PlaneX.Plane_ID] = {
        "status": PlaneX.Current_Status,
        "landing_runway": PlaneX.Planned_LandingRunway_ID,
        "gate": PlaneX.Planned_Gate_ID,
        "departure_runway": PlaneX.Planned_DepartureRunway_ID,
        "size": PlaneX.Size
    }
    indexDepartingRunway = get_index_Departing_Runway(PlaneX)
    if indexDepartingRunway != 10000 and Runways[indexDepartingRunway].Available and len(Patrolling_Planes) == 0:
        print(f"[SERVER] Plane {PlaneX.Plane_ID} cleared to depart on Runway {Runways[indexDepartingRunway].Runway_ID}")
        Runways[indexDepartingRunway].Change_Unavailable()
        time.sleep(random.randint(6, 9))
        PlaneX.Set_Status("Departed")
        ActivePlanes[PlaneX.Plane_ID] = {
            "status": PlaneX.Current_Status,
            "landing_runway": PlaneX.Planned_LandingRunway_ID,
            "gate": PlaneX.Planned_Gate_ID,
            "departure_runway": PlaneX.Planned_DepartureRunway_ID,
            "size": PlaneX.Size
        }

    else:
        Taxi_Planes.append(PlaneX)
        print(f"[SERVER] Plane {PlaneX.Plane_ID} waiting to depart...")
        while PlaneX.Current_Status == "Departing":
            time.sleep(2)
            indexDepartingRunway = find_available_runway(PlaneX)
            if indexDepartingRunway != 10000 and find_taxi_order(PlaneX.Plane_ID) == 0 and len(Patrolling_Planes) == 0:
                print(f"[SERVER] Plane {PlaneX.Plane_ID} departing after wait")
                Runways[indexDepartingRunway].Change_Unavailable()
                Taxi_Planes.remove(PlaneX)
                time.sleep(random.randint(6, 9))
                PlaneX.Set_Status("Departed")
                ActivePlanes[PlaneX.Plane_ID] = {
                    "status": PlaneX.Current_Status,
                    "landing_runway": PlaneX.Planned_LandingRunway_ID,
                    "gate": PlaneX.Planned_Gate_ID,
                    "departure_runway": PlaneX.Planned_DepartureRunway_ID,
                    "size": PlaneX.Size
                }

    Runways[indexDepartingRunway].Change_Available()
    print(f"[SERVER] Plane {PlaneX.Plane_ID} has departed.")

# Opens connections with client after receiving a partially filled-in Plane Object (say just size from radar)
def New_Plane(PlaneX: Plane):
    Track_Plane(PlaneX)  # Plane travels throughout the airport

# FastAPI setup for communication with Radar
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or replace with ["http://localhost"] if you want stricter rules
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlaneRequest(BaseModel):
    plane_id: int
    size: str

@app.post("/spawn_plane/")
def spawn_plane(data: PlaneRequest):
    plane = Plane(data.plane_id, data.size)
    print(f"[SERVER] Received plane {plane.Plane_ID} ({plane.Size}) from radar.")
    thread = threading.Thread(target=New_Plane, args=(plane,))
    thread.start()
    return {"status": f"Tracking started for plane {plane.Plane_ID}"}

@app.get("/planes/")
def get_active_planes():
    return ActivePlanes

@app.get("/resources/")
def get_resources():
    # GATE STATUS
    gate_data = []
    for gate in Gates:
        plane_id = None
        for plane_id_key, plane in ActivePlanes.items():
            if plane["gate"] == gate.Ring_ID and plane["status"] == "At_Gate":
                plane_id = plane_id_key
                break
        gate_data.append({
            "gate_id": gate.Ring_ID,
            "available": gate.Available,
            "plane_id": plane_id
        })

    # RUNWAY STATUS
    runway_data = []
    for runway in Runways:
        plane_id = None
        for plane_id_key, plane in ActivePlanes.items():
            if (
                (plane["landing_runway"] == runway.Runway_ID or plane["departure_runway"] == runway.Runway_ID)
                and plane["status"] in ["Landing", "Departing"]
            ):
                plane_id = plane_id_key
                break
        runway_data.append({
            "runway_id": runway.Runway_ID,
            "size": runway.Size,
            "available": runway.Available,
            "plane_id": plane_id
        })

    return {"gates": gate_data, "runways": runway_data}

# Goes in server
if __name__ == "__main__":
    # Run FastAPI server for Radar client to connect to
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)