from flask import Flask, request, jsonify, render_template, send_from_directory
from PIL import Image, ImageDraw
import os
from datetime import datetime
from pathlib import Path
import csv
import random
from dotenv import load_dotenv
from inference_sdk import InferenceHTTPClient

load_dotenv()

app = Flask(__name__)

message="Touching"

# Vercel functions can write only to /tmp. This takes precedence over imported
# local settings so the same .env file can be used for local development and Vercel.
IS_VERCEL = bool(os.getenv("VERCEL"))
UPLOAD_FOLDER = "/tmp/uploads" if IS_VERCEL else os.getenv("UPLOAD_FOLDER", "uploads")
PROCESSED_FOLDER = (
    "/tmp/processed_image" if IS_VERCEL else os.getenv("PROCESSED_FOLDER", "processed_image")
)
CONDUCTORS_CSV = Path(os.getenv("CONDUCTORS_CSV", "conductors_location.csv"))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

client = InferenceHTTPClient(
    api_url=os.getenv("ROBOFLOW_API_URL", "https://detect.roboflow.com"),
    api_key=os.getenv("ROBOFLOW_API_KEY")
)

@app.route("/")
def index():
    return render_template("index.html")

def get_devices_info(latitude, longitude):
    """Return conductors at the selected coordinates from the local CSV export.

    The CSV has no header row and uses this column order:
    latitude, longitude, alias, hdl, phase.
    """
    if not CONDUCTORS_CSV.exists():
        print(f"Conductors CSV not found: {CONDUCTORS_CSV}")
        return []

    # Compare numeric values so harmless formatting differences (for example,
    # -89.4758291 vs -89.47582910) do not prevent a match.
    try:
        requested_latitude = float(latitude)
        requested_longitude = float(longitude)
    except (TypeError, ValueError):
        return []

    result = []
    with CONDUCTORS_CSV.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            if len(row) < 5:
                continue
            try:
                row_latitude = float(row[0].strip())
                row_longitude = float(row[1].strip())
            except ValueError:
                # Also safely skips an optional header row if one is added later.
                continue

            if row_latitude == requested_latitude and row_longitude == requested_longitude:
                result.append({
                    "alias": row[2].strip(),
                    "Hdl": row[3].strip(),
                    "phase": row[4].strip(),
                })

    return result


@app.route('/get_devices', methods=['POST'])
def get_devices():
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    if not latitude or not longitude:
        return jsonify({"error": "Latitude and longitude required"}), 400

    devices = get_devices_info(latitude, longitude)
    return jsonify(devices)

