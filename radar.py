import threading
import time
import requests
import pika
import random

SERVER_URL = "http://127.0.0.1:8000"

def send_request(endpoint, data):
    url = f"{SERVER_URL}/{endpoint}"
    print(f"Sending request to {url} with data: {data}")  # Debug print
    response = requests.post(url, json=data)
    print(f"Response from {url}: {response.json()}")  # Debug print
    return response.json()

def monitor_runways():
    while True:
        time.sleep(5)  # Check every 5 seconds
        print("Checking runways for release...")  # Debug print
        for runway_id in ["runway-1", "runway-2"]:
            print(f"Attempting to release runway: {runway_id}")  # Debug print
            response = send_request("release_runway", {"runway_id": runway_id})
            print("Runway status updated:", response)

def process_holding():
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue="holding_pattern")

    def callback(ch, method, properties, body):
        plane_id = body.decode()
        print(f"Plane {plane_id} cleared for landing.")  # Debug print
        
        # Attempt to assign the plane to a runway
        print(f"Attempting to assign plane {plane_id} to a runway...")  # Debug print
        response = send_request("register_plane", {"plane_id": plane_id, "altitude": 0, "distance": 0})
        print(response)

        # If the plane cannot be assigned, log the issue and do not re-add it to the queue
        if response.get("status") == "waiting":
            print(f"Plane {plane_id} could not be assigned to a runway. Skipping.")  # Debug print

    print("Waiting for holding pattern planes...")
    channel.basic_consume(queue="holding_pattern", on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

def spawn_plane(plane_id):
    altitude = random.randint(2000, 10000)
    distance = 20  # All planes start 20 km away
    
    print(f"Radar detected plane {plane_id} at {altitude} ft, {distance} km away.")  # Debug print
    
    # Register the plane
    print(f"Attempting to register plane {plane_id}...")  # Debug print
    response = send_request("register_plane", {
        "plane_id": plane_id,
        "altitude": altitude,
        "distance": distance
    })
    print(response)

    # If the plane is added to a ring (holding pattern), send it to RabbitMQ
    if response.get("status") == "waiting":
        print(f"Plane {plane_id} added to holding pattern.")  # Debug print
        add_to_holding(plane_id)

def add_to_holding(plane_id):
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue="holding_pattern")
    print(f"Adding plane {plane_id} to RabbitMQ holding pattern queue...")  # Debug print
    channel.basic_publish(exchange="", routing_key="holding_pattern", body=plane_id.encode())
    connection.close()
    print(f"Plane {plane_id} added to holding pattern.")  # Debug print

def simulate_plane_movement():
    while True:
        time.sleep(5)
        print("Simulating plane movement...")  # Debug print
        response = send_request("status", {})
        planes = response.get("planes", {})
        print(f"Current planes: {planes}")  # Debug print
        for plane_id, plane_info in planes.items():
            if "runway_id" in plane_info:
                plane_info["distance"] -= 2
                print(f"Update: {plane_id} at {plane_info['altitude']} ft, {plane_info['distance']} km away, approaching the airport")
            elif "ring_id" in plane_info:
                plane_info["distance"] -= 2
                print(f"Update: {plane_id} at {plane_info['altitude']} ft, {plane_info['distance']} km away, approaching ring {plane_info['ring_id']} at {plane_info['altitude']} ft.")
                if plane_info["distance"] <= 0:
                    print(f"Plane {plane_id} has reached the airport. Attempting to assign to a runway...")
                    response = send_request("register_plane", {"plane_id": plane_id, "altitude": plane_info["altitude"], "distance": 0})
                    print(response)

if __name__ == "__main__":
    # Preassign runways and airways
    print("Preassigning runways and airways...")  # Debug print
    send_request("register_runway", {"runway_id": "runway-1", "type": "landing", "airway_id": "airway-1"})
    send_request("register_runway", {"runway_id": "runway-2", "type": "departure", "airway_id": "airway-2"})
    send_request("register_airway", {"airway_id": "airway-1", "runway_id": "runway-1"})
    send_request("register_airway", {"airway_id": "airway-2", "runway_id": "runway-2"})

    # Preassign gates
    print("Preassigning gates...")  # Debug print
    for i in range(10):
        send_request("register_gate", {"gate_id": f"gate-{i}"})

    # Start the runway monitor in a separate thread
    print("Starting runway monitor thread...")  # Debug print
    threading.Thread(target=monitor_runways, daemon=True).start()
    
    # Start processing the holding pattern (RabbitMQ queue)
    print("Starting holding pattern processor thread...")  # Debug print
    threading.Thread(target=process_holding, daemon=True).start()

    # Start simulating plane movement
    print("Starting plane movement simulation thread...")  # Debug print
    threading.Thread(target=simulate_plane_movement, daemon=True).start()

    # Simulate incoming planes
    print("Simulating incoming planes...")  # Debug print
    for i in range(10):
        spawn_plane(f"Flight-{1000 + i}")
        time.sleep(3)  # Space out plane arrivals

    # Keep the main thread alive
    print("Main thread running...")  # Debug print
    while True:
        time.sleep(1)