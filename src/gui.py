from flask import Flask, render_template, jsonify, request
from session import Session
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Fuzzer metrics
metrics = {
    "time": "00:00:00",
    "packets_sent": 0,
    "connected_to_target": False
}

# Store scanned devices temporarily
scanned_devices = []

# Initialize session
session = Session()

@app.route('/')
def index():
    return render_template('index.html')

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
    selected_target = next((device for device in scanned_devices if device.identifier == target_identifier), None)
    
    if not selected_target:
        return jsonify({"error": "Target not found"}), 404

    session.set_mode('example_module', 'fuzzing', 'selected', target=selected_target)
    return jsonify({"message": "Target selected", "target": selected_target.__dict__})

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Example of adding a custom radio module (user-defined)
    # from custom_radio_module import CustomRadioModule
    # custom_module = CustomRadioModule('example_module', {'packet_count': 20})
    # session.add_radio_module(custom_module)
    
    # Simulate scanning devices
    for module in session.radio_modules:
        scanned_devices.extend(module.scan_for_devices())

    # Start the session
    session.start()

    app.run(debug=True)
