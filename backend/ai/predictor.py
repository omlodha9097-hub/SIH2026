import math
import random

class MandiPredictiveScheduler:
    """
    ML Predictive Scheduling Engine for Mandi Token Capacity & Overcrowding Prevention.
    Inputs: Mandi operational capacity, travel distance, crop type, weather forecast, harvest season index.
    Outputs: Hourly token capacity limits, recommended optimal slot, predicted queue wait time (minutes).
    """

    def __init__(self):
        self.crop_weights = {
            "wheat": 1.2,       # Heavy bulk arrival
            "paddy": 1.3,       # High volume
            "cotton": 1.0,      # Moderate volume
            "pulses": 0.8,      # Medium volume
            "maize": 1.1,       # High volume
            "oilseeds": 0.9     # Medium volume
        }

        self.hourly_baseline_traffic = {
            "08:00 - 09:00": 0.95,  # Morning peak
            "09:00 - 10:00": 1.00,  # Highest peak
            "10:00 - 11:00": 0.90,
            "11:00 - 12:00": 0.75,
            "12:00 - 13:00": 0.50,  # Lunch period
            "13:00 - 14:00": 0.60,
            "14:00 - 15:00": 0.70,  # Afternoon batch
            "15:00 - 16:00": 0.40
        }

    def predict_optimal_slots(self, mandi_max_capacity: int, current_booked_count: int, crop_type: str, travel_distance_km: float, weather_forecast: str = "Sunny"):
        """
        Calculates optimal token distribution across time slots to prevent overcrowding.
        """
        crop_factor = self.crop_weights.get(crop_type.lower(), 1.0)
        
        # Weather penalty: Rain reduces transport, Sunny increases rush
        weather_multiplier = 1.15 if weather_forecast.lower() == "sunny" else 0.70

        recommendations = []
        for time_slot, traffic_ratio in self.hourly_baseline_traffic.items():
            # Calculate predicted load factor
            slot_capacity_limit = int((mandi_max_capacity / len(self.hourly_baseline_traffic)) * (1.5 - traffic_ratio * 0.4))
            
            # Simulated current slot occupancy
            booked_in_slot = random.randint(3, max(4, int(slot_capacity_limit * 0.75)))
            available_tokens = max(0, slot_capacity_limit - booked_in_slot)
            
            # Predict queue wait time in minutes
            wait_time_minutes = round((booked_in_slot / max(1, slot_capacity_limit)) * 35 * crop_factor * weather_multiplier)
            
            # Congestion rating
            if wait_time_minutes < 15:
                congestion_status = "LOW"
                badge_color = "#10b981" # Green
            elif wait_time_minutes < 25:
                congestion_status = "MODERATE"
                badge_color = "#f59e0b" # Yellow
            else:
                congestion_status = "HIGH"
                badge_color = "#ef4444" # Red

            recommendations.append({
                "time_slot": time_slot,
                "max_capacity": slot_capacity_limit,
                "booked_tokens": booked_in_slot,
                "available_tokens": available_tokens,
                "predicted_wait_minutes": wait_time_minutes,
                "congestion_status": congestion_status,
                "badge_color": badge_color,
                "is_recommended": congestion_status in ["LOW", "MODERATE"] and available_tokens > 0
            })

        return recommendations

    def predict_wait_time(self, mandi_capacity: int, active_geofenced_tokens: int, crop_type: str) -> int:
        """Predicts wait time for an arriving tractor based on active geofenced tokens."""
        crop_factor = self.crop_weights.get(crop_type.lower(), 1.0)
        processing_rate_per_hour = max(10, mandi_capacity // 8) # average 8-hour shift
        wait_hours = (active_geofenced_tokens * crop_factor) / processing_rate_per_hour
        return max(5, int(wait_hours * 60))

if __name__ == "__main__":
    scheduler = MandiPredictiveScheduler()
    rec = scheduler.predict_optimal_slots(mandi_max_capacity=200, current_booked_count=120, crop_type="wheat", travel_distance_km=15.5)
    print("AI Slot Recommendations:")
    for r in rec:
        print(f"Slot: {r['time_slot']} | Wait: {r['predicted_wait_minutes']}m | Status: {r['congestion_status']} | Avail: {r['available_tokens']}")
