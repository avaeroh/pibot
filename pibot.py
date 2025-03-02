from flask import Flask, request, jsonify
from utility import movement_controls
import os

app = Flask(__name__)

@app.route("/move", methods=["POST"])
def move():
    data = request.get_json()
    direction = data.get("direction")

    if direction not in ["forwards", "backwards", "left", "right", "stop"]:
        return jsonify({"error": "Invalid direction"}), 400

    getattr(movement_controls, direction.capitalize())()
    return jsonify({"message": f"Moving {direction}"}), 200

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port)