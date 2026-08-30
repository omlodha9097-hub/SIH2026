"""
Integration Test Suite for Mandi Procurement & AI Queue Management Platform.
"""
import unittest
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_db_connection
from geofence import verify_geofence, haversine_distance
from pfms_mock import process_dbt_payment, get_pfms_status
from ai.predictor import MandiPredictiveScheduler
from voice.voice_service import MultilingualVoiceBot

class TestMandiProcurementPlatform(unittest.TestCase):

    def setUp(self):
        init_db()
        self.scheduler = MandiPredictiveScheduler()
        self.voice_bot = MultilingualVoiceBot()

    def test_database_initialization(self):
        conn = get_db_connection()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        table_names = [t[0] for t in tables]
        conn.close()

        self.assertIn("farmers", table_names)
        self.assertIn("mandis", table_names)
        self.assertIn("slots", table_names)
        self.assertIn("tokens", table_names)
        self.assertIn("quality_gradings", table_names)
        self.assertIn("pfms_transactions", table_names)

    def test_geofencing_haversine(self):
        # Pune Mandi Gate (18.5204, 73.8567)
        # Farmer 1 inside 500m perimeter (18.5215, 73.8572 -> ~170m)
        res_inside = verify_geofence(18.5215, 73.8572, 18.5204, 73.8567, threshold_meters=500.0)
        self.assertTrue(res_inside["is_within_geofence"])
        self.assertLess(res_inside["distance_meters"], 500.0)

        # Farmer 2 outside perimeter (18.5400, 73.8800 -> ~3.3km)
        res_outside = verify_geofence(18.5400, 73.8800, 18.5204, 73.8567, threshold_meters=500.0)
        self.assertFalse(res_outside["is_within_geofence"])
        self.assertGreater(res_outside["distance_meters"], 500.0)

    def test_ml_predictive_scheduler(self):
        slots = self.scheduler.predict_optimal_slots(
            mandi_max_capacity=300,
            current_booked_count=50,
            crop_type="wheat",
            travel_distance_km=10.0
        )
        self.assertGreater(len(slots), 0)
        for s in slots:
            self.assertIn("time_slot", s)
            self.assertIn("predicted_wait_minutes", s)
            self.assertIn("congestion_status", s)

    def test_multilingual_voice_bot(self):
        # Hindi query
        hi = self.voice_bot.process_voice_input("मुझे गेहूं टोकन चाहिए", language="hi")
        self.assertEqual(hi["detected_intent"], "BOOK_SLOT")
        self.assertEqual(hi["extracted_crop"], "Wheat")

        # Marathi query
        mr = self.voice_bot.process_voice_input("माझ्या टोकनची काय स्थिती आहे", language="mr")
        self.assertEqual(mr["detected_intent"], "CHECK_STATUS")

    def test_pfms_payment_mock(self):
        pay = process_dbt_payment(farmer_id=1, slot_id=10, amount=91000.00, farmer_name="Ramesh Patil")
        self.assertEqual(pay["status"], "APPROVED")
        self.assertTrue(pay["pfms_ref_no"].startswith("PFMS-2026-"))
        self.assertEqual(pay["amount_inr"], 91000.00)

        st = get_pfms_status(pay["pfms_ref_no"])
        self.assertEqual(st["status"], "CREDITED")

if __name__ == '__main__':
    unittest.main()
