import argparse
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

parser = argparse.ArgumentParser(description="FastMCP Agent for NEF interactions.")
parser.add_argument(
    "-H",
    "--nef-url",
    type=str,
    default=API_ROOT,
    help="URL of the NEF (Network Exposure Function) API.",
)
args = parser.parse_args()
API_ROOT = args.nef_url

mcp = FastMCP(host='0.0.0.0')




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
    :param subscription_data: A dictionary containing the subscription details. The expected structure is provided in the system prompt when --rag flag is used.
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
    :param subscription_data: A dictionary containing the new subscription details. The expected structure is provided in the system prompt when --rag flag is used.
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



if __name__ == "__main__":
    mcp.run(transport="sse", port=8080)
