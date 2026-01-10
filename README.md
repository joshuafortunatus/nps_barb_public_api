# BARB API

Browser for Adventuring, Recreation, and Backpacking - A public API for National Parks Service data.

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

## API Documentation

Once deployed, visit `/docs` for interactive API documentation (Swagger UI).

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
GCP_PROJECT=your-project-id
DATASET_ID=nps_barb
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
  --set-env-vars GCP_PROJECT=your-project-id,DATASET_ID=nps_barb
```

## Data Source

Data is sourced from the National Parks Service API and processed through dbt transformations. See the [personal-dbt](https://github.com/joshuafortunatus/personal-dbt) repository for data pipeline details.

## License

MIT