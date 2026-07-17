"""
================================================================================
BATTERY STATE OF CHARGE PREDICTION SYSTEM
Step 4: Real-Time SOC Prediction from ESP32
================================================================================
Complete Production-Ready Code
Features:
- Real-time data acquisition from ESP32
- ML-based SOC prediction (Random Forest)
- Coulomb counting integration
- Charging/Discharging mode detection
- Voltage drop and fault detection
- Live data visualization and logging
- Comprehensive statistics reporting
- Firebase Realtime Database cloud sync
================================================================================
"""

import warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore')

# ============================================================
# IMPORT ALL REQUIRED LIBRARIES
# ============================================================
import serial
import numpy as np
import joblib
import pandas as pd
from datetime import datetime
import time
import sys
import os
from collections import deque
import platform
import requests

print("\n" + "="*120)
print("BATTERY STATE OF CHARGE PREDICTION SYSTEM")
print("Step 4: Real-Time Monitoring from ESP32")
print("="*120)

# ============================================================
# SECTION 1: LOAD TRAINED MODEL AND SCALER
# ============================================================
print("\n[1/8] Loading trained model and scaler...")

try:
    rf_model = joblib.load('soc_model.pkl')
    scaler = joblib.load('scaler.pkl')
    print(f"      ✓ Random Forest model loaded successfully")
    print(f"      ✓ Feature scaler loaded successfully")
    model_loaded = True
except FileNotFoundError as e:
    print(f"      ✗ Error: {e}")
    print(f"      Please ensure 'soc_model.pkl' and 'scaler.pkl' exist")
    print(f"      Run 'step3_train_model.py' first!")
    model_loaded = False
    sys.exit(1)

# ============================================================
# SECTION 2: DEFINE BATTERY PARAMETERS
# ============================================================
print("\n[2/8] Setting battery parameters...")

# Battery chemistry: LiPo/Li-ion 3.7V nominal
BATTERY_CAPACITY    = 2.0   # 2000 mAh = 2.0 Ah
BATTERY_MIN_VOLTAGE = 3.0   # 0% SOC voltage (empty)
BATTERY_MAX_VOLTAGE = 4.2   # 100% SOC voltage (full)
NOMINAL_VOLTAGE     = 3.7   # Nominal Li-ion voltage

print(f"      Battery Capacity: {BATTERY_CAPACITY} Ah (2000 mAh)")
print(f"      Voltage Range: {BATTERY_MIN_VOLTAGE}V - {BATTERY_MAX_VOLTAGE}V")
print(f"      Chemistry: Li-ion (3.7V nominal)")

# ============================================================
# SECTION 3: DEFINE OPERATING THRESHOLDS
# ============================================================
print("\n[3/8] Setting operating thresholds...")

# Current thresholds (for mode detection)
CHARGING_CURRENT_THRESHOLD  =  0.01    # > 10mA  = charging
DISCHARGE_CURRENT_THRESHOLD = -0.01    # < -10mA = discharging
TRICKLE_CURRENT             =  0.005   # 5mA     = float/idle threshold

# Voltage thresholds (for fault detection)
VOLTAGE_DROP_THRESHOLD = 0.5           # Sudden drop > 0.5V = fault
NORMAL_VOLTAGE_MIN     = 3.0           # Below 3.0V = fault
NORMAL_VOLTAGE_MAX     = 4.3           # Above 4.3V = fault

# SOC thresholds (for alerts)
SOC_CRITICAL = 10.0                    # Below 10% = critical
SOC_LOW      = 20.0                    # Below 20% = low
SOC_HIGH     = 80.0                    # Above 80% = high
SOC_FULL     = 95.0                    # Above 95% = fully charged

print(f"      Current Thresholds: {CHARGING_CURRENT_THRESHOLD*1000:.1f}mA (charge), "
      f"{DISCHARGE_CURRENT_THRESHOLD*1000:.1f}mA (discharge)")
