from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from google.cloud import bigquery
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import date
from collections import OrderedDict
import os
import threading
import time

app = FastAPI(
    title="BARB API",
    description="Browser for Adventuring, Recreation, and Backpacking - NPS Data API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Browsers and CDNs may reuse a response for a few minutes. The marts refresh
# on a pipeline schedule, so a short max-age never serves meaningfully stale data.
BROWSER_CACHE_SECONDS = int(os.getenv('BROWSER_CACHE_SECONDS', '300'))

@app.middleware("http")
async def add_cache_control(request, call_next):
    response = await call_next(request)
    if request.method == "GET" and response.status_code == 200:
        response.headers.setdefault("Cache-Control", f"public, max-age={BROWSER_CACHE_SECONDS}")
    return response

client = bigquery.Client(project=os.getenv('GCP_PROJECT_ID'))
DATASET = os.getenv('DATASET_ID')

# In-process result cache. Every request used to run a fresh BigQuery job
# (~650ms even for tiny tables); a warm instance now answers from memory.
# Bounded by an approximate byte budget so large responses (boundaries,
# places) can't exhaust the instance's memory.
CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '600'))
CACHE_MAX_BYTES = int(os.getenv('CACHE_MAX_BYTES', str(64 * 1024 * 1024)))
_cache = OrderedDict()  # key -> (stored_at, rows, approx_bytes)
_cache_bytes = 0
_cache_lock = threading.Lock()

def run_query(query, params=()):
    global _cache_bytes
    params = list(params)
    key = (query, tuple((p.name, p.type_, p.value) for p in params))
    now = time.monotonic()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL_SECONDS:
            _cache.move_to_end(key)
            return hit[1]

    job_config = bigquery.QueryJobConfig(query_parameters=params)
    rows = [dict(row) for row in client.query(query, job_config=job_config).result()]
    size = sum(len(repr(row)) for row in rows)

    with _cache_lock:
        old = _cache.pop(key, None)
        if old:
            _cache_bytes -= old[2]
        if size <= CACHE_MAX_BYTES:
            _cache[key] = (now, rows, size)
            _cache_bytes += size
            while _cache_bytes > CACHE_MAX_BYTES:
                _, (_, _, evicted) = _cache.popitem(last=False)
                _cache_bytes -= evicted
    return rows

# Response Models
class Park(BaseModel):
    park_id: str
    park_code: str
    park_short_name: Optional[str]
    park_full_name: str
    park_description: Optional[str]
    full_address: Optional[str]
    google_maps_url: Optional[str]
    apple_maps_url: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    park_url: Optional[str]
    plan_your_visit_url: Optional[str]
    park_image_title: Optional[str]
    park_image_caption: Optional[str]
    park_image_url: Optional[str]
    amenities_json: Optional[str]

class Activity(BaseModel):
    activity_id: str
    activity_title: str
    activity_type: Optional[str]
    short_description: Optional[str]
    long_description: Optional[str]
    activity_url: Optional[str]
    duration: Optional[str]
    trail_miles: Optional[float]
    trail_length_full: Optional[str]
    fee_description: Optional[str]
    park_code: str
    park_short_name: Optional[str]
    park_full_name: Optional[str]
    activity_image_caption: Optional[str]
    activity_image_url: Optional[str]

class Alert(BaseModel):
    alert_id: str
    alert_title: str
    alert_description: Optional[str]
    alert_url: Optional[str]
    alert_category: Optional[str]
    park_code: str
    park_short_name: Optional[str]
    park_full_name: Optional[str]
    is_emergency_alert: Optional[bool]

class Campground(BaseModel):
    campground_id: str
    park_code: str
    campground_name: str
    campground_description: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    sites_first_come_first_serve_count: Optional[int]
    sites_reservable_count: Optional[int]
    reservation_info: Optional[str]
    wheelchair_access: Optional[str]
    total_sites: Optional[int]
    park_short_name: Optional[str]
    park_full_name: Optional[str]
    campground_url: Optional[str]
    reservation_details: Optional[str]
    accessibility_classifications: Optional[str]
    campground_image_url: Optional[str]
    is_reservation_url: Optional[bool]

