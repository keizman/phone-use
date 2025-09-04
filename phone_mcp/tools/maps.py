try:
    import requests
    import json
    import os
    import aiohttp
    from typing import Optional, Dict, Any, List, Union

    # Default API key can be set through environment variable
    DEFAULT_API_KEY = os.environ.get("AMAP_MAPS_API_KEY")

    # Check if there is a valid API key
    HAS_VALID_API_KEY = DEFAULT_API_KEY is not None and DEFAULT_API_KEY.strip() != ""
except ImportError:
    import json
    import os
    from typing import Optional, Dict, Any, List, Union
    
    # Mark as not available
    HAS_VALID_API_KEY = False
    DEFAULT_API_KEY = None


async def get_phone_numbers_from_poi(
    location: str, keywords: Optional[str] = None, radius: Optional[str] = "1000"
) -> str:
    """
    Retrieve phone numbers and information from Points of Interest (POIs) around a specified location.

    This function uses the AMap API to find nearby businesses and points of interest, primarily to obtain
    their contact phone numbers. It searches around a given coordinate location, allowing keyword filtering
    and custom search radius. The results include business names, addresses, phone numbers, and additional details.

    Args:
        location (str): Central coordinate point in format: "longitude,latitude"
        keywords (str, optional): Search keywords to filter results, like "restaurant", "hotel", etc.
        radius (str, optional): Search radius in meters. Default is 1000 meters.

    Returns:
        str: JSON string containing POI information with phone numbers or error details if the search fails
    """
    if not HAS_VALID_API_KEY:
        return json.dumps(
            {
                "error": "API key not configured. Please set the AMAP_MAPS_API_KEY environment variable."
            },
            ensure_ascii=False,
        )

    url = "https://restapi.amap.com/v3/place/around"
    params = {
        "key": DEFAULT_API_KEY,
        "location": location,
        "radius": radius,  # Default radius is now set in the parameter
    }

    if keywords:
        params["keywords"] = keywords

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()

                if data.get("status") == "1" and data.get("pois"):
                    return json.dumps(data, ensure_ascii=False)
                else:
                    return json.dumps(
                        {"error": "POI search failed", "details": data},
                        ensure_ascii=False,
                    )
    except Exception as e:
        return json.dumps({"error": f"Request failed: {str(e)}"}, ensure_ascii=False)
