import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3
import random
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_db_connection
from geofence import verify_geofence
from pfms_mock import process_dbt_payment, get_pfms_status
from ai.predictor import MandiPredictiveScheduler
from voice.voice_service import MultilingualVoiceBot

# Global AI & Voice Instances
scheduler = MandiPredictiveScheduler()
voice_bot = MultilingualVoiceBot()

class MandiAPIHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Type", content_type)
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def _read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            return json.loads(body)
        except Exception:
            return {}

    def _send_json(self, data, status=200):
        self._set_headers(status, "application/json")
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _serve_file(self, filepath, content_type="text/html"):
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self._set_headers(200, content_type)
            self.wfile.write(content.encode('utf-8'))
        else:
            self._send_json({"error": "File not found", "path": filepath}, 404)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # Route static HTML web apps
        if path == "/" or path == "/index.html":
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            farmer_html = os.path.join(root_dir, "farmer-app", "index.html")
            self._serve_file(farmer_html)
            return

        elif path == "/farmer" or path == "/farmer/":
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            farmer_html = os.path.join(root_dir, "farmer-app", "index.html")
            self._serve_file(farmer_html)
            return

        elif path == "/admin" or path == "/admin/":
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            admin_html = os.path.join(root_dir, "admin-dashboard", "index.html")
            self._serve_file(admin_html)
            return

        # Serve static assets (images)
        elif path.startswith("/assets/"):
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_name = os.path.basename(path)
            asset_path = os.path.join(root_dir, "farmer-app", "assets", file_name)
            
            content_type = "image/jpeg"
            if file_name.endswith(".png"):
                content_type = "image/png"
            elif file_name.endswith(".svg"):
                content_type = "image/svg+xml"
            elif file_name.endswith(".js"):
                content_type = "application/javascript"
                
            if os.path.exists(asset_path):
                with open(asset_path, "rb") as f:
                    content = f.read()
                self._set_headers(200, content_type)
                self.wfile.write(content)
            else:
                self._send_json({"error": "Asset not found"}, 404)
            return


        # REST API Routes
        elif path == "/api/v1/mandis":
            conn = get_db_connection()
            mandis = conn.execute("SELECT * FROM mandis").fetchall()
            conn.close()
            self._send_json([dict(m) for m in mandis])

        elif path == "/api/v1/slots/recommendations":
            mandi_id = int(query.get("mandi_id", [1])[0])
            crop = query.get("crop", ["wheat"])[0]
            
            conn = get_db_connection()
            mandi = conn.execute("SELECT * FROM mandis WHERE id = ?", (mandi_id,)).fetchone()
            conn.close()

            max_cap = mandi["max_daily_capacity"] if mandi else 250
            recs = scheduler.predict_optimal_slots(
                mandi_max_capacity=max_cap,
                current_booked_count=45,
                crop_type=crop,
                travel_distance_km=12.5,
                weather_forecast="Sunny"
            )
            self._send_json({
                "mandi_id": mandi_id,
                "crop": crop,
                "ai_engine": "XGBoost Mandi Congestion Predictor v2.6",
                "recommended_slots": recs
            })

        elif path == "/api/v1/queue/live":
            mandi_id = int(query.get("mandi_id", [1])[0])
            conn = get_db_connection()
            
            slots = conn.execute('''
                SELECT s.*, f.name as farmer_name, f.mobile, f.aadhaar_hash, t.token_number, t.is_active, t.is_geofenced, t.distance_to_mandi_meters, q.grade, q.net_weight, q.total_payout, p.status as pfms_status, p.pfms_ref_no
                FROM slots s
                JOIN farmers f ON s.farmer_id = f.id
                LEFT JOIN tokens t ON s.id = t.slot_id
                LEFT JOIN quality_gradings q ON s.id = q.slot_id
                LEFT JOIN pfms_transactions p ON s.id = p.slot_id
                WHERE s.mandi_id = ?
                ORDER BY s.id DESC
            ''', (mandi_id,)).fetchall()
            conn.close()

            self._send_json([dict(s) for s in slots])

        elif path == "/api/v1/msp-rates":
            msp_data = [
                {"category": "Pulses", "crop": "Tur (Arhar)", "code": "tur", "msp_rate": 7000, "unit": "₹/Qtl"},
                {"category": "Pulses", "crop": "Chana (Gram)", "code": "chana", "msp_rate": 5440, "unit": "₹/Qtl"},
                {"category": "Pulses", "crop": "Masur (Lentil)", "code": "masur", "msp_rate": 6425, "unit": "₹/Qtl"},
                {"category": "Pulses", "crop": "Moong", "code": "moong", "msp_rate": 8558, "unit": "₹/Qtl"},
                {"category": "Pulses", "crop": "Urad", "code": "urad", "msp_rate": 6950, "unit": "₹/Qtl"},
                {"category": "Cereals", "crop": "Wheat", "code": "wheat", "msp_rate": 2275, "unit": "₹/Qtl"},
                {"category": "Cereals", "crop": "Paddy (Common)", "code": "paddy", "msp_rate": 2183, "unit": "₹/Qtl"},
                {"category": "Cereals", "crop": "Maize", "code": "maize", "msp_rate": 2090, "unit": "₹/Qtl"},
                {"category": "Oilseeds", "crop": "Soyabean", "code": "soyabean", "msp_rate": 4600, "unit": "₹/Qtl"},
                {"category": "Oilseeds", "crop": "Mustard", "code": "mustard", "msp_rate": 5650, "unit": "₹/Qtl"},
                {"category": "Commercial", "crop": "Cotton", "code": "cotton", "msp_rate": 6620, "unit": "₹/Qtl"}
            ]
            self._send_json(msp_data)

        elif path == "/api/v1/agmarknet/ticker":
            ticker_items = [
                "🌾 Pune APMC Mandi: Wheat ₹2,310/Qtl (+1.5%) | Daily Arrivals: 1,420 Qtl | Procurement Status: Active",
                "🫘 Latur APMC: Tur (Arhar) ₹7,150/Qtl | Daily Arrivals: 850 Qtl | MSP Rate: ₹7,000/Qtl (Procurement Live)",
                "🌾 Karnal Grain Mandi: Wheat ₹2,280/Qtl | Arrivals: 2,100 Qtl | DBT Direct Credit: Active",
                "🌻 Nashik APMC: Soyabean ₹4,650/Qtl | Arrivals: 980 Qtl | Quality Grade A: 88%",
                "🌱 Indore Market: Chana ₹5,520/Qtl (+1.2%) | Arrivals: 1,150 Qtl | e-Samridhi Linked"
            ]
            self._send_json({"ticker": ticker_items})

        elif path == "/api/v1/grievances":
            conn = get_db_connection()
            grievances = conn.execute("SELECT g.*, COALESCE(f.name, 'Ramesh Patil') as farmer_name, COALESCE(f.mobile, '9823411029') as mobile FROM grievances g LEFT JOIN farmers f ON g.farmer_id = f.id ORDER BY g.id DESC").fetchall()
            conn.close()
            self._send_json([dict(g) for g in grievances])

        else:
            self._send_json({"error": "Endpoint not found", "path": path}, 404)

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        body = self._read_json_body()

        if path == "/api/v1/seed":
            init_db()
            conn = get_db_connection()
            cursor = conn.cursor()

            # Seed Mandis
            cursor.execute("DELETE FROM mandis")
            cursor.execute("DELETE FROM farmers")
            cursor.execute("DELETE FROM slots")
            cursor.execute("DELETE FROM tokens")

            mandis_seed = [
                ("Pune Main APMC Mandi", "APMC-PUNE-01", 18.5204, 73.8567, 300, "Pune", "Maharashtra"),
                ("Nashik Grain Mandi", "APMC-NSK-02", 19.9975, 73.7898, 450, "Nashik", "Maharashtra"),
                ("Karnal Wheat Mandi", "APMC-KRN-03", 29.6857, 76.9905, 500, "Karnal", "Haryana")
            ]
            for m in mandis_seed:
                cursor.execute("INSERT INTO mandis (name, code, latitude, longitude, max_daily_capacity, city, state) VALUES (?, ?, ?, ?, ?, ?, ?)", m)
            
            # Seed Demo Farmer
            cursor.execute("INSERT INTO farmers (aadhaar_hash, name, mobile, state, district, crop_type, land_hectares) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           ("8492-3019-4810", "Ramesh Patil", "9823411029", "Maharashtra", "Pune", "Wheat", 4.5))
            farmer_id = cursor.lastrowid

            # Seed Active Slot
            token_code = f"TK-{random.randint(1000, 9999)}"
            cursor.execute("INSERT INTO slots (farmer_id, mandi_id, slot_date, hour_slot, allocated_crop_qty, crop_type, token_code, status, predicted_wait_minutes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (farmer_id, 1, "2026-08-27", "09:00 - 10:00", 50.0, "Wheat", token_code, "BOOKED", 12))
            slot_id = cursor.lastrowid

            cursor.execute("INSERT INTO tokens (slot_id, token_number, is_active, is_geofenced, distance_to_mandi_meters) VALUES (?, ?, ?, ?, ?)",
                           (slot_id, token_code, 0, 0, 1420.0))

            conn.commit()
            conn.close()

            self._send_json({"message": "Seed database populated successfully!", "farmer_id": farmer_id, "token_code": token_code})

        elif path == "/api/v1/farmers/register":
            name = body.get("name", "Farmer")
            mobile = body.get("mobile", "9999999999")
            aadhaar = body.get("aadhaar", "123456789012")
            state = body.get("state", "Maharashtra")
            district = body.get("district", "Pune")
            crop = body.get("crop_type", "Wheat")
            land = float(body.get("land_hectares", 2.0))

            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO farmers (aadhaar_hash, name, mobile, state, district, crop_type, land_hectares) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (aadhaar, name, mobile, state, district, crop, land))
                fid = cursor.lastrowid
                conn.commit()
                conn.close()
                self._send_json({"success": True, "farmer_id": fid, "name": name, "aadhaar_status": "VERIFIED_UIDAI_MOCK"})
            except sqlite3.IntegrityError:
                conn.close()
                self._send_json({"success": True, "farmer_id": 1, "name": name, "aadhaar_status": "VERIFIED_EXISTING"})

        elif path == "/api/v1/slots/book":
            farmer_id = int(body.get("farmer_id", 1))
            mandi_id = int(body.get("mandi_id", 1))
            slot_date = body.get("slot_date", "2026-08-27")
            hour_slot = body.get("hour_slot", "09:00 - 10:00")
            qty = float(body.get("crop_qty", 40.0))
            crop = body.get("crop_type", "Wheat")

            token_code = f"TK-{random.randint(1000, 9999)}"
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO slots (farmer_id, mandi_id, slot_date, hour_slot, allocated_crop_qty, crop_type, token_code, status, predicted_wait_minutes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (farmer_id, mandi_id, slot_date, hour_slot, qty, crop, token_code, "BOOKED", 15))
            slot_id = cursor.lastrowid

            cursor.execute("INSERT INTO tokens (slot_id, token_number, is_active, is_geofenced, distance_to_mandi_meters) VALUES (?, ?, ?, ?, ?)",
                           (slot_id, token_code, 0, 0, 2400.0))
            conn.commit()
            conn.close()

            self._send_json({
                "success": True,
                "slot_id": slot_id,
                "token_code": token_code,
                "hour_slot": hour_slot,
                "status": "BOOKED",
                "message": "Slot booked successfully! Head to Mandi and your token will auto-activate when within 500m."
            })

        elif path == "/api/v1/tokens/activate-geofence":
            slot_id = int(body.get("slot_id", 1))
            farmer_lat = float(body.get("latitude", 18.5210))
            farmer_lon = float(body.get("longitude", 73.8570))

            conn = get_db_connection()
            cursor = conn.cursor()
            slot = cursor.execute("SELECT s.*, m.latitude as mandi_lat, m.longitude as mandi_lng FROM slots s JOIN mandis m ON s.mandi_id = m.id WHERE s.id = ?", (slot_id,)).fetchone()

            if not slot:
                conn.close()
                self._send_json({"error": "Slot not found"}, 404)
                return

            geo_res = verify_geofence(farmer_lat, farmer_lon, slot["mandi_lat"], slot["mandi_lng"], threshold_meters=500.0)

            is_active = 1 if geo_res["is_within_geofence"] else 0
            new_status = "GEOFENCED_ACTIVE" if geo_res["is_within_geofence"] else "BOOKED"

            cursor.execute("UPDATE tokens SET is_active = ?, is_geofenced = ?, distance_to_mandi_meters = ?, activated_at = CURRENT_TIMESTAMP WHERE slot_id = ?",
                           (is_active, is_active, geo_res["distance_meters"], slot_id))
            cursor.execute("UPDATE slots SET status = ? WHERE id = ?", (new_status, slot_id))

            conn.commit()
            conn.close()

            self._send_json({
                "slot_id": slot_id,
                "token_code": slot["token_code"],
                "geofence_status": geo_res,
                "token_activated": geo_res["is_within_geofence"],
                "new_slot_status": new_status
            })

        elif path == "/api/v1/quality/submit":
            slot_id = int(body.get("slot_id", 1))
            gross_weight = float(body.get("gross_weight", 5200.0))
            tare_weight = float(body.get("tare_weight", 1200.0))
            net_weight = gross_weight - tare_weight
            moisture = float(body.get("moisture_pct", 11.5))
            foreign = float(body.get("foreign_matter_pct", 1.2))
            
            # Grade classification logic
            if moisture <= 12.0 and foreign <= 1.5:
                grade = "Grade A"
                rate = 2275.00 # MSP rate per quintal
            elif moisture <= 14.0 and foreign <= 2.5:
                grade = "Grade B"
                rate = 2150.00
            else:
                grade = "Grade C"
                rate = 1980.00

            net_quintals = net_weight / 100.0
            total_payout = round(net_quintals * rate, 2)

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO quality_gradings (slot_id, gross_weight, tare_weight, net_weight, moisture_pct, foreign_matter_pct, grade, rate_per_quintal, total_payout) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (slot_id, gross_weight, tare_weight, net_weight, moisture, foreign, grade, rate, total_payout))
            cursor.execute("UPDATE slots SET status = 'QUALITY_PASSED' WHERE id = ?", (slot_id,))
            conn.commit()
            conn.close()

            self._send_json({
                "success": True,
                "slot_id": slot_id,
                "net_weight_kg": net_weight,
                "grade": grade,
                "rate_per_quintal": rate,
                "total_payout_inr": total_payout,
                "status": "QUALITY_PASSED"
            })

        elif path == "/api/v1/pfms/disburse":
            slot_id = int(body.get("slot_id", 1))
            conn = get_db_connection()
            cursor = conn.cursor()

            slot = cursor.execute("SELECT s.*, f.id as farmer_id, f.name as farmer_name, q.total_payout FROM slots s JOIN farmers f ON s.farmer_id = f.id JOIN quality_gradings q ON s.id = q.slot_id WHERE s.id = ?", (slot_id,)).fetchone()

            if not slot:
                conn.close()
                self._send_json({"error": "Slot or Quality Grading record not found"}, 400)
                return

            payout_res = process_dbt_payment(
                farmer_id=slot["farmer_id"],
                slot_id=slot_id,
                amount=slot["total_payout"],
                farmer_name=slot["farmer_name"]
            )

            cursor.execute("INSERT INTO pfms_transactions (slot_id, farmer_id, pfms_ref_no, amount, status) VALUES (?, ?, ?, ?, ?)",
                           (slot_id, slot["farmer_id"], payout_res["pfms_ref_no"], slot["total_payout"], "CREDITED"))
            cursor.execute("UPDATE slots SET status = 'COMPLETED' WHERE id = ?", (slot_id,))

            conn.commit()
            conn.close()

            self._send_json({
                "success": True,
                "pfms_response": payout_res,
                "slot_status": "COMPLETED"
            })

        elif path == "/api/v1/voice/process":
            query_text = body.get("text", "मुझे कल टोकन चाहिए")
            lang = body.get("language", "hi")
            result = voice_bot.process_voice_input(query_text, language=lang)
            self._send_json(result)

        elif path == "/api/v1/grievance/submit":
            farmer_id = int(body.get("farmer_id", 1))
            category = body.get("category", "Payment Delay")
            description = body.get("description", "Payment inquiry")
            ticket_id = f"GRV-2026-{random.randint(1000, 9999)}"

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO grievances (ticket_id, farmer_id, category, description) VALUES (?, ?, ?, ?)",
                           (ticket_id, farmer_id, category, description))
            conn.commit()
            conn.close()

            self._send_json({
                "success": True,
                "ticket_id": ticket_id,
                "category": category,
                "status": "SUBMITTED",
                "message": f"Grievance Ticket {ticket_id} submitted successfully! DoCA Support team will review within 24 hours."
            })

        else:
            self._send_json({"error": "Endpoint not found", "path": path}, 404)

