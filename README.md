# Smart Power Bank Health Monitoring using ESP32 and Machine Learning

## Overview

This project presents a **Smart Power Bank Health Monitoring System** that combines **ESP32** and **Machine Learning** to estimate the **State of Charge (SOC)** of a lithium-ion battery in real time.

The ESP32 collects battery parameters such as voltage and current using an INA219 sensor and transmits the data to a Python application. A trained **Random Forest Regressor** processes the data and predicts the battery's SOC with high accuracy, enabling efficient battery monitoring and management.

---

## Key Features

- Real-time battery parameter monitoring
- ESP32-based data acquisition
- INA219 voltage and current sensing
- Machine Learning based SOC prediction
- Random Forest Regression model
- Live serial communication
- High prediction accuracy
- Scalable architecture for Battery Management Systems (BMS)

---

## Hardware Components

- ESP32 Development Board
- INA219 Current & Voltage Sensor
- 18650 Li-ion Battery
- Dynamic Load
- USB Cable
- Personal Computer

---

## Software Used

- Python 3
- Arduino IDE
- Google Colab
- Jupyter Notebook
- Scikit-learn
- Pandas
- NumPy
- Matplotlib
- Joblib

---

## Machine Learning Model

**Algorithm:** Random Forest Regressor

### Input Features

- Voltage
- Current
- Power
- Battery Charge Cycle

### Output

- State of Charge (SOC %)

---

## Project Workflow

```
Battery
      │
      ▼
INA219 Sensor
      │
      ▼
ESP32
      │
      ▼
Serial Communication
      │
      ▼
Python Application
      │
      ▼
Random Forest Model
      │
      ▼
SOC Prediction
      │
      ▼
Real-Time Monitoring
```

---

## Repository Structure

```
Smart-PowerBank-Health-Monitoring-using-ESP32/
│
├── dataset/
│   ├── charging.csv
│   ├── charging_with_soc.csv
│   ├── discharging.csv
│   ├── ina219_data.csv
│   ├── soc_predictions_final.csv
│   └── soc_predictions_live.csv
│
├── machine_learning/
│   ├── train_model.ipynb
│   ├── prediction_battery_3.py
│   ├── soc_model.pkl
│   └── scaler.pkl
│
├── esp32/
│   └── esp32_code.ino
│
├── docs/
│   └── AIML_Batch15.pdf
│
├── requirements.txt
├── LICENSE
├── .gitignore
└── README.md
```

---

## Performance

| Metric | Value |
|---------|-------|
| Machine Learning Model | Random Forest Regressor |
| R² Score | **0.9561** |
| Mean Absolute Error (MAE) | **±0.003 % SOC** |
| Root Mean Square Error (RMSE) | **0.000109** |

---

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/rio-sathish/Smart-PowerBank-Health-Monitoring-using-ESP32.git
```

### Install Required Packages

```bash
pip install -r requirements.txt
```

### Train the Model

Open and run:

```
machine_learning/train_model.ipynb
```

or

```bash
python machine_learning/train_model.py
```

### Run Real-Time Prediction

```bash
python machine_learning/prediction_battery_3.py
```

---

## Applications

- Smart Power Banks
- Battery Management Systems (BMS)
- Portable Energy Storage
- IoT Battery Monitoring
- Embedded AI Applications

---

## Future Enhancements

- Deploy the ML model directly on ESP32 (TinyML/Edge AI)
- Battery State of Health (SOH) prediction
- Remaining Useful Life (RUL) estimation
- Cloud dashboard for remote monitoring
- Mobile application integration
- Automatic anomaly detection and safety alerts

---

## Documentation

Detailed project documentation is available in the **docs/** folder.

---

## Author

**Sathish M**

Electronics and Communication Engineering

PSG College of Technology

- GitHub: https://github.com/rio-sathish
- LinkedIn: https://www.linkedin.com/in/sathish-m-b19844289/

---

## License

This project is licensed under the MIT License.
