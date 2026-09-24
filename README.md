# Dynamic Vegetation Management

Dynamic Vegetation Management (DVM) is a Python and Flask prototype for identifying vegetation encroachment near electrical conductors. It combines image-based AI detection with a local conductor-location dataset to help utility teams identify potential clearance risks before they become outages or safety hazards.

The wider DVM vision uses UAV RGB and LiDAR data, predictive vegetation-growth models, optimized crew routing, and Network Management System (NMS) workflows to support proactive vegetation maintenance.

## Current Prototype Features

- Upload a vegetation-corridor image through a browser interface.
- Detect trees and power lines with a Roboflow inference workflow.
- Evaluate tree and conductor bounding boxes to identify possible encroachment.
- Load conductor details from a local CSV file using latitude and longitude.
- Display detection results and save annotated output images in `processed_image/`.
- Generate a six-digit simulated Non-Outage Event reference and operation-note message when encroachment is detected.

> The current prototype **does not create real NMS events or operation notes**. It displays the event message for demonstration purposes.

## Solution Vision

The intended end-to-end DVM workflow is:

1. UAVs collect RGB imagery and LiDAR point clouds along power-line corridors.
2. Preprocessing and data fusion isolate trees, conductors, and terrain.
3. AI models classify vegetation and detect encroachment near conductor safety corridors.
4. Growth modelling forecasts future vegetation risk.
5. Utility workflows use the results for inspection planning, crew routing, work orders, switching plans, and operator visibility in NMS.

## Solution Architecture

This video explains the proposed DVM architecture, from UAV data acquisition and AI-based encroachment analysis through NMS-supported utility operations.

[Watch the solution architecture explanation](Architecture%20Explanation%20-%20Trim.mp4)

## Technology Stack

- Python 3.12+
- Flask
- OpenCV and NumPy
- Roboflow Inference SDK
- Pandas, Matplotlib, and Tabulate
- HTML, CSS, and JavaScript
- CSV-based conductor lookup

## Project Structure

```text
.
|-- app.py                       # Flask application and analysis workflow
|-- conductors_location.csv       # Local conductor export (not committed)
|-- templates/
|   `-- index.html                # Web interface
|-- static/
|   |-- script.js                 # Browser interactions
|   `-- style.css                 # Interface styling
|-- uploads/                      # Uploaded images (generated at runtime)
|-- processed_image/              # Annotated images (generated at runtime)
|-- .env.example                  # Environment variable template
`-- requirements.txt              # Python dependencies
```

## Getting Started

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd "Dynamic Vegetation Management"
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the template and add your Roboflow API key:

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Edit `.env` and set `ROBOFLOW_API_KEY` to your own key. Never commit `.env` to GitHub.

### 5. Add the conductor dataset

Place `conductors_location.csv` in the project root. The file must be a headerless CSV with this column order:

```text
latitude,longitude,alias,hdl,phase
```

Example:

```csv
40.72985477,-81.52852817,T321SS_Secondary,409.85,
```

### 6. Run the application

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## How to Use

1. Enter the latitude and longitude for the inspection location.
2. Select **Load Conductors** and choose a conductor from the list.
3. Upload an image of the vegetation corridor.
4. Select **Analyze**.
5. Review the tree/conductor results and the analysis message.

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `ROBOFLOW_API_URL` | Roboflow inference endpoint. |
| `ROBOFLOW_API_KEY` | Your Roboflow API key. |
| `ROBOFLOW_WORKSPACE` | Roboflow workspace name. |
| `ROBOFLOW_WORKFLOW_ID` | Roboflow workflow ID. |
| `UPLOAD_FOLDER` | Runtime folder for uploaded images. |
| `PROCESSED_FOLDER` | Runtime folder for annotated images. |
| `CONDUCTORS_CSV` | Path to the local conductor CSV. |
| `HOST` | Flask host address. |
| `PORT` | Flask port. |
| `FLASK_DEBUG` | Enables Flask debug mode when set to `true`. |

## Important Data and Security Notes

- Do not publish `.env`, API keys, internal conductor identifiers, coordinates, or operational data.
- `conductors_location.csv` is ignored by Git by default. Supply a sanitized sample dataset if you want to include an example publicly.
- This project is a prototype and should be validated against utility safety procedures and data-governance requirements before operational use.

## Future Enhancements

- UAV LiDAR and RGB data fusion.
- Tree species classification and height estimation.
- Vegetation-growth prediction using Richard's Growth Model.
- GIS risk maps and inspection dashboards.
- Optimized UAV and vegetation-crew routing.
- Secure, authenticated NMS event, work-order, and switching-plan integration.

## Demo Walkthrough

Watch the DVM prototype walkthrough, including conductor loading, image analysis, and encroachment results.

[Watch the DVM demo walkthrough](DVM%20Demo%20Video.mp4)

## License

No license has been selected yet. Add a license file before accepting external reuse or contributions.
