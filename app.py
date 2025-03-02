# filepath: /Users/Jonathan.Millington-Hotze/Documents/Personal/repos/pibot/app.py
from flask import Flask, jsonify, send_from_directory
from utility.movement_controls import Forwards, Backwards, Left, Right, Stop

app = Flask(__name__, static_folder='static')

# UI route
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# HTTP movement controls
@app.route('/forwards', methods=['POST'])
def move_forwards():
    Forwards()
    return jsonify({"message": "Moving forwards"})

@app.route('/backwards', methods=['POST'])
def move_backwards():
    Backwards()
    return jsonify({"message": "Moving backwards"})

@app.route('/left', methods=['POST'])
def move_left():
    Left()
    return jsonify({"message": "Turning left"})

@app.route('/right', methods=['POST'])
def move_right():
    Right()
    return jsonify({"message": "Turning right"})

@app.route('/stop', methods=['POST'])
def stop_movement():
    Stop()
    return jsonify({"message": "Stopped"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)