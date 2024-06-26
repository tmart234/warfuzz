from radioModule import RadioModule  # Correct import statement
import logging
from typing import List, Dict, Any, Optional
from flask import Flask, render_template, jsonify, request

logger = logging.getLogger(__name__)
app = Flask(__name__)

# Fuzzer metrics
metrics = {
    "time": "00:00:00",
    "packets_sent": 0,
    "connected_to_target": False
}

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


def update_global_metrics(time: str, packets_sent: int, connected_to_target: bool):
    global metrics
    metrics['time'] = time
    metrics['packets_sent'] = packets_sent
    metrics['connected_to_target'] = connected_to_target

if __name__ == '__main__':
    app.run(debug=True)
