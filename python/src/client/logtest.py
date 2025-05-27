from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import time
import os

# The user specified the service is a Prometheus Pushgateway at http://localhost:9090/
# Default Pushgateway port is 9091, but we'll use 9090 as specified.
PUSHGATEWAY_URL = os.environ.get("PUSHGATEWAY_URL", "localhost:9090") 
# push_to_gateway expects host:port, not http://host:port

JOB_NAME = "my_hello_world_job"
METRIC_NAME = "hello_world_gauge"
METRIC_DESCRIPTION = "A simple gauge metric for testing Pushgateway."

def send_gauge_metric_to_pushgateway(value: float):
    """
    Creates a gauge metric, sets its value, and pushes it to the Pushgateway.
    """
    registry = CollectorRegistry()
    
    try:
        # Try to unregister the metric first if it exists from a previous run in the same process
        # This is more relevant for long-running processes, but good practice.
        # For a simple script, it might not be strictly necessary.
        if METRIC_NAME in registry._names_to_collectors:
             registry.unregister(registry._names_to_collectors[METRIC_NAME])
    except Exception as e:
        print(f"Note: Could not unregister pre-existing metric '{METRIC_NAME}' (might be harmless): {e}")

    try:
        gauge = Gauge(METRIC_NAME, METRIC_DESCRIPTION, registry=registry)
        gauge.set(value)
        
        print(f"Attempting to push metric '{METRIC_NAME}' with value {value} to Pushgateway at: {PUSHGATEWAY_URL}")
        print(f"Job name: {JOB_NAME}")

        push_to_gateway(PUSHGATEWAY_URL, job=JOB_NAME, registry=registry)
        
        print("Metric pushed successfully to Pushgateway.")
        print(f"You should be able to see it at http://{PUSHGATEWAY_URL}/metrics for job '{JOB_NAME}'.")

    except ConnectionRefusedError: # More specific error for push_to_gateway
        print(f"Error: Connection refused by Pushgateway at {PUSHGATEWAY_URL}. Is it running and accessible?")
    except Exception as e:
        print(f"An error occurred while pushing the metric: {e}")

if __name__ == "__main__":
    print("--- Pushgateway Metric Test Script ---")
    print("This script will attempt to send a gauge metric to a Prometheus Pushgateway.")
    print("It requires the 'prometheus_client' library. If not installed, run: pip install prometheus_client")
    print(f"Target Pushgateway: {PUSHGATEWAY_URL}")
    print(f"Job Name: {JOB_NAME}")
    print("-" * 30)
    
    # Send a simple gauge metric with a value, e.g., current timestamp or a fixed number
    current_time_value = time.time()
    send_gauge_metric_to_pushgateway(current_time_value)
    
    print("-" * 30)
    print("Metric push attempt finished. Check the Pushgateway and the output above for results.")