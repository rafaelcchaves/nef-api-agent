import json
import methods
import requests
import sys

API_ROOT = "http://10.100.200.7:8000"
AF_ID = "af001"

def print_response(response):
    """Helper function to print response details."""
    print(f"   Status: {response.status_code}")
    try:
        # Try to parse and pretty-print JSON
        print("   Response Body (JSON):")
        print(json.dumps(response.json(), indent=4))
    except json.JSONDecodeError:
        # If not JSON, print raw text
        if response.text:
            print("   Response Body (Text):")
            print(response.text)
        else:
            print("   Response body is empty.")

print("--- 3gpp-traffic-influence API Client Example ---")

# --- 1. Create Subscription (POST) ---
new_sub_data = {
    "afServiceId": "Service1",
    "dnn": "internet",
    "snssai": {
        "sst": 1,
        "sd": "010203"
    },
    "anyUeInd": True,
    "notificationDestination": "http://af:8000/test123",
    "trafficFilters": [{
        "flowId": 1,
        "flowDescriptions": [
            "permit out ip from <server-cidr> to 10.60.0.0/16"
        ]
    }],
    "trafficRoutes": [
        {
            "dnai": "mec"
        }
    ]
}
print(f"\n1. Attempting to CREATE subscription for AF: {AF_ID}")
created_response = None
EXAMPLE_SUB_ID = None
try:
    created_response = methods.create_subscription(API_ROOT, AF_ID, new_sub_data)
    if created_response.ok:
        print("   Success!")
        print_response(created_response)
        try:
            EXAMPLE_SUB_ID = created_response.json()["self"].split("/")[-1]
        except (KeyError, json.JSONDecodeError):
            print("   Could not get subscription ID from create response. Halting tests.")
            sys.exit(1)
    else:
        print("   Request failed!")
        print_response(created_response)
        sys.exit(1)
except requests.exceptions.RequestException as e:
    print(f"   An exception occurred: {e}")
    sys.exit(1)

if not EXAMPLE_SUB_ID:
    print("Halting tests because subscription ID was not retrieved.")
    sys.exit(1)

# --- 2. Get All Subscriptions (GET) ---
print(f"\n2. Attempting to GET all subscriptions for AF: {AF_ID}")
try:
    all_subs_response = methods.get_all_subscriptions(API_ROOT, AF_ID)
    if all_subs_response.ok:
        print("   Success!")
        print_response(all_subs_response)
    else:
        print("   Request failed!")
        print_response(all_subs_response)
except requests.exceptions.RequestException as e:
    print(f"   An exception occurred: {e}")

# --- 3. Get Individual Subscription (GET) ---
print(f"\n3. Attempting to GET subscription: {EXAMPLE_SUB_ID}")
try:
    get_sub_response = methods.get_subscription(API_ROOT, AF_ID, EXAMPLE_SUB_ID)
    if get_sub_response.ok:
        print("   Success!")
        print_response(get_sub_response)
    else:
        print("   Request failed!")
        print_response(get_sub_response)
except requests.exceptions.RequestException as e:
    print(f"   An exception occurred: {e}")

# --- 4. Patch Subscription (PATCH) ---
patch_data = { "appReloInd": True }
print(f"\n4. Attempting to PATCH subscription: {EXAMPLE_SUB_ID}")
try:
    patch_response = methods.patch_subscription(API_ROOT, AF_ID, EXAMPLE_SUB_ID, patch_data)
    if patch_response.ok:
        print("   Success!")
        print_response(patch_response)
    else:
        print("   Request failed!")
        print_response(patch_response)
except requests.exceptions.RequestException as e:
    print(f"   An exception occurred: {e}")
    
# --- 5. Update/Replace Subscription (PUT) ---
full_update_data = new_sub_data.copy()
full_update_data["appReloInd"] = True

print(f"\n5. Attempting to PUT subscription: {EXAMPLE_SUB_ID}")
try:
    put_response = methods.update_subscription(API_ROOT, AF_ID, EXAMPLE_SUB_ID, full_update_data)
    if put_response.ok:
        print("   Success!")
        print_response(put_response)
    else:
        print("   Request failed!")
        print_response(put_response)
except requests.exceptions.RequestException as e:
    print(f"   An exception occurred: {e}")
    
# --- 6. Delete Subscription (DELETE) ---
print(f"\n6. Attempting to DELETE subscription: {EXAMPLE_SUB_ID}")
try:
    delete_response = methods.delete_subscription(API_ROOT, AF_ID, EXAMPLE_SUB_ID)
    if delete_response.ok:
        print("   Success!")
        print_response(delete_response)
    else:
        print("   Request failed!")
        print_response(delete_response)
except requests.exceptions.RequestException as e:
    print(f"   An exception occurred: {e}")