class Event(BaseModel):
    event_id: str
    event_title: str
    event_description: Optional[str]
    info_url: Optional[str]
    park_code: str
    park_short_name: Optional[str]
    park_full_name: Optional[str]
    event_start_date: Optional[Union[str, date]]
    is_recurring: Optional[bool]
    is_all_day: Optional[bool]
    is_free: Optional[bool]
    is_registration_required: Optional[bool]
    registration_url: Optional[str]
    event_end_date: Optional[Union[str, date]]
    event_image_url: Optional[str]

class Hike(BaseModel):
    hike_id: str
    hike_name: str
    hike_description: Optional[str]
    hike_url: Optional[str]
    hike_duration: Optional[str]
    hike_distance: Optional[str]
    hike_difficulty: Optional[str]
    length_category: Optional[str]
    park_code: str
    park_short_name: Optional[str]
    park_full_name: Optional[str]
    hike_image_url: Optional[str]
    accessible_status: Optional[str]

class Place(BaseModel):
    place_id: str
    npmap_id: Optional[str]
    geometry_poi_id: Optional[str]
    place_name: str
    body_text: Optional[str]
    listing_description: Optional[str]
    location_description: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    lat_long: Optional[str]
    place_url: Optional[str]
    managed_by_url: Optional[str]
    is_managed_by_nps: Optional[bool]
    is_open_to_public: Optional[bool]
    is_map_pin_hidden: Optional[bool]
    is_passport_stamp_location: Optional[bool]
    passport_stamp_location_description: Optional[str]
    audio_description: Optional[str]
    credit: Optional[str]
    primary_image_url: Optional[str]
    primary_image_caption: Optional[str]
    primary_image_alt_text: Optional[str]
    primary_image_credit: Optional[str]
    park_full_name: Optional[str]
    park_code: Optional[str]
    park_url: Optional[str]
    park_states: Optional[str]
    image_count: Optional[int]
    related_park_count: Optional[int]
    difficulty_raw: Optional[str]
    duration_raw: Optional[str]
    distance_raw: Optional[str]
    elevation_change_raw: Optional[str]
    difficulty: Optional[str]
    duration_hours: Optional[float]
    distance_miles: Optional[float]
    elevation_feet: Optional[float]
    park_short_name: Optional[str]
    amenities_json: Optional[str]

class Tour(BaseModel):
    tour_id: str
    park_code: str
    park_short_name: Optional[str]
    park_full_name: Optional[str]
    park_url: Optional[str]
    tour_title: str
    tour_description: Optional[str]
    duration_min: Optional[int]
    duration_max: Optional[int]
    duration_unit: Optional[str]
    tour_min_duration_in_minutes: Optional[int]
    tour_max_duration_in_minutes: Optional[int]
    duration_unit_label: Optional[str]
    image_url: Optional[str]

class Boundary(BaseModel):
    park_code: str
    park_boundary_geometry_id: str
    boundary_type: Optional[str]
    geometry_json: Optional[str]
    park_short_name: Optional[str]
    park_full_name: Optional[str]

# Parks Endpoints
@app.get("/parks", response_model=List[Park])
def get_parks(
    park_code: Optional[str] = Query(None, description="Filter by park code"),
    limit: int = Query(100, le=1000)
):
    """Get all parks with optional filters"""
    query = f"""
    SELECT *
    FROM `{DATASET}.nps__mart_national_parks`
    WHERE 1=1
    """
    params = []
    
    if park_code:
        query += " AND park_code = @park_code"
        params.append(bigquery.ScalarQueryParameter("park_code", "STRING", park_code))
    
    query += f" LIMIT {limit}"
    
    return run_query(query, params)

@app.get("/parks/{park_code}", response_model=Park)
def get_park(park_code: str):
    """Get specific park details"""
    query = f"""
    SELECT *
    FROM `{DATASET}.nps__mart_national_parks`
    WHERE park_code = @park_code
    """
    results = run_query(query, [bigquery.ScalarQueryParameter("park_code", "STRING", park_code)])
    
    if not results:
        raise HTTPException(status_code=404, detail="Park not found")
    
    return dict(results[0])

# Activities Endpoints
@app.get("/activities", response_model=List[Activity])
def get_activities(
    park_code: Optional[str] = Query(None, description="Filter by park code")
):
    """Get park activities"""
    query = f"""
    SELECT activity_id, activity_title, activity_type, short_description, long_description, 
           activity_url, duration, trail_miles, trail_length_full, fee_description,
           park_code, park_short_name, park_full_name, activity_image_caption, activity_image_url
    FROM `{DATASET}.nps__mart_national_park_activities`
    WHERE 1=1
    """
    params = []
    
    if park_code:
        query += " AND park_code = @park_code"
        params.append(bigquery.ScalarQueryParameter("park_code", "STRING", park_code))
    
    return run_query(query, params)

