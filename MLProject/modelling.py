import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import os

def main(n_estimators=100, max_depth=None, random_state=42):
    # Load dataset
    df = pd.read_csv("student_performance_preprocessing.csv")
    X = df.drop(columns=["final_score"])
    y = df["final_score"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    with mlflow.start_run() as run:
        # Check if parameters are already logged by MLflow Projects to avoid collisions
        existing_params = mlflow.get_run(run.info.run_id).data.params
        if "max_depth" not in existing_params:
            mlflow.log_param("n_estimators", n_estimators)
            mlflow.log_param("max_depth", max_depth)
            mlflow.log_param("random_state", random_state)
        
        model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=random_state)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2", r2)
        
        mlflow.sklearn.log_model(model, "random_forest_model")
        
        with open("run_id.txt", "w") as f:
            f.write(run.info.run_id)
        
        print(f"Run ID: {run.info.run_id}")
        print(f"MAE: {mae:.4f}, RMSE: {rmse:.4f}, R2: {r2:.4f}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_estimators", type=int, default=100)
    parser.add_argument("--max_depth", type=int, default=None)
    parser.add_argument("--random_state", type=int, default=42)
    args = parser.parse_args()
    max_depth = args.max_depth
    if max_depth == -1:
        max_depth = None
    main(n_estimators=args.n_estimators, max_depth=max_depth, random_state=args.random_state)