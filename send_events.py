import asyncio
import json
import random
import time
from datetime import datetime, timezone
from azure.eventhub import EventHubProducerClient, EventData


CONNECTION_STR = "TWÓJ KLUCZ"
EVENTHUB_NAME = "input-stream-projekt"

NUM_DEVICES = 10           # liczba czujników
SEND_INTERVAL = 1          # sekundy
ANOMALY_PROBABILITY = 0.05 # 5% anomalii

# async def run():
#     producer = EventHubProducerClient.from_connection_string(
#         conn_str=CONNECTION_STR,
#         eventhub_name=EVENTHUB_NAME
#     )

#     async with producer:
#         while True:
#             event_body = {
#                 "deviceId": f"sensor_{random.randint(1, 5)}",
#                 "temperature": round(random.uniform(15.0, 25.0), 2),
#                 "timestamp": datetime.utcnow().isoformat()
#             }

#             batch = await producer.create_batch()
#             batch.add(EventData(json.dumps(event_body)))
#             await producer.send_batch(batch)

#             print(f"Sent: {event_body}")
#             await asyncio.sleep(1)

# asyncio.run(run())

#==================
# GENERATOR DANYCH
def generate_sensor_data(device_id: str):
    temperature = random.normalvariate(22, 2)
    humidity = random.normalvariate(50, 5)
    pressure = random.normalvariate(1013, 10)

    # losowa anomalia
    if random.random() < ANOMALY_PROBABILITY:
        temperature += random.choice([20, 30])

    return {
        "deviceId": device_id,
        "temperature": round(temperature, 2),
        "humidity": round(humidity, 2),
        "pressure": round(pressure, 2),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ========
# PRODUCER
def main():
    producer = EventHubProducerClient.from_connection_string(
        conn_str=CONNECTION_STR,
        eventhub_name=EVENTHUB_NAME
    )

    print("IoT Simulator started...")

    with producer:
        while True:
            event_batch = producer.create_batch()

            for i in range(NUM_DEVICES):
                device_id = f"sensor-{i:02d}"
                data = generate_sensor_data(device_id)
                event_batch.add(EventData(json.dumps(data)))

            producer.send_batch(event_batch)
            print(f"Sent batch with {NUM_DEVICES} events")

            time.sleep(SEND_INTERVAL)

if __name__ == "__main__":
    main()
