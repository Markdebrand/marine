from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_arriving():
    # Attempt to hit the arriving endpoint for port 10830 (Antwerp usually or similar, need a valid port number).
    # Since we don't know the exact port_number without standard lookup, let's first list ports and pick one
    resp = client.get("/api/ports/search?unlocode=BEANR")
    if resp.status_code == 200:
        port_num = resp.json().get("port_number")
        print(f"Testing arriving vessels for port: {port_num}")
        resp_arr = client.get(f"/api/ports/{port_num}/arriving")
        if resp_arr.status_code == 200:
            print("Arriving vessels test PASSED:")
            data = resp_arr.json()
            print(f"Port: {data['port']}")
            print(f"Count: {data['count']}")
            if data['count'] > 0:
                print(f"Sample vessel: {data['vessels'][0]['ship_name']} to {data['vessels'][0]['destination']}")
        else:
            print(f"Arriving vessels test FAILED with {resp_arr.status_code}: {resp_arr.text}")
    else:
        print("Could not find port BEANR to test with.")

if __name__ == "__main__":
    test_arriving()
