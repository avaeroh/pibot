from control.server import app
from flask import jsonify
from utility.movement_controls import Forwards, Backwards, Left, Right, Stop

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
