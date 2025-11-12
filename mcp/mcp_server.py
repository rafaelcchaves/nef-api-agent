from fastmcp import FastMCP
from methods import ( 
    get_all_subscriptions,
    create_subscription,
    get_subscription,
    update_subscription,
    patch_subscription,
    delete_subscription,
)

API_ROOT = "http://10.100.200.6:8000"

mcp = FastMCP()

@mcp.tool()
def list_subscriptions(af_id: str):
    """
    Retrieves a list of all active Traffic Influence subscriptions for a given Application Function (AF).

    :param af_id: The identifier of the Application Function.
    :return: A JSON object containing a list of subscriptions.
    """
    response = get_all_subscriptions(API_ROOT, af_id)
    return response.json()

@mcp.tool()
def add_subscription(
    af_id: str,
    subscription_data: dict,
):
    """
    Creates a new Traffic Influence subscription for a given Application Function (AF).

    :param af_id: The identifier of the Application Function.
    :param subscription_data: A dictionary containing the subscription details. Use the 'subscription_schema' resource to see the expected structure.
    :return: A JSON object representing the newly created subscription.
    """
    response = create_subscription(API_ROOT, af_id, subscription_data)
    return response.json()

@mcp.tool()
def get_subscription_details(af_id: str, subscription_id: str):
    """
    Reads the details of a specific Traffic Influence subscription.

    :param af_id: The identifier of the Application Function.
    :param subscription_id: The identifier of the subscription to retrieve.
    :return: A JSON object containing the subscription details.
    """
    response = get_subscription(API_ROOT, af_id, subscription_id)
    return response.json()

@mcp.tool()
def update_full_subscription(
    af_id: str,
    subscription_id: str,
    subscription_data: dict,
):
    """
    Fully updates/replaces an existing Traffic Influence subscription.

    :param af_id: The identifier of the Application Function.
    :param subscription_id: The identifier of the subscription to update.
    :param subscription_data: A dictionary containing the new subscription details. Use the 'subscription_schema' resource to see the expected structure.
    :return: A JSON object representing the updated subscription.
    """
    response = update_subscription(API_ROOT, af_id, subscription_id, subscription_data)
    return response.json()

@mcp.tool()
def update_partial_subscription(
    af_id: str, subscription_id: str, patch_data: dict
):
    """
    Partially updates an existing Traffic Influence subscription.

    :param af_id: The identifier of the Application Function.
    :param subscription_id: The identifier of the subscription to update.
    :param patch_data: A dictionary containing the fields to update.
    :return: A JSON object representing the updated subscription.
    """
    response = patch_subscription(API_ROOT, af_id, subscription_id, patch_data)
    return response.json()

@mcp.tool()
def remove_subscription(af_id: str, subscription_id: str):
    """
    Deletes a specific Traffic Influence subscription.

    :param af_id: The identifier of the Application Function.
    :param subscription_id: The identifier of the subscription to delete.
    :return: A confirmation message if successful, otherwise a JSON error object.
    """
    response = delete_subscription(API_ROOT, af_id, subscription_id)
    if response.status_code == 204:
        return {"status": "Subscription deleted successfully"}
    return response.json()

@mcp.resource("data://subscription_schema")
def subscription_schema():
    """
    Provides the JSON schema for a 3GPP Traffic Influence subscription.
    This schema defines the structure and data types required when creating or updating a subscription.
    Use this to ensure the 'subscription_data' dictionary is correctly formatted.
    """
    return {
        "type": "object",
        "properties": {
            "afServiceId": {"type": "string", "description": "Identifier of the AF service"},
            "dnn": {"type": "string", "description": "Data Network Name"},
            "snssai": {
                "type": "object",
                "properties": {
                    "sst": {"type": "integer", "description": "Slice/Service Type"},
                    "sd": {"type": "string", "description": "Slice Differentiator"}
                },
                "required": ["sst", "sd"]
            },
            "anyUeInd": {"type": "boolean", "description": "Indicates whether the subscription applies to any UE"},
            "notificationDestination": {"type": "string", "description": "URL to send notifications"},
            "trafficFilters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "flowId": {"type": "integer", "description": "Flow identifier"},
                        "flowDescriptions": {
                            "type": "array",
                            "items": {"type": "string", "description": "Description of the traffic flow (e.g., IP filter)"}
                        }
                    },
                    "required": ["flowId", "flowDescriptions"]
                }
            },
            "trafficRoutes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "dnai": {"type": "string", "description": "Data Network Access Identifier"}
                    },
                    "required": ["dnai"]
                }
            },
            "appReloInd": {"type": "boolean", "description": "Indicates whether application relocation is allowed (for PATCH/PUT)"}
        },
        "required": [
            "afServiceId",
            "dnn",
            "snssai",
            "anyUeInd",
            "notificationDestination",
            "trafficFilters",
            "trafficRoutes"
        ]
    }

if __name__ == "__main__":
    mcp.run(transport="sse", port=8080)
