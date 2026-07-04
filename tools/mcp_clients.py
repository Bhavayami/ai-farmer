import time
import requests
from typing import Dict, Any, List, Optional
from config import settings
from logger import logger
from database import db_manager, CacheRepository
from exceptions import MCPException

class MCPClient:
    """
    Client for calling external services and simulating MCP tools
    with caching, timeouts, retries, and offline mock fallbacks.
    """
    
    @staticmethod
    def _get_cache(key: str) -> Optional[Dict[str, Any]]:
        db = next(db_manager.get_db())
        try:
            return CacheRepository.get(db, key)
        except Exception as e:
            logger.error(f"Cache read error for key {key}: {e}")
            return None

    @staticmethod
    def _set_cache(key: str, value: Dict[str, Any], ttl_seconds: int):
        db = next(db_manager.get_db())
        try:
            CacheRepository.set(db, key, value, ttl_seconds)
        except Exception as e:
            logger.error(f"Cache write error for key {key}: {e}")

    @classmethod
    def get_weather_data(cls, lat: float, lon: float) -> Dict[str, Any]:
        """
        Fetches 7-day weather forecast. Caches results for 1 hour (3600s).
        """
        cache_key = f"weather_{lat}_{lon}"
        cached = cls._get_cache(cache_key)
        if cached:
            logger.info(f"Serving cached weather data for {lat}, {lon}")
            return cached

        # Attempt to call actual weather API if key is present
        if settings.weather_api_key and settings.weather_api_key != "your_weather_api_key_here":
            url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={settings.weather_api_key}&units=metric"
            for attempt in range(3):
                try:
                    response = requests.get(url, timeout=5)
                    response.raise_for_status()
                    data = response.json()
                    cls._set_cache(cache_key, data, 3600)
                    return data
                except Exception as e:
                    logger.warning(f"Weather API attempt {attempt+1} failed: {e}")
                    time.sleep(1)

        # Fallback to high-quality localized mock weather data
        logger.info(f"Using mock weather fallback for {lat}, {lon}")
        mock_weather = {
            "current": {
                "temp": 30.5,
                "humidity": 65,
                "wind_speed": 12.5,
                "weather": [{"description": "scattered clouds", "main": "Clouds"}]
            },
            "daily": [
                {"dt": int(time.time()), "temp": {"min": 24, "max": 33}, "humidity": 60, "weather": [{"main": "Clear", "description": "clear sky"}], "pop": 0.1},
                {"dt": int(time.time()) + 86400, "temp": {"min": 23, "max": 31}, "humidity": 72, "weather": [{"main": "Rain", "description": "light rain"}], "pop": 0.6},
                {"dt": int(time.time()) + 172800, "temp": {"min": 22, "max": 29}, "humidity": 80, "weather": [{"main": "Rain", "description": "moderate rain"}], "pop": 0.95},
                {"dt": int(time.time()) + 259200, "temp": {"min": 23, "max": 32}, "humidity": 75, "weather": [{"main": "Clouds", "description": "broken clouds"}], "pop": 0.4},
                {"dt": int(time.time()) + 345600, "temp": {"min": 24, "max": 34}, "humidity": 65, "weather": [{"main": "Clear", "description": "sunny"}], "pop": 0.05},
                {"dt": int(time.time()) + 432000, "temp": {"min": 25, "max": 35}, "humidity": 58, "weather": [{"main": "Clear", "description": "sunny"}], "pop": 0.0},
                {"dt": int(time.time()) + 518400, "temp": {"min": 25, "max": 35}, "humidity": 55, "weather": [{"main": "Clear", "description": "sunny"}], "pop": 0.0}
            ]
        }
        cls._set_cache(cache_key, mock_weather, 3600)
        return mock_weather

    @classmethod
    def get_market_prices(cls, crop: str, region: str) -> Dict[str, Any]:
        """
        Fetches commodity price trends for crops in the region. Caches for 4 hours (14400s).
        """
        cache_key = f"market_{crop.lower()}_{region.lower().replace(' ', '_')}"
        cached = cls._get_cache(cache_key)
        if cached:
            logger.info(f"Serving cached market prices for {crop} in {region}")
            return cached

        # Simulated or external API call (e.g., Data.gov.in / Agmarknet API mock)
        logger.info(f"Fetching market prices for {crop} in {region}")
        
        # Local prices dictionary (INR per Quintal)
        price_db = {
            "rice": {"current": 2200, "min": 2000, "max": 2400, "trend": "up", "last_week": 2150},
            "wheat": {"current": 2450, "min": 2200, "max": 2600, "trend": "stable", "last_week": 2450},
            "cotton": {"current": 6800, "min": 6200, "max": 7500, "trend": "down", "last_week": 7000},
            "sugarcane": {"current": 340, "min": 315, "max": 350, "trend": "up", "last_week": 335},
            "maize": {"current": 1950, "min": 1800, "max": 2100, "trend": "up", "last_week": 1900},
            "soybean": {"current": 4600, "min": 4200, "max": 5000, "trend": "stable", "last_week": 4610}
        }
        
        norm_crop = crop.strip().lower()
        crop_data = price_db.get(norm_crop, {"current": 2500, "min": 2100, "max": 2800, "trend": "stable", "last_week": 2500})
        
        # Add region variations
        if "maharashtra" in region.lower():
            crop_data["current"] = int(crop_data["current"] * 1.02)
        elif "punjab" in region.lower():
            crop_data["current"] = int(crop_data["current"] * 1.05)
            
        result = {
            "crop": crop,
            "region": region,
            "currency": "INR",
            "unit": "Quintal (100 kg)",
            "pricing": crop_data,
            "timestamp": int(time.time())
        }
        
        cls._set_cache(cache_key, result, 14400)
        return result

    @classmethod
    def search_nearby_resources(cls, lat: float, lon: float, query: str) -> List[Dict[str, Any]]:
        """
        Simulates Places API search for nearby agricultural resources (seed stores, cold storages).
        """
        cache_key = f"places_{lat}_{lon}_{query.lower().replace(' ', '_')}"
        cached = cls._get_cache(cache_key)
        if cached:
            logger.info(f"Serving cached places for query '{query}'")
            return cached["results"]

        logger.info(f"Searching nearby places for '{query}' at {lat}, {lon}")
        
        # Local resources pool
        resources = [
            {"name": "Kisan Krishi Kendra (Seeds & Fertilizer)", "type": "seed_shop", "distance_km": 1.8, "rating": 4.5, "phone": "+91 98765 43210", "lat_offset": 0.01, "lon_offset": -0.008},
            {"name": "Balaji Cold Storage Ltd.", "type": "cold_storage", "distance_km": 4.2, "rating": 4.2, "phone": "+91 98765 43211", "lat_offset": 0.03, "lon_offset": 0.02},
            {"name": "Government Warehouse & Grain Mandi", "type": "mandi", "distance_km": 5.5, "rating": 4.0, "phone": "022-2345678", "lat_offset": -0.04, "lon_offset": 0.015},
            {"name": "Greenhouse Irrigation & Equipment Supplies", "type": "equipment", "distance_km": 3.1, "rating": 4.7, "phone": "+91 98765 43212", "lat_offset": -0.01, "lon_offset": -0.02},
            {"name": "District Soil Testing Laboratory", "type": "lab", "distance_km": 8.0, "rating": 4.3, "phone": "022-8765432", "lat_offset": 0.05, "lon_offset": -0.05}
        ]
        
        # Filter based on query keyword
        filtered = []
        q_lower = query.lower()
        for res in resources:
            if any(k in res["name"].lower() or k in res["type"] for k in q_lower.split()):
                res["latitude"] = lat + res["lat_offset"]
                res["longitude"] = lon + res["lon_offset"]
                filtered.append(res)
                
        # If query is too specific and nothing matched, return all
        if not filtered:
            for res in resources:
                res["latitude"] = lat + res["lat_offset"]
                res["longitude"] = lon + res["lon_offset"]
            filtered = resources
            
        cls._set_cache(cache_key, {"results": filtered}, 86400) # cache for 24h
        return filtered

    @classmethod
    def search_web(cls, query: str) -> str:
        """
        Simulates Search MCP server. Fetches web info or government schemes.
        """
        cache_key = f"websearch_{query.lower().replace(' ', '_')}"
        cached = cls._get_cache(cache_key)
        if cached:
            logger.info(f"Serving cached web search for '{query}'")
            return cached["content"]

        logger.info(f"Performing search for '{query}'")
        
        # Preset knowledge responses for standard farmer queries
        knowledge_base = {
            "pm kisan": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi) is a central sector scheme providing an income support of Rs. 6,000 per year in three equal installments to all landholding farmer families across the country.",
            "crop insurance": "PMFBY (Pradhan Mantri Fasal Bima Yojana) offers comprehensive crop insurance cover against unavoidable natural risks from pre-sowing to post-harvest stage at extremely low premium rates of 2% for Kharif and 1.5% for Rabi crops.",
            "soil health card": "The Soil Health Card Scheme provides crop-wise recommendations of nutrients and fertilizers required for individual farms to help farmers improve productivity through wise use of inputs.",
            "krishi sinchayee": "PMKSY (Pradhan Mantri Krishi Sinchayee Yojana) focuses on creating sources for assured irrigation, promoting micro-irrigation ('Per Drop More Crop'), and water conservation practices."
        }
        
        content = "Search results matching query:\n"
        matched = False
        q_lower = query.lower()
        for key, text in knowledge_base.items():
            if key in q_lower:
                content += f"- **{key.upper()}**: {text}\n"
                matched = True
                
        if not matched:
            content += f"- General agricultural bulletin indicates normal monsoon patterns, and advisories urge crop diversity and integrated pest management.\n"
            content += f"- Farmers can contact the toll-free Kisan Call Centre (KCC) at 1800-180-1551 for direct state-specific updates.\n"
            
        cls._set_cache(cache_key, {"content": content}, 43200) # cache for 12h
        return content
