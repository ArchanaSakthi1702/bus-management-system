from fastapi import Depends,APIRouter
from typing import Dict
from datetime import datetime
from admin_dependancies import is_admin
from schemas import GPSUpdate

gps_router=APIRouter(
    prefix="/gps"
)

bus_locations: Dict[str, dict] = {}

@gps_router.post("/update-bus-location",dependencies=[Depends(is_admin)])
async def update_bus_location(data: GPSUpdate):
    """
    Receive GPS data from a bus and save in memory.
    """
    bus_locations[data.bus_id] = {
        "lat": data.latitude,
        "lon": data.longitude,
        "timestamp": datetime.now() 
    }
    return {"status": "success", "bus_id": data.bus_id}