@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files["image"]
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    result = client.run_workflow(
        workspace_name=os.getenv("ROBOFLOW_WORKSPACE", "innovationewnms"),
        workflow_id=os.getenv("ROBOFLOW_WORKFLOW_ID", "custom-workflow"),
        images={"image": filepath}
    )

    def extract_boxes(result):
        tree_boxes, wire_boxes = [], []
        for item in result:
            if isinstance(item, dict) and "predictions" in item:
                for prediction in item["predictions"]["predictions"]:
                    x, y, w, h = prediction["x"], prediction["y"], prediction["width"], prediction["height"]
                    class_name = prediction["class"]
                    x1, y1 = int(x - w / 2), int(y - h / 2)
                    x2, y2 = int(x + w / 2), int(y + h / 2)

                    if class_name.lower() == "tree":
                        tree_boxes.append([x1, y1, x2, y2])
                    elif class_name.lower() == "powerline":
                        wire_boxes.append([x1, y1, x2, y2])
        return tree_boxes, wire_boxes

    tree_boxes, wire_boxes = extract_boxes(result)
    print(f"✅ Detected {len(tree_boxes)} trees and {len(wire_boxes)} powerlines.")

    def are_adjacent(gaps):
        adjacent_pairs = [{"Top", "Left"}, {"Top", "Right"}, {"Bottom", "Left"}, {"Bottom", "Right"}]
        return any(set(gaps) == pair for pair in adjacent_pairs)

    def draw_corridors(image, tree_boxes, wire_boxes, margin=20):
        draw = ImageDraw.Draw(image)
        corridor_boxes = []
        touching_flag = False
        results = []
        for wire_idx, wire in enumerate(wire_boxes, start=1):
            x1, y1, x2, y2 = wire
            for tree_idx, tree in enumerate(tree_boxes, start=1):
                t_x1, t_y1, t_x2, t_y2 = tree
                # x1, y1, x2, y2 = x1-5, y1, x2+5, y2
                t_x1, t_y1, t_x2, t_y2 = t_x1-10, t_y1-10, t_x2-10, t_y2-10
                corridor_x1, corridor_y1, corridor_x2, corridor_y2 = x1, y1, x2, y2
                
                gaps = []

                if t_y2 > y1 and t_y1 < y1:
                    corridor_y1 = max(0, y1 - margin)
                    gaps.append("Top")
                if t_y1 < y2 and t_y2 > y2:
                    corridor_y2 = y2 + margin
                    gaps.append("Bottom")
                if t_x2 > x1 and t_x1 < x1:
                    corridor_x1 = max(0, x1 - margin)
                    gaps.append("Left")
                if t_x1 < x2 and t_x2 > x2:
                    corridor_x2 = x2 + margin
                    gaps.append("Right")

                touching = len(gaps) > 2
                status = "Yes" if touching else "No"

                if touching:
                    touching_flag = True

                results.append({"Tree No": tree_idx, "Powerline No": wire_idx, "Result": status})
                
                corridor_box = [corridor_x1, corridor_y1, corridor_x2, corridor_y2]
                corridor_boxes.append(corridor_box)

                # Print details
                print(f"\nPowerline {wire_idx} vs Tree {tree_idx}:")
                print(f"Powerline Box: {wire}")
                print(f"Tree Box: {tree}")
                print(f"Gaps: {gaps}")
                print(f"Status: {status}")

                # Draw powerline box (Red)
            draw.rectangle((x1, y1, x2, y2), outline=(0, 0, 255), width=2)
            draw.text((x1 + 5, y1 + 10), f"PL {wire_idx}", fill=(0, 0, 255))

            # Draw tree box (Green)
            draw.rectangle((t_x1 + 10, t_y1 + 10, t_x2 + 10, t_y2 + 10), outline=(0, 255, 0), width=2)
            draw.text((t_x1 + 15, t_y1 + 30), f"Tree {tree_idx}", fill=(0, 255, 0))

            # Draw corridor box (Blue)
            draw.rectangle((corridor_x1, corridor_y1, corridor_x2, corridor_y2), outline=(255, 0, 0), width=1)

            # Draw status label (Touching or Nearby)
            color = (0, 0, 255) if touching else (0, 255, 255)
            draw.text((corridor_x1 + 5, corridor_y1 - 5), f"{status} T{tree_idx}-P{wire_idx}", fill=color)

        print(results)
        print(f"\nTouching Detected? {'✅ True' if touching_flag else '❌ False'}")

        return touching_flag, results

    image = Image.open(filepath).convert("RGB")
    touching_flag, results = draw_corridors(image, tree_boxes, wire_boxes)
    print(f"Test: {touching_flag}, {results}")

    if touching_flag:
        device = request.form.get("alias", "the selected conductor")
        numb_value = random.randint(100000, 999999)
        message = (
            f"Tree Encroachment Detected & Non Outage Event #{numb_value} created on "
            f"{device}, and an Operation Event Note is added with this same note; "
            "a unique symbol will be displayed in Viewer of DMS application."
        )
        print(message)

    else:
        device = request.form.get('alias', 'the selected conductor')
        message = f"No Encroachment on {device}"
        print('No event creation needed')

    output_folder = Path("processed_image")
    output_folder.mkdir(parents=True, exist_ok=True)
    status_text = "Touching" if touching_flag else "Not_Touching"
    filename = f"{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}_{status_text}.jpg"
    output_path = output_folder / filename
    image.save(output_path, format="JPEG")
    print(f"✅ Image saved at: {output_path}")
    # results = tuple(results)

    return jsonify({
        "message": f"{message}",
        "tabulation": results
    })

@app.route("/processed_image/<filename>")
def get_processed_image(filename):
    return send_from_directory(PROCESSED_FOLDER, filename)

if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