print(f"      Voltage Thresholds: {NORMAL_VOLTAGE_MIN}V (min), {NORMAL_VOLTAGE_MAX}V (max)")
print(f"      SOC Alerts: {SOC_CRITICAL}% (critical), {SOC_LOW}% (low), {SOC_HIGH}% (high)")

# ============================================================
# FIREBASE CONFIGURATION
# ============================================================
# Project ID: esp32-led-7e8fb
FIREBASE_URL = "https://esp32-led-7e8fb-default-rtdb.firebaseio.com/battery.json"

def sync_to_firebase(data):
    """Push battery data to Firebase Realtime Database."""
    try:
        response = requests.patch(FIREBASE_URL, json=data, timeout=3)
        if response.status_code == 200:
            print(f"  📡 Cloud Sync: Success")
        else:
            print(f"  📡 Cloud Sync: HTTP {response.status_code}")
    except Exception as e:
        print(f"  📡 Cloud Sync: Failed ({e})")

# ============================================================
# SECTION 4: SETUP SERIAL CONNECTION
# ============================================================
print("\n[4/8] Setting up serial connection with ESP32...")

# Define serial parameters
SERIAL_PORT = 'COM5'          # *** CHANGE TO YOUR PORT ***
BAUD_RATE   = 115200
TIMEOUT     = 2

print(f"      Port: {SERIAL_PORT}")
print(f"      Baud Rate: {BAUD_RATE}")
print(f"      Timeout: {TIMEOUT}s")

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
    print(f"      ✓ Connected to {SERIAL_PORT}!")
    time.sleep(2)  # Wait for ESP32 to initialize
    connection_successful = True
except Exception as e:
    print(f"      ✗ Connection failed: {e}")
    print(f"      Available ports: Check Device Manager (Windows) or ls /dev/tty* (Linux/Mac)")
    connection_successful = False
    sys.exit(1)

# ============================================================
# SECTION 5: WAIT FOR DATA HEADER
# ============================================================
print("\n[5/8] Waiting for data header from ESP32...")

header_found   = False
timeout_counter = 0
max_timeout    = 30

while not header_found and timeout_counter < max_timeout:
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').strip()
        if ',' in line and 'cycle' in line.lower():
            header_found = True
            print(f"      ✓ Header received!")
            print(f"      ✓ Data format: {line}")
    else:
        timeout_counter += 1
        if timeout_counter % 5 == 0:
            print(f"      Waiting... {timeout_counter}s (will timeout at {max_timeout}s)")
        time.sleep(1)

if not header_found:
    print(f"      ✗ No header received from ESP32!")
    print(f"      Check that:")
    print(f"        1. ESP32 code is uploaded and running")
    print(f"        2. USB cable is connected")
    print(f"        3. COM port is correct")
    ser.close()
    sys.exit(1)

# ============================================================
# SECTION 6: INITIALIZE DATA STRUCTURES
# ============================================================
print("\n[6/8] Initializing data tracking structures...")

predictions_log = []

voltage_history = deque(maxlen=10)
current_history = deque(maxlen=10)
soc_history     = deque(maxlen=10)
power_history   = deque(maxlen=10)

sample_count   = 0
start_time     = datetime.now()

last_voltage   = None
last_soc       = None
last_mode      = "IDLE"
last_timestamp = None

total_charged    = 0.0
total_discharged = 0.0
total_energy     = 0.0
max_soc     = 0.0
min_soc     = 100.0
max_voltage = 0.0
min_voltage = 5.0
max_current = 0.0
min_current = 0.0

mode_counts = {'CHARGING': 0, 'DISCHARGING': 0, 'IDLE': 0, 'FAULT': 0}

print(f"      ✓ Data structures initialized")
print(f"      ✓ Ready for real-time predictions")

