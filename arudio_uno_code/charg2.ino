// ============================================================
// ESP32 Battery Monitor with INA219
// FIXED VERSION - With explicit cycle counting
// ============================================================

#include <Wire.h>
#include <Adafruit_INA219.h>

Adafruit_INA219 ina219;

// ============================================================
// VARIABLES - INITIALIZE OUTSIDE OF LOOP
// ============================================================
uint32_t cycle = 1;
uint32_t sample_count = 0;

// TESTING MODE - Short cycle for quick testing
#define SAMPLES_PER_CYCLE 5      // Change cycle every 5 samples
#define SAMPLING_INTERVAL 2000   // 2 seconds

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("\n===========================================");
  Serial.println("ESP32 Battery Monitor with INA219");
  Serial.println("===========================================\n");
  
  Wire.begin(21, 22);
  Serial.println("I2C: SDA=21, SCL=22");
  
  Serial.print("INA219 Init: ");
  if (!ina219.begin()) {
    Serial.println("FAILED!");
    while (1) delay(100);
  }
  Serial.println("SUCCESS");
  
  ina219.setCalibration_16V_400mA();
  
  Serial.println("\nSettings:");
  Serial.print("  Samples per cycle: ");
  Serial.println(SAMPLES_PER_CYCLE);
  Serial.print("  Sampling interval: ");
  Serial.print(SAMPLING_INTERVAL);
  Serial.println("ms\n");
  
  Serial.println("cycle,voltage,current,power");
}

void loop() {
  // Read sensor data
  float busVoltage_V = ina219.getBusVoltage_V();
  float current_mA = ina219.getCurrent_mA();
  float current_A = current_mA / 1000.0;
  float power_W = busVoltage_V * current_A;
  
  // Send CSV data
  Serial.print(cycle);
  Serial.print(",");
  Serial.print(busVoltage_V, 4);
  Serial.print(",");
  Serial.print(current_A, 6);
  Serial.print(",");
  Serial.println(power_W, 6);
  
  // Increment sample counter
  sample_count = sample_count + 1;
  
  // Check if we should change cycle
  if (sample_count >= SAMPLES_PER_CYCLE) {
    // Print cycle change notification
    Serial.print(">>> CYCLE CHANGE: ");
    Serial.print(cycle);
    Serial.print(" -> ");
    cycle = cycle + 1;
    Serial.println(cycle);
    
    // Reset sample counter
    sample_count = 0;
  }
  
  // Wait before next sample
  delay(SAMPLING_INTERVAL);
}