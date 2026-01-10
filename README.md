# BARB API

Browser for Adventuring, Recreation, and Backpacking - A public API for National Parks Service data.

## Live API

🔗 **API Base URL:** https://barb-api-658225020507.us-central1.run.app

📚 **Interactive Documentation:** https://barb-api-658225020507.us-central1.run.app/docs

## Overview

BARB API provides programmatic access to comprehensive National Parks Service data including parks, campgrounds, trails, activities, events, and more.

## Endpoints

- `GET /parks` - List all parks
- `GET /parks/{park_code}` - Get specific park details
- `GET /activities` - List park activities
- `GET /alerts` - Get park alerts
- `GET /campgrounds` - List campgrounds
- `GET /events` - Get park events
- `GET /hikes` - List hiking trails
- `GET /places` - Get places of interest
- `GET /tours` - List park tours
- `GET /boundaries` - Get park boundary data

All endpoints support filtering by `park_code` where applicable.

## Quick Start

### cURL Examples

Get all parks:
```bash
curl https://barb-api-658225020507.us-central1.run.app/parks
```

Get a specific park:
```bash
curl https://barb-api-658225020507.us-central1.run.app/parks/YOSE
```

Get alerts for Yosemite:
```bash
curl https://barb-api-658225020507.us-central1.run.app/alerts?park_code=YOSE
```

### Python
```python
import requests

# Get all parks
response = requests.get('https://barb-api-658225020507.us-central1.run.app/parks')
parks = response.json()

# Get specific park
response = requests.get('https://barb-api-658225020507.us-central1.run.app/parks/YOSE')
yosemite = response.json()

# Get campgrounds for a park
response = requests.get('https://barb-api-658225020507.us-central1.run.app/campgrounds?park_code=YOSE')
campgrounds = response.json()
```

### JavaScript
```javascript
// Get all parks
fetch('https://barb-api-658225020507.us-central1.run.app/parks')
  .then(response => response.json())
  .then(data => console.log(data));

// Get specific park
fetch('https://barb-api-658225020507.us-central1.run.app/parks/YOSE')
  .then(response => response.json())
  .then(data => console.log(data));

// Get campgrounds with async/await
async function getCampgrounds(parkCode) {
  const response = await fetch(`https://barb-api-658225020507.us-central1.run.app/campgrounds?park_code=${parkCode}`);
  const campgrounds = await response.json();
  return campgrounds;
}
```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
GCP_PROJECT_ID=your-project-id
DATASET_ID=your-dataset-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

3. Run the API:
```bash
uvicorn main:app --reload
```

4. Visit `http://localhost:8000/docs` for interactive documentation.

## Deployment

Deploy to Google Cloud Run:
```bash
gcloud run deploy barb-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=your-project-id,DATASET_ID=your-dataset-id
```

## Data Source

Data is primarily sourced from the National Parks Service API, with some data manually imbued.

## License

MIT