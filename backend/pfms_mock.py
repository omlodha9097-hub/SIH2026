import random
import time
from datetime import datetime

def generate_pfms_ref():
    """Generates a unique PFMS reference number format: PFMS-2026-XXXXX"""
    rand_num = random.randint(100000, 999999)
    return f"PFMS-2026-{rand_num}"

def process_dbt_payment(farmer_id: int, slot_id: int, amount: float, farmer_name: str, bank_ifsc: str = "SBIN0001234"):
    """
    Simulates sending payment request to PFMS server for Direct Benefit Transfer (DBT).
    """
    ref_no = generate_pfms_ref()
    
    # Mock PFMS response payload
    return {
        "status": "APPROVED",
        "pfms_ref_no": ref_no,
        "farmer_id": farmer_id,
        "slot_id": slot_id,
        "farmer_name": farmer_name,
        "amount_inr": amount,
        "bank_ifsc": bank_ifsc,
        "account_mask": "XXXXXX4892",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "bank_transaction_utr": f"UTR{random.randint(100000000000, 999999999999)}",
        "message": f"₹{amount:,.2f} successfully credited to {farmer_name}'s bank account via PFMS DBT."
    }

def get_pfms_status(pfms_ref_no: str):
    """
    Retrieves real-time status of a PFMS payment transaction.
    """
    return {
        "pfms_ref_no": pfms_ref_no,
        "status": "CREDITED",
        "stage": "DBT_ACKNOWLEDGED_BY_BANK",
        "verification_level": "AADHAAR_SEEDED_BANK_ACC",
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }

if __name__ == "__main__":
    payment = process_dbt_payment(farmer_id=1, slot_id=101, amount=45200.00, farmer_name="Ramesh Patil")
    print("PFMS Payment Mock Output:", payment)
