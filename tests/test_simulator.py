import pytest
from datetime import datetime

# Symulacja Twojej funkcji generującej dane
def generate_sensor_data(device_id, temperature, humidity, pressure):
    return {
        "deviceId": device_id,
        "temperature": round(temperature, 2),
        "humidity": round(humidity, 2),
        "pressure": round(pressure, 2),
        "timestamp": datetime.now().isoformat()
    }

def test_sensor_data_format():
    data = generate_sensor_data("sensor_01", 22.556, 45.2, 1013.1)
    
    # Testy struktury
    assert "deviceId" in data [cite: 96]
    assert data["temperature"] == 22.56  # sprawdza zaokrąglenie
    assert isinstance(data["timestamp"], str) [cite: 138]

def test_values_range():
    data = generate_sensor_data("sensor_01", 25.0, 50.0, 1010.0)
    # Testy logiczne (np. czy temperatura nie jest fizycznie niemożliwa)
    assert -50 < data["temperature"] < 100
    assert 0 <= data["humidity"] <= 100