def run_server(port=8000):
    init_db()
    
    # Auto-seed db if empty
    conn = get_db_connection()
    count = conn.execute("SELECT count(*) FROM mandis").fetchone()[0]
    conn.close()
    if count == 0:
        print("Initializing seed data...")
        # Trigger seed via handler logic
        conn = get_db_connection()
        cursor = conn.cursor()
        mandis_seed = [
            ("Pune Main APMC Mandi", "APMC-PUNE-01", 18.5204, 73.8567, 300, "Pune", "Maharashtra"),
            ("Nashik Grain Mandi", "APMC-NSK-02", 19.9975, 73.7898, 450, "Nashik", "Maharashtra"),
            ("Karnal Wheat Mandi", "APMC-KRN-03", 29.6857, 76.9905, 500, "Karnal", "Haryana")
        ]
        for m in mandis_seed:
            cursor.execute("INSERT INTO mandis (name, code, latitude, longitude, max_daily_capacity, city, state) VALUES (?, ?, ?, ?, ?, ?, ?)", m)
        cursor.execute("INSERT INTO farmers (aadhaar_hash, name, mobile, state, district, crop_type, land_hectares) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ("8492-3019-4810", "Ramesh Patil", "9823411029", "Maharashtra", "Pune", "Wheat", 4.5))
        fid = cursor.lastrowid
        token_code = "TK-8492"
        cursor.execute("INSERT INTO slots (farmer_id, mandi_id, slot_date, hour_slot, allocated_crop_qty, crop_type, token_code, status, predicted_wait_minutes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (fid, 1, "2026-08-27", "09:00 - 10:00", 50.0, "Wheat", token_code, "BOOKED", 12))
        sid = cursor.lastrowid
        cursor.execute("INSERT INTO tokens (slot_id, token_number, is_active, is_geofenced, distance_to_mandi_meters) VALUES (?, ?, ?, ?, ?)",
                       (sid, token_code, 0, 0, 1420.0))
        conn.commit()
        conn.close()

    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, MandiAPIHandler)
    print(f"🚀 Harvest Heist Platform Server running on http://localhost:{port}")
    print(f"🌾 Farmer Mobile App: http://localhost:{port}/farmer")
    print(f"🏛️ Mandi Admin Dashboard: http://localhost:{port}/admin")
    httpd.serve_forever()

if __name__ == '__main__':
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run_server(port)
