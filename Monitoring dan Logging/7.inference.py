import time
import random
import pandas as pd
import requests

# URL of the prometheus exporter prediction proxy
PREDICT_URL = "http://127.0.0.1:8000/predict"

def main():
    print("Starting inference generator. Reading preprocessed dataset...")
    try:
        df = pd.read_csv("student_performance_preprocessing.csv")
    except FileNotFoundError:
        try:
            df = pd.read_csv("MLProject/student_performance_preprocessing.csv")
        except FileNotFoundError:
            df = pd.read_csv("../MLProject/student_performance_preprocessing.csv")
    
    # Remove the target column if it exists in the dataset
    if "final_score" in df.columns:
        df = df.drop(columns=["final_score"])
    
    columns = list(df.columns)
    data_records = df.values.tolist()
    
    print(f"Dataset read successfully. Total records: {len(data_records)}.")
    print("Sending random inference requests to proxy endpoint at 1-second intervals. Press Ctrl+C to stop.")
    
    while True:
        try:
            # Pick a random record
            record = random.choice(data_records)
            
            # Format split orientation payload
            payload = {
                "dataframe_split": {
                    "columns": columns,
                    "data": [record]
                }
            }
            
            # Send prediction request
            response = requests.post(PREDICT_URL, json=payload)
            if response.status_code == 200:
                print(f"Prediction success! Input: study_hours={record[1]:.2f}, attendance={record[2]:.2f} -> Predicted Score: {response.json().get('predictions', [None])[0]:.2f}")
            else:
                print(f"Prediction failed with status code {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"Error sending request: {e}")
            
        time.sleep(1)

if __name__ == "__main__":
    main()
