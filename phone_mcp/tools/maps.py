import requests
import json
import os
import aiohttp
from typing import Optional, Dict, Any, List, Union

# Default API key can be set through environment variable
DEFAULT_API_KEY = os.environ.get("AMAP_MAPS_API_KEY")

# Check if there is a valid API key
HAS_VALID_API_KEY = DEFAULT_API_KEY is not None and DEFAULT_API_KEY.strip() != ""

async def get_poi_info_by_location(location: str, keywords: Optional[str] = None, radius: Optional[str] = "1000") -> str:
    """
    Search for Points of Interest (POIs) around a specified location and get their detailed information including phone numbers.
    
    This function uses the AMap API to find POIs near a given coordinate location. It allows filtering by keywords
    and setting a custom search radius. The returned data includes detailed POI information such as names, addresses,
    phone numbers, business hours, and more.
    
    Args:
        location (str): Central coordinate point in format: "longitude,latitude"
        keywords (str, optional): Search keywords to filter results, like "restaurant", "hotel", etc.
        radius (str, optional): Search radius in meters. Default is 1000 meters.
    
    Returns:
        str: JSON string containing POI information or error details if the search fails
    """
    if not HAS_VALID_API_KEY:
        return json.dumps({"error": "API key not configured. Please set the AMAP_MAPS_API_KEY environment variable."}, ensure_ascii=False)
    
    url = "https://restapi.amap.com/v3/place/around"
    params = {
        "key": DEFAULT_API_KEY,
        "location": location,
        "radius": radius  # Default radius is now set in the parameter
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
                    return json.dumps({"error": "POI search failed", "details": data}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Request failed: {str(e)}"}, ensure_ascii=False) 