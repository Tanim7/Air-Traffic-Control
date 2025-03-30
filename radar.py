import requests
import random
import time

SERVER_URL = "http://127.0.0.1:8000/spawn_plane/"

def generate_random_plane():
    plane_id = random.randint(1000, 9999)
    size = random.choice(["Small", "Large"])
    return {"plane_id": plane_id, "size": size}

if __name__ == "__main__":
    print("[RADAR] Starting radar simulation...")
    while True:
        plane_data = generate_random_plane()
        print(f"[RADAR] Sending plane {plane_data['plane_id']} ({plane_data['size']})")
        try:
            response = requests.post(SERVER_URL, json=plane_data)
            print("[RADAR] Server response:", response.json())
        except Exception as e:
            print("[RADAR] Error connecting to server:", e)

        time.sleep(random.randint(5, 15))  # spawn a new plane every 5–15 seconds