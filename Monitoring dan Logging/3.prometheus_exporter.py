import time
import requests
import psutil
from flask import Flask, request, jsonify
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
import threading

app = Flask(__name__)

# Target MLflow model server URL (served locally)
MLFLOW_SERVER_URL = "http://127.0.0.1:8080/invocations"

# Define Prometheus Metrics (12 metrics to satisfy Advanced criteria)
REQUESTS_TOTAL = Counter("ml_requests_total", "Total number of prediction requests")
ERRORS_TOTAL = Counter("ml_prediction_errors_total", "Total number of failed prediction requests")
LATENCY = Histogram("ml_request_latency_seconds", "Inference latency in seconds")

PREDICTED_SCORE_LATEST = Gauge("ml_predicted_score_latest", "The latest predicted student final score")
PREDICTED_SCORE_MEAN = Gauge("ml_predicted_score_mean", "Running mean of predicted student final scores")
PREDICTED_SCORE_MAX = Gauge("ml_predicted_score_max", "Maximum predicted student final score")
PREDICTED_SCORE_MIN = Gauge("ml_predicted_score_min", "Minimum predicted student final score")

INPUT_STUDY_HOURS_MEAN = Gauge("ml_input_study_hours_mean", "Running mean of input study_hours_per_week")
INPUT_ATTENDANCE_RATE_MEAN = Gauge("ml_input_attendance_rate_mean", "Running mean of input attendance_rate")
INPUT_PREVIOUS_SCORE_MEAN = Gauge("ml_input_previous_score_mean", "Running mean of input previous_score")

CPU_USAGE = Gauge("system_cpu_usage_ratio", "System CPU usage ratio (0 to 1)")
MEMORY_USAGE = Gauge("system_memory_usage_ratio", "System memory usage ratio (0 to 1)")

# State for calculating running means, max, and min
class MetricsState:
    def __init__(self):
        self.count = 0
        self.score_sum = 0
        self.score_max = -float('inf')
        self.score_min = float('inf')
        self.study_hours_sum = 0
        self.attendance_rate_sum = 0
        self.previous_score_sum = 0

state = MetricsState()
state_lock = threading.Lock()

@app.route("/predict", methods=["POST"])
def predict():
    REQUESTS_TOTAL.inc()
    start_time = time.time()
    
    try:
        # Forward request to MLflow model server
        payload = request.get_json()
        response = requests.post(MLFLOW_SERVER_URL, json=payload)
        
        # Record latency
        latency_duration = time.time() - start_time
        LATENCY.observe(latency_duration)
        
        if response.status_code != 200:
            ERRORS_TOTAL.inc()
            return jsonify({"error": "MLflow server error", "details": response.text}), response.status_code
        
        predictions = response.json().get("predictions", [])
        if len(predictions) > 0:
            pred_val = float(predictions[0])
            
            # Extract features from input (assuming split orientation payload)
            try:
                df_split = payload.get("dataframe_split", {})
                cols = df_split.get("columns", [])
                data = df_split.get("data", [[]])[0]
                
                study_hours = data[cols.index("study_hours_per_week")] if "study_hours_per_week" in cols else 0
                attendance_rate = data[cols.index("attendance_rate")] if "attendance_rate" in cols else 0
                previous_score = data[cols.index("previous_score")] if "previous_score" in cols else 0
            except Exception:
                study_hours, attendance_rate, previous_score = 0, 0, 0
            
            # Update state metrics under lock
            with state_lock:
                state.count += 1
                state.score_sum += pred_val
                state.study_hours_sum += study_hours
                state.attendance_rate_sum += attendance_rate
                state.previous_score_sum += previous_score
                
                if pred_val > state.score_max:
                    state.score_max = pred_val
                if pred_val < state.score_min:
                    state.score_min = pred_val
                
                # Update Gauges
                PREDICTED_SCORE_LATEST.set(pred_val)
                PREDICTED_SCORE_MEAN.set(state.score_sum / state.count)
                PREDICTED_SCORE_MAX.set(state.score_max)
                PREDICTED_SCORE_MIN.set(state.score_min)
                
                INPUT_STUDY_HOURS_MEAN.set(state.study_hours_sum / state.count)
                INPUT_ATTENDANCE_RATE_MEAN.set(state.attendance_rate_sum / state.count)
                INPUT_PREVIOUS_SCORE_MEAN.set(state.previous_score_sum / state.count)
                
        return jsonify(response.json())
        
    except Exception as e:
        ERRORS_TOTAL.inc()
        return jsonify({"error": "Exporter proxy server error", "details": str(e)}), 500

@app.route("/metrics", methods=["GET"])
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

def update_system_metrics():
    while True:
        try:
            CPU_USAGE.set(psutil.cpu_percent() / 100.0)
            MEMORY_USAGE.set(psutil.virtual_memory().percent / 100.0)
        except Exception:
            pass
        time.sleep(2)

if __name__ == "__main__":
    print("Starting Prometheus MLflow Exporter Proxy on port 8000...")
    # Start system metrics update thread
    threading.Thread(target=update_system_metrics, daemon=True).start()
    
    # Start the Flask app
    app.run(host="0.0.0.0", port=8000)