# ============================================================
# SECTION 7: DISPLAY COLUMN HEADERS
# ============================================================
print("\n" + "="*140)
print("REAL-TIME BATTERY MONITORING")
print("="*140)
print(f"{'Time':<20} {'Mode':<12} {'Cyc':<5} {'Volt':<10} {'Curr':<12} "
      f"{'Pwr':<10} {'ML SOC':<10} {'Coulomb':<10} {'Final':<10} {'Status':<35}")
print("-"*140)

# ============================================================
# SECTION 8: MAIN PREDICTION LOOP
# ============================================================

try:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()

            # Skip empty and non-data lines
            if not line or ',' not in line or 'cycle' in line.lower() or '>>>' in line:
                continue

            try:
                # ====== PARSE DATA ======
                parts = line.split(',')
                if len(parts) != 4:
                    continue

                cycle   = float(parts[0])
                voltage = float(parts[1])
                current = float(parts[2])
                power   = float(parts[3])

                timestamp    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                current_time = datetime.now()

                # ====== VALIDATION: CHECK VOLTAGE RANGE ======
                if voltage < NORMAL_VOLTAGE_MIN or voltage > NORMAL_VOLTAGE_MAX:
                    status        = "⚠️  FAULT: Voltage out of range"
                    mode          = "FAULT"
                    soc_percent   = 0.0
                    ml_soc        = 0.0
                    coulomb_soc   = 0.0
                    current_ma    = current * 1000

                    predictions_log.append({
                        'timestamp': timestamp,
                        'cycle': int(cycle),
                        'voltage': voltage,
                        'current': current,
                        'current_mA': current_ma,
                        'power': power,
                        'mode': mode,
                        'ml_soc': ml_soc,
                        'coulomb_soc': coulomb_soc,
                        'soc': soc_percent / 100,
                        'soc_percent': soc_percent,
                        'status': status
                    })

                    print(f"{timestamp} {mode:<12} {int(cycle):<5} {voltage:>8.3f}V "
                          f"{current_ma:>10.2f}mA {power:>8.6f}W {ml_soc:>8.1f}% "
                          f"{coulomb_soc:>8.1f}% {soc_percent:>8.1f}% {status:<35}")

                    # Firebase sync for fault
                    sync_to_firebase({
                        "voltage": round(voltage, 3),
                        "current": round(current_ma, 2),
                        "soc": round(soc_percent, 1),
                        "mode": mode,
                        "status": status,
                        "last_updated": datetime.now().strftime("%H:%M:%S")
                    })

                    last_voltage = voltage
                    mode_counts[mode] += 1
                    sample_count += 1
                    continue

                # ====== DETECTION: SUDDEN VOLTAGE DROP ======
                if last_voltage is not None:
                    voltage_drop = last_voltage - voltage
                    if voltage_drop > VOLTAGE_DROP_THRESHOLD:
                        status      = "⚠️  ALERT: Sudden voltage drop detected!"
                        mode        = "FAULT"
                        soc_percent = 0.0
                        ml_soc      = 0.0
                        coulomb_soc = 0.0
                        current_ma  = current * 1000

                        print(f"{timestamp} {mode:<12} {int(cycle):<5} {voltage:>8.3f}V "
                              f"{current_ma:>10.2f}mA {power:>8.6f}W {ml_soc:>8.1f}% "
                              f"{coulomb_soc:>8.1f}% {soc_percent:>8.1f}% {status:<35}")

                        # Firebase sync for voltage drop fault
                        sync_to_firebase({
                            "voltage": round(voltage, 3),
                            "current": round(current_ma, 2),
                            "soc": round(soc_percent, 1),
                            "mode": mode,
                            "status": status,
                            "last_updated": datetime.now().strftime("%H:%M:%S")
                        })

                        last_voltage = voltage
                        mode_counts[mode] += 1
                        sample_count += 1
                        continue

                # ====== MODE DETECTION ======
                if current > CHARGING_CURRENT_THRESHOLD:
                    mode             = "CHARGING"
                    charge_increment = (current / BATTERY_CAPACITY) * (5 / 3600)   # 5s interval

                elif current < DISCHARGE_CURRENT_THRESHOLD:
                    mode             = "DISCHARGING"
                    charge_increment = (current / BATTERY_CAPACITY) * (5 / 3600)   # Negative

                else:
                    mode             = "IDLE"
                    charge_increment = 0

                # ====== SOC ESTIMATION: COULOMB COUNTING ======
                if last_soc is None:
                    # First sample: voltage-based initial estimate
                    coulomb_soc = (voltage - BATTERY_MIN_VOLTAGE) / (BATTERY_MAX_VOLTAGE - BATTERY_MIN_VOLTAGE)
                    coulomb_soc = np.clip(coulomb_soc, 0, 1)
                else:
                    coulomb_soc = last_soc + charge_increment
                    coulomb_soc = np.clip(coulomb_soc, 0, 1)

                # ====== SOC PREDICTION: MACHINE LEARNING ======
                features        = pd.DataFrame([[cycle, voltage, current, power]],
                                               columns=['cycle', 'voltage', 'current', 'power'])
                features_scaled = scaler.transform(features)
                ml_soc          = rf_model.predict(features_scaled)[0]
                ml_soc          = np.clip(ml_soc, 0, 1)

                # ====== HYBRID SOC ESTIMATION ======
                # 70% ML + 30% Coulomb counting
                soc_final   = 0.7 * ml_soc + 0.3 * coulomb_soc
                soc_final   = np.clip(soc_final, 0, 1)
                soc_percent = soc_final * 100

                # ====== UPDATE STATISTICS ======
                if charge_increment > 0:
                    total_charged += charge_increment
                    total_energy  += power * (5 / 3600)
                elif charge_increment < 0:
                    total_discharged += abs(charge_increment)
                    total_energy     += abs(power * (5 / 3600))

                max_soc     = max(max_soc, soc_percent)
                min_soc     = min(min_soc, soc_percent)
                max_voltage = max(max_voltage, voltage)
                min_voltage = min(min_voltage, voltage)
                max_current = max(max_current, abs(current))
                min_current = min(min_current, current)

                # ====== DETERMINE STATUS MESSAGE ======
                if mode == "CHARGING":
                    if soc_percent >= 99.0:
                        status = "✓ FULLY CHARGED"
                    elif soc_percent >= SOC_HIGH:
                        status = f"✓ Charging ({soc_percent:.0f}%)"
                    else:
                        status = "↑ Charging..."

                elif mode == "DISCHARGING":
                    if soc_percent <= SOC_CRITICAL:
                        status = "⚠️  CRITICAL: Low battery!"
                    elif soc_percent <= SOC_LOW:
                        status = f"⚠️  Low battery ({soc_percent:.0f}%)"
                    else:
                        status = "↓ Discharging..."

                else:  # IDLE
                    if soc_percent >= SOC_FULL:
                        status = "✓ Fully charged (idle)"
                    elif soc_percent <= 5.0:
                        status = "⚠️  Nearly empty (idle)"
                    else:
                        status = "= Idle"

                # ====== DISPLAY REAL-TIME DATA ======
                current_ma       = current * 1000
                ml_soc_percent   = ml_soc * 100
                coulomb_soc_pct  = coulomb_soc * 100

                print(f"{timestamp} {mode:<12} {int(cycle):<5} {voltage:>8.3f}V "
                      f"{current_ma:>10.2f}mA {power:>8.6f}W {ml_soc_percent:>8.1f}% "
                      f"{coulomb_soc_pct:>8.1f}% {soc_percent:>8.1f}% {status:<35}")

                # ====== LOG DATA TO MEMORY ======
                predictions_log.append({
                    'timestamp':   timestamp,
                    'cycle':       int(cycle),
                    'voltage':     voltage,
                    'current':     current,
                    'current_mA':  current_ma,
                    'power':       power,
                    'mode':        mode,
                    'ml_soc':      ml_soc_percent,
                    'coulomb_soc': coulomb_soc_pct,
                    'soc':         soc_final,
                    'soc_percent': soc_percent,
                    'status':      status
                })

                # ====== FIREBASE CLOUD SYNC ======
                sync_to_firebase({
                    "voltage":      round(voltage, 3),
                    "current":      round(current_ma, 2),
                    "soc":          round(soc_percent, 1),
                    "mode":         mode,
                    "status":       status,
                    "last_updated": datetime.now().strftime("%H:%M:%S")
                })

                # ====== UPDATE HISTORIES ======
                voltage_history.append(voltage)
                current_history.append(current)
                soc_history.append(soc_percent)
                power_history.append(power)

                # ====== UPDATE TRACKING VARIABLES ======
                last_voltage = voltage
                last_soc     = soc_final
                last_mode    = mode
                last_timestamp = timestamp
                mode_counts[mode] += 1
                sample_count += 1

                # ====== PERIODIC SAVE (Every 20 samples) ======
                if sample_count % 20 == 0 and sample_count > 0:
                    df_log = pd.DataFrame(predictions_log)
                    df_log.to_csv('soc_predictions_live.csv', index=False)
                    elapsed = (datetime.now() - start_time).total_seconds()
                    print(f"\n[SAVE] {sample_count} samples collected | {elapsed:.0f}s elapsed | "
                          f"Current SOC: {soc_percent:.1f}% | Mode: {mode}")
                    print(f"{'Time':<20} {'Mode':<12} {'Cyc':<5} {'Volt':<10} {'Curr':<12} "
                          f"{'Pwr':<10} {'ML SOC':<10} {'Coulomb':<10} {'Final':<10} {'Status':<35}")
                    print("-"*140)

            except ValueError:
                continue
            except Exception:
                continue

