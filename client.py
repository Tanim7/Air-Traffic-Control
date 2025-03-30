import grpc
import atc_pb2
import atc_pb2_grpc

def run():
    channel = grpc.insecure_channel("localhost:50051")
    stub = atc_pb2_grpc.AirTrafficControlStub(channel)

    response = stub.IncomingAirway(atc_pb2.AirwayRequest(
        aircraft_id="A123",
        altitude=3000,
        distance=15,
        airway="Arrival Airway 1"
    ))
    print(response)

    response = stub.DepartingAirway(atc_pb2.AirwayRequest(
        aircraft_id="B456",
        altitude=5000,
        distance=20,
        airway="Departure Airway 1"
    ))
    print(response)

    response = stub.GateAssignment(atc_pb2.GateRequest(
        aircraft_id="C789",
        duration=45
    ))
    print(response)

    response = stub.LandingRunway(atc_pb2.RunwayRequest(
        aircraft_id="C789",
        duration=2,
        runway="Arrival Runway 1"
    ))
    print(response)

    response = stub.DepartingRunway(atc_pb2.RunwayRequest(
        aircraft_id="E202",
        duration=1,
        runway="Runway 1"
    ))
    print(response)

    response = stub.AssignAircraft(atc_pb2.AssignAircraftRequest(
        aircraft_id="G404",
        runway="Runway 1",
        gate="Gate A3",
        airspace="Sector B"
    ))
    print(response)

    response = stub.ReleaseRunways(atc_pb2.Empty())
    print(response)

if __name__ == "__main__":
    run()