import re
import json

class MultilingualVoiceBot:
    """
    Multilingual Voice AI Service for Farmers (Hindi, Marathi, English).
    Uses Speech-to-Text & NLP intent recognition for WhatsApp / Twilio voice booking.
    """

    def __init__(self):
        # Keyword patterns for Intent recognition across languages
        self.slot_keywords = ["टोकन", "स्लॉट", "बुक", "slot", "book", "token", "तारीख", "गहू", "गेहूं", "wheat", "तांदूळ", "चावल", "paddy"]
        self.status_keywords = ["स्थिती", "स्थिति", "status", "queue", "वेटिंग", "टोकन नंबर", "नंबर", "number", "कधी", "कब", "when"]

    def process_voice_input(self, audio_transcript_or_text: str, language: str = "hi"):
        """
        Parses text/transcription from Whisper Speech-to-Text model.
        Extracted intents: 'BOOK_SLOT' or 'CHECK_STATUS' or 'GENERAL_QUERY'.
        """
        text = audio_transcript_or_text.strip().lower()

        # Detect intent
        is_booking = any(kw in text for kw in self.slot_keywords)
        is_status = any(kw in text for kw in self.status_keywords)

        # Extract crop type
        crop = "Wheat"
        if any(c in text for c in ["गहू", "गेहूं", "wheat"]):
            crop = "Wheat"
        elif any(c in text for c in ["तांदूळ", "चावल", "paddy", "rice"]):
            crop = "Paddy"
        elif any(c in text for c in ["कापूस", "कपास", "cotton"]):
            crop = "Cotton"

        if is_status:
            intent = "CHECK_STATUS"
            if language == "mr":
                response_text = "तुमचे टोकन #TK-8492 सध्या सक्रिय आहे. तुमच्या पुढे ५ ट्रॅक्टर रांगेत आहेत. अंदाजे वेळ: १५ मिनिटे."
            elif language == "hi":
                response_text = "आपका टोकन #TK-8492 वर्तमान में सक्रिय है। आपके आगे 5 ट्रैक्टर कतार में हैं। अनुमानित समय: 15 मिनट।"
            else:
                response_text = "Your token #TK-8492 is active. 5 tractors ahead in queue. Estimated wait: 15 minutes."

        elif is_booking or "बुक" in text or "slot" in text:
            intent = "BOOK_SLOT"
            if language == "mr":
                response_text = f"नमस्कार! {crop} साठवणुकीसाठी उद्या सकाळी ०९:०० ते १०:०० चा स्लॉट सुचवला आहे. टोकन बुक करण्यासाठी होय म्हणा."
            elif language == "hi":
                response_text = f"नमस्कार! {crop} की बिक्री के लिए कल सुबह 09:00 से 10:00 का स्लॉट अनुशंसित है। टोकन बुक करने के लिए 'हाँ' कहें।"
            else:
                response_text = f"Hello! Recommended slot for {crop} tomorrow 09:00 - 10:00 AM. Reply YES to confirm booking."

        else:
            intent = "GENERAL_QUERY"
            if language == "mr":
                response_text = "हार्वेस्ट हाइस्ट (Harvest Heist) मंडी खरेदी प्लॅटफॉर्मवर आपले स्वागत आहे. आपण स्लॉट बुकिंग किंवा टोकन स्थितीबद्दल विचारू शकता."
            elif language == "hi":
                response_text = "हार्वेस्ट हाइस्ट (Harvest Heist) मंडी खरीद प्लेटफॉर्म में आपका स्वागत है। आप स्लॉट बुकिंग या टोकन स्थिति के बारे में पूछ सकते हैं।"
            else:
                response_text = "Welcome to Harvest Heist Mandi Procurement Platform. You can query slot booking or queue token status."

        return {
            "input_text": audio_transcript_or_text,
            "detected_language": language,
            "detected_intent": intent,
            "extracted_crop": crop,
            "voice_response_text": response_text,
            "audio_mock_url": f"/api/v1/voice/audio-stream?text={response_text[:20]}"
        }

if __name__ == "__main__":
    bot = MultilingualVoiceBot()
    
    # Test Hindi booking query
    hi_res = bot.process_voice_input("मुझे कल गेहूं बेचने के लिए टोकन बुक करना है", language="hi")
    print("Hindi Voice Query Result:", json.dumps(hi_res, ensure_ascii=False, indent=2))

    # Test Marathi status query
    mr_res = bot.process_voice_input("माझ्या टोकनची काय स्थिती आहे", language="mr")
    print("\nMarathi Voice Query Result:", json.dumps(mr_res, ensure_ascii=False, indent=2))