# ============================================================
# SECTION 9: HANDLE KEYBOARD INTERRUPT (Ctrl+C)
# ============================================================
except KeyboardInterrupt:
    print(f"\n\n{'='*140}")
    print("STOPPING REAL-TIME MONITORING")
    print(f"{'='*140}")

    ser.close()
    print("\n✓ Serial connection closed")

    # ============================================================
    # SECTION 10: SAVE FINAL DATA AND GENERATE REPORT
    # ============================================================

    if predictions_log:
        df_log = pd.DataFrame(predictions_log)
        df_log.to_csv('soc_predictions_final.csv', index=False)

        elapsed_time    = (datetime.now() - start_time).total_seconds()
        elapsed_minutes = elapsed_time / 60
        elapsed_hours   = elapsed_minutes / 60
        sampling_rate   = sample_count / elapsed_time if elapsed_time > 0 else 0

        print(f"\n{'='*140}")
        print("📊 SESSION SUMMARY STATISTICS")
        print(f"{'='*140}\n")

        print("SESSION DURATION:")
        print(f"  Total Time: {elapsed_time:.1f} seconds ({elapsed_minutes:.2f} minutes, {elapsed_hours:.3f} hours)")
        print(f"  Total Samples: {len(df_log)}")
        print(f"  Sampling Rate: {sampling_rate:.2f} samples/second")

        print(f"\n📈 STATE OF CHARGE (SOC) STATISTICS:")
        print(f"  Current SOC: {df_log['soc_percent'].iloc[-1]:.1f}%")
        print(f"  Maximum SOC: {df_log['soc_percent'].max():.1f}%")
        print(f"  Minimum SOC: {df_log['soc_percent'].min():.1f}%")
        print(f"  Average SOC: {df_log['soc_percent'].mean():.1f}%")
        print(f"  Median SOC:  {df_log['soc_percent'].median():.1f}%")
        print(f"  SOC Range:   {df_log['soc_percent'].max() - df_log['soc_percent'].min():.1f}%")
        print(f"  Std Dev:     {df_log['soc_percent'].std():.1f}%")

        print(f"\n⚡ VOLTAGE STATISTICS:")
        print(f"  Minimum: {df_log['voltage'].min():.4f}V")
        print(f"  Maximum: {df_log['voltage'].max():.4f}V")
        print(f"  Average: {df_log['voltage'].mean():.4f}V")
        print(f"  Median:  {df_log['voltage'].median():.4f}V")
        print(f"  Range:   {df_log['voltage'].max() - df_log['voltage'].min():.4f}V")

        print(f"\n⏱️  CURRENT STATISTICS:")
        print(f"  Minimum: {df_log['current_mA'].min():.2f}mA")
        print(f"  Maximum: {df_log['current_mA'].max():.2f}mA")
        print(f"  Average: {df_log['current_mA'].mean():.2f}mA")
        print(f"  Median:  {df_log['current_mA'].median():.2f}mA")

        print(f"\n🔋 ENERGY CHARGING STATISTICS:")
        print(f"  Total Charged:    {total_charged:.4f} Ah ({total_charged*1000:.1f} mAh)")
        print(f"  Total Discharged: {total_discharged:.4f} Ah ({total_discharged*1000:.1f} mAh)")
        net = total_charged - total_discharged
        print(f"  Net Change:       {net:.4f} Ah ({net*1000:.1f} mAh)")
        print(f"  Total Energy:     {total_energy:.3f} Wh")

        print(f"\n📋 OPERATING MODE DISTRIBUTION:")
        total_samples = len(df_log)
        for mode_name in ['CHARGING', 'DISCHARGING', 'IDLE', 'FAULT']:
            count      = mode_counts[mode_name]
            percentage = (count / total_samples * 100) if total_samples > 0 else 0
            bar_length = int(percentage / 2)
            bar        = '█' * bar_length + '░' * (50 - bar_length)
            print(f"  {mode_name:<12}: {count:>4} samples ({percentage:>5.1f}%) {bar}")

        print(f"\n🎯 SOC LEVEL DISTRIBUTION:")
        soc_critical_cnt = len(df_log[df_log['soc_percent'] <= SOC_CRITICAL])
        soc_low_cnt      = len(df_log[(df_log['soc_percent'] > SOC_CRITICAL) & (df_log['soc_percent'] <= SOC_LOW)])
        soc_medium_cnt   = len(df_log[(df_log['soc_percent'] > SOC_LOW)      & (df_log['soc_percent'] < SOC_HIGH)])
        soc_high_cnt     = len(df_log[df_log['soc_percent'] >= SOC_HIGH])

        print(f"  Critical (≤10%):  {soc_critical_cnt} samples ({soc_critical_cnt/total_samples*100:.1f}%)")
        print(f"  Low (10-20%):     {soc_low_cnt} samples ({soc_low_cnt/total_samples*100:.1f}%)")
        print(f"  Medium (20-80%):  {soc_medium_cnt} samples ({soc_medium_cnt/total_samples*100:.1f}%)")
        print(f"  High (≥80%):      {soc_high_cnt} samples ({soc_high_cnt/total_samples*100:.1f}%)")

        print(f"\n📁 FILES SAVED:")
        print(f"  ✓ soc_predictions_final.csv (Complete session data — {len(df_log)} records)")
        print(f"  ✓ soc_predictions_live.csv  (Latest snapshot)")

        print(f"\n{'='*140}")
        print("SAMPLE DATA (First 10 Records):")
        print(f"{'='*140}")
        print(df_log[['timestamp', 'mode', 'voltage', 'current_mA',
                       'ml_soc', 'coulomb_soc', 'soc_percent', 'status']].head(10).to_string(index=False))

        if len(df_log) > 10:
            print(f"\n... and {len(df_log) - 10} more records (see soc_predictions_final.csv)")

        print(f"\n{'='*140}")
        print("✓ SESSION COMPLETE — ALL DATA SAVED")
        print(f"{'='*140}\n")

# ============================================================
# SECTION 11: FINAL CLEANUP
# ============================================================

print("\n" + "="*140)
print("GOODBYE! Your battery SOC monitoring session has ended successfully.")
print("="*140 + "\n")