# Alerts Endpoints
@app.get("/alerts", response_model=List[Alert])
def get_alerts(
    park_code: Optional[str] = None,
    category: Optional[str] = None,
    emergency_only: Optional[bool] = Query(None, description="Filter to emergency alerts only"),
    limit: int = Query(100, le=1000)
):
    """Get park alerts"""
    query = f"""
    SELECT *
    FROM `{DATASET}.nps__mart_national_park_alerts`
    WHERE 1=1
    """
    params = []
    
    if park_code:
        query += " AND park_code = @park_code"
        params.append(bigquery.ScalarQueryParameter("park_code", "STRING", park_code))
    
    if category:
        query += " AND alert_category = @category"
        params.append(bigquery.ScalarQueryParameter("category", "STRING", category))
    
    if emergency_only:
        query += " AND is_emergency_alert = true"
    
    query += f" LIMIT {limit}"
    
    return run_query(query, params)

# Campgrounds Endpoints
@app.get("/campgrounds", response_model=List[Campground])
def get_campgrounds(
    park_code: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get campgrounds"""
    query = f"""
    SELECT *
    FROM `{DATASET}.nps__mart_national_park_campgrounds`
    WHERE 1=1
    """
    params = []
    
    if park_code:
        query += " AND park_code = @park_code"
        params.append(bigquery.ScalarQueryParameter("park_code", "STRING", park_code))
    
    query += f" LIMIT {limit}"
    
    return run_query(query, params)

# Events Endpoints
@app.get("/events", response_model=List[Event])
def get_events(
    park_code: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get park events"""
    query = f"""
    SELECT *
    FROM `{DATASET}.nps__mart_national_park_events`
    WHERE 1=1
    """
    params = []
    
    if park_code:
        query += " AND park_code = @park_code"
        params.append(bigquery.ScalarQueryParameter("park_code", "STRING", park_code))
    
    query += f" LIMIT {limit}"
    
    return run_query(query, params)

# Hikes Endpoints
@app.get("/hikes", response_model=List[Hike])
def get_hikes(
    park_code: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get park hikes"""
    query = f"""
    SELECT *
    FROM `{DATASET}.nps__mart_national_park_hikes`
    WHERE 1=1
    """
    params = []
    
    if park_code:
        query += " AND park_code = @park_code"
        params.append(bigquery.ScalarQueryParameter("park_code", "STRING", park_code))
    
    query += f" LIMIT {limit}"
    
    return run_query(query, params)

# Places Endpoints
@app.get("/places", response_model=List[Place])
def get_places(
    park_code: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get park places of interest"""
    query = f"""
    SELECT *
    FROM `{DATASET}.nps__mart_national_park_places`
    WHERE 1=1
    """
    params = []
    
    if park_code:
        query += " AND park_code = @park_code"
        params.append(bigquery.ScalarQueryParameter("park_code", "STRING", park_code))
    
    query += f" LIMIT {limit}"
    
    return run_query(query, params)

# Tours Endpoints
@app.get("/tours", response_model=List[Tour])
def get_tours(
    park_code: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get park tours"""
    query = f"""
    SELECT *
    FROM `{DATASET}.nps__mart_national_park_tours`
    WHERE 1=1
    """
    params = []
    
    if park_code:
        query += " AND park_code = @park_code"
        params.append(bigquery.ScalarQueryParameter("park_code", "STRING", park_code))
    
    query += f" LIMIT {limit}"
    
    return run_query(query, params)

# Boundaries Endpoints
@app.get("/boundaries", response_model=List[Boundary])
def get_boundaries(
    park_code: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get park boundaries"""
    query = f"""
    SELECT park_code, park_boundary_geometry_id, boundary_type,
           geometry_json, park_short_name, park_full_name
    FROM `{DATASET}.nps__mart_national_park_boundaries`
    WHERE 1=1
    """
    params = []
    
    if park_code:
        query += " AND park_code = @park_code"
        params.append(bigquery.ScalarQueryParameter("park_code", "STRING", park_code))
    
    query += f" LIMIT {limit}"
    
    return run_query(query, params)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)