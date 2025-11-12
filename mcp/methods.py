import requests

def get_all_subscriptions(api_root, af_id):
    """
    GET /{afId}/subscriptions
    Reads all active subscriptions for the AF.
    """
    url = f"{api_root}/3gpp-traffic-influence/v1/{af_id}/subscriptions"
    headers = {"Accept": "application/json"}
    return requests.get(url, headers=headers)

def create_subscription(api_root, af_id, subscription_data):
    """
    POST /{afId}/subscriptions
    Creates a new subscription resource.
    """
    url = f"{api_root}/3gpp-traffic-influence/v1/{af_id}/subscriptions"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    return requests.post(url, headers=headers, json=subscription_data)

def get_subscription(api_root, af_id, subscription_id):
    """
    GET /{afId}/subscriptions/{subscriptionId}
    Reads an active subscription.
    """
    url = f"{api_root}/3gpp-traffic-influence/v1/{af_id}/subscriptions/{subscription_id}"
    headers = {"Accept": "application/json"}
    return requests.get(url, headers=headers)

def update_subscription(api_root, af_id, subscription_id, subscription_data):
    """
    PUT /{afId}/subscriptions/{subscriptionId}
    Updates/replaces an existing subscription resource.
    """
    url = f"{api_root}/3gpp-traffic-influence/v1/{af_id}/subscriptions/{subscription_id}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    return requests.put(url, headers=headers, json=subscription_data)

def patch_subscription(api_root, af_id, subscription_id, patch_data):
    """
    PATCH /{afId}/subscriptions/{subscriptionId}
    Updates parts of an existing subscription resource.
    """
    url = f"{api_root}/3gpp-traffic-influence/v1/{af_id}/subscriptions/{subscription_id}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/merge-patch+json"
    }
    return requests.patch(url, headers=headers, json=patch_data)

def delete_subscription(api_root, af_id, subscription_id):
    """
    DELETE /{afId}/subscriptions/{subscriptionId}
    Deletes an existing subscription.
    """
    url = f"{api_root}/3gpp-traffic-influence/v1/{af_id}/subscriptions/{subscription_id}"
    headers = {"Accept": "application/json"}
    return requests.delete(url, headers=headers)
