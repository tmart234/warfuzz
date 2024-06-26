from radioModule import RadioModule  # Correct import statement
import logging
from typing import List, Dict, Any, Optional
from flask import Flask, render_template, jsonify, request
from wardriver import WardriverManager

logger = logging.getLogger(__name__)
app = Flask(__name__)

# Fuzzer metrics
metrics = {
    "time": "00:00:00",
    "packets_sent": 0,
    "connected_to_target": False
}

manager = WardriverManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/metrics', methods=['POST'])
def update_metrics():
    global metrics
    data = request.json
    metrics.update(data)
    return jsonify(metrics)

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    return jsonify(metrics)

@app.route('/api/metrics', methods=['POST'])
def update_metrics():
    global metrics
    data = request.json
    metrics.update(data)
    return jsonify(metrics)


@app.route('/api/devices', methods=['GET'])
def get_devices():
    return jsonify([device.__dict__ for device in scanned_devices])

@app.route('/api/select_target', methods=['POST'])
def select_target():
    global scanned_devices
    data = request.json
    target_identifier = data.get('identifier')
    for device in scanned_devices:
        if device.identifier == target_identifier:
            selected_target = device
            break
    else:
        return jsonify({"error": "Target not found"}), 404

    # Example usage of setting the target for a specific module
    manager.configure_module('radio1', 'fuzzing', 'selected', target=selected_target)
    return jsonify({"message": "Target selected", "target": selected_target.__dict__})

def update_global_metrics(time: str, packets_sent: int, connected_to_target: bool):
    global metrics
    metrics['time'] = time
    metrics['packets_sent'] = packets_sent
    metrics['connected_to_target'] = connected_to_target

if __name__ == '__main__':
    app.run(debug=True)
