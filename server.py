import grpc
from concurrent import futures
import time
import atc_pb2
import atc_pb2_grpc

# Runway & airway status
runway_status = {
    "Arrival Runway 1": None,
    "Arrival Runway 2": None,
    "Departure Runway 1": None,
    "Departure Runway 2": None
}

airway_status = {
    "Arrival Airway 1": [],
    "Arrival Airway 2": [],
    "Departure Airway 1": [],
    "Departure Airway 2": []
}

class ATCService(atc_pb2_grpc.AirTrafficControlServicer):
    def IncomingAirway(self, request, context):
        if request.airway not in airway_status:
            return atc_pb2.Response(status="error", message=f"Invalid airway {request.airway}")

        airway_status[request.airway].append(request.aircraft_id)
        return atc_pb2.Response(status="received", message=f"{request.aircraft_id} registered in {request.airway}")

    def DepartingAirway(self, request, context):
        if request.airway not in airway_status:
            return atc_pb2.Response(status="error", message=f"Invalid airway {request.airway}")

        airway_status[request.airway].append(request.aircraft_id)
        return atc_pb2.Response(status="received", message=f"{request.aircraft_id} departing via {request.airway}")

    def LandingRunway(self, request, context):
        if request.runway not in runway_status:
            return atc_pb2.Response(status="error", message=f"Invalid runway {request.runway}")
        
        if runway_status[request.runway]:
            return atc_pb2.Response(status="blocked", message=f"Runway {request.runway} is occupied")

        runway_status[request.runway] = {"aircraft_id": request.aircraft_id, "release_time": time.time() + request.duration * 60}
        return atc_pb2.Response(status="landing", message=f"{request.aircraft_id} assigned to {request.runway}")

    def DepartingRunway(self, request, context):
        if request.runway not in runway_status:
            return atc_pb2.Response(status="error", message=f"Invalid runway {request.runway}")

        runway_status[request.runway] = {"aircraft_id": request.aircraft_id, "release_time": time.time() + request.duration * 60}
        return atc_pb2.Response(status="departure", message=f"{request.aircraft_id} departing from {request.runway}")

    def GateAssignment(self, request, context):
        return atc_pb2.Response(status="assigned", message=f"{request.aircraft_id} assigned gate for {request.duration} minutes")

    def AssignAircraft(self, request, context):
        return atc_pb2.Response(status="assigned", message=f"{request.aircraft_id} assigned to {request.runway}, {request.gate}")

    def ReleaseRunways(self, request, context):
        now = time.time()
        for rwy in runway_status:
            if runway_status[rwy] and runway_status[rwy]["release_time"] <= now:
                runway_status[rwy] = None
        return atc_pb2.Response(status="updated", message="Expired runways released")

# Start gRPC server
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    atc_pb2_grpc.add_AirTrafficControlServicer_to_server(ATCService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC server running on port 50051...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
