"""
Synthetic Dataset Generator and AI Model Trainer for Mandi Operational Capacity & Queue Prediction.
"""
import random
import json
import os

def generate_synthetic_mandi_data(samples=500):
    dataset = []
    crops = ["wheat", "paddy", "cotton", "pulses", "maize"]
    weather_types = ["Sunny", "Cloudy", "Rainy"]

    for i in range(samples):
        capacity = random.randint(100, 500)
        distance = round(random.uniform(2.0, 45.0), 1)
        crop = random.choice(crops)
        weather = random.choice(weather_types)
        booked = random.randint(20, capacity)
        
        # Target wait time calculation formula
        base_wait = (booked / capacity) * 45
        if weather == "Rainy":
            base_wait *= 0.6 # Rain delays arrivals
        elif weather == "Sunny":
            base_wait *= 1.1

        dataset.append({
            "sample_id": i + 1,
            "mandi_capacity": capacity,
            "travel_distance_km": distance,
            "crop_type": crop,
            "weather": weather,
            "current_booked": booked,
            "target_predicted_wait_minutes": max(5, int(base_wait))
        })

    model_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(model_dir, "mandi_training_data.json")
    with open(data_path, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"Generated {samples} training data records at: {data_path}")
    return data_path

if __name__ == "__main__":
    generate_synthetic_mandi_data()
