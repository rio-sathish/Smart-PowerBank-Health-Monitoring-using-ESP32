# Machine Learning

This folder contains the Machine Learning implementation used for predicting the State of Charge (SOC) of a lithium-ion battery in the Smart Power Bank Health Monitoring System.

## Model

- Algorithm: Random Forest Regressor
- Task: Battery State of Charge (SOC) Prediction
- Framework: Scikit-learn

## Files

| File | Description |
|------|-------------|
| train_model.ipynb | Google Colab notebook used to preprocess data, train, and evaluate the model |
| prediction_battery_3.py | Python application for real-time SOC prediction |
| soc_model.pkl | Trained Random Forest model |
| scaler.pkl | Feature scaler used during prediction |

## Input Features

- Voltage (V)
- Current (A)
- Power (W)
- Battery Charge Cycle

## Output

- Predicted Battery State of Charge (SOC %)

## Performance

- Model: Random Forest Regressor
- R² Score: **0.9561**
- Mean Absolute Error (MAE): **±0.003 % SOC**
- Root Mean Square Error (RMSE): **0.000109**

## Workflow

1. Load the battery dataset.
2. Preprocess the data.
3. Train the Random Forest model.
4. Save the trained model and scaler.
5. Load the saved model for real-time prediction.
6. Predict SOC from ESP32 sensor data.

## Required Libraries

- Python 3.x
- NumPy
- Pandas
- Scikit-learn
- Joblib
- Matplotlib

## Usage

### Train the Model

```bash
python train_model.py
```

### Run Real-Time Prediction

```bash
python prediction_battery_3.py
```
