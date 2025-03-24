from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
import time

app = FastAPI()

# In-memory state tracking
runways: Dict[str, Dict] = {}
airways: Dict[str, Dict] = {}
gates: Dict[str, Dict] = {}
rings: Dict[str, Dict] = {}  # Holding patterns for planes waiting to land
planes: Dict[str, Dict] = {}  # Track all planes

class ReleaseRunwayData(BaseModel):
    runway_id: str

class AirwayData(BaseModel):
    airway_id: str
    runway_id: str

class PlaneData(BaseModel):
    plane_id: str
    altitude: int
    distance: int

class GateData(BaseModel):
    gate_id: str

class RunwayData(BaseModel):
    runway_id: str
    type: str  # "landing" or "departure"
    airway_id: str

@app.post("/register_gate")
def register_gate(data: GateData):
    gates[data.gate_id] = {"occupied": False}
    return {"status": "success", "message": f"Gate {data.gate_id} registered"}

@app.post("/register_runway")
def register_runway(data: RunwayData):
    runways[data.runway_id] = {"type": data.type, "airway_id": data.airway_id, "occupied": False}
    return {"status": "success", "message": f"Runway {data.runway_id} registered for {data.type}"}

@app.post("/register_airway")
def register_airway(data: AirwayData):
    airways[data.airway_id] = {"runway_id": data.runway_id, "occupied": False}
    return {"status": "success", "message": f"Airway {data.airway_id} registered for runway {data.runway_id}"}

@app.post("/register_plane")
def register_plane(data: PlaneData):
    # Attempt to assign the plane to a runway and airway
    for runway_id, runway_info in runways.items():
        if runway_info["type"] == "landing" and not runway_info["occupied"]:
            airway_id = runway_info["airway_id"]
            if not airways[airway_id]["occupied"]:
                # Assign the plane to the runway and airway
                runways[runway_id]["occupied"] = True
                airways[airway_id]["occupied"] = True
                planes[data.plane_id] = {"runway_id": runway_id, "airway_id": airway_id, "altitude": data.altitude, "distance": data.distance}
                return {
                    "status": "assigned",
                    "message": f"Plane {data.plane_id} assigned to runway {runway_id} and airway {airway_id}"
                }
    
    # If no runway or airway is available, add the plane to a ring (holding pattern)
    ring_id = f"ring-{len(rings) + 1}"
    rings[ring_id] = {"plane_id": data.plane_id, "altitude": 1000 * len(rings) + 1, "distance": data.distance}
    planes[data.plane_id] = {"ring_id": ring_id, "altitude": 1000 * len(rings) + 1, "distance": data.distance}
    return {"status": "waiting", "message": f"Plane {data.plane_id} added to ring {ring_id} with altitude {1000 * len(rings)} ft"}

@app.post("/release_runway")
def release_runway(data: ReleaseRunwayData):
    runway_id = data.runway_id
    if runway_id in runways:
        runways[runway_id]["occupied"] = False
        airway_id = runways[runway_id]["airway_id"]
        airways[airway_id]["occupied"] = False

        # Check if there are any planes in the holding pattern and assign them to the runway
        for ring_id, ring_info in rings.items():
            plane_id = ring_info["plane_id"]
            response = register_plane(PlaneData(plane_id=plane_id, altitude=ring_info["altitude"], distance=ring_info["distance"]))
            if response["status"] == "assigned":
                del rings[ring_id]
                break

        return {"status": "success", "message": f"Runway {runway_id} and airway {airway_id} released"}
    return {"status": "error", "message": f"Runway {runway_id} not found"}

@app.post("/assign_gate")
def assign_gate(plane_id: str):
    for gate_id, gate_info in gates.items():
        if not gate_info["occupied"]:
            gates[gate_id]["occupied"] = True
            return {"status": "assigned", "message": f"Plane {plane_id} assigned to gate {gate_id}"}
    return {"status": "error", "message": "No gates available"}

@app.post("/status")
def get_status():
    return {"runways": runways, "airways": airways, "gates": gates, "rings": rings, "planes": planes}