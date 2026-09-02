class VoiceEngine {
  constructor(lang = 'en-IN') {
    if (VoiceEngine.instance) return VoiceEngine.instance;
    this.lang = lang;
    this.recognition = null;
    this.isListening = false;
    this.isSpeaking = false;
    this.voices = [];
    
    // Voice Synth Init
    if ('speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = () => {
        this.voices = window.speechSynthesis.getVoices();
      };
      // Fetch immediately if already loaded
      this.voices = window.speechSynthesis.getVoices();
    }

    this.initSpeechRecognition();
    this.initUI();
    VoiceEngine.instance = this;
  }

  initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.lang = this.lang;
      this.recognition.interimResults = false;
      this.recognition.maxAlternatives = 1;

      this.recognition.onstart = () => {
        this.isListening = true;
        this.updateUIState();
      };

      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        this.processCommand(transcript);
      };

      this.recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        if (event.error === 'no-speech') {
          this.showToast("No speech detected. Please try again.");
        } else if (event.error === 'network') {
          this.showToast("Network error. Check connection.");
        } else if (event.error === 'not-allowed') {
          this.showToast("Mic access denied. Please allow permissions.");
        } else {
          this.showToast("Mic error: " + event.error);
        }
        this.isListening = false;
        this.updateUIState();
      };

      this.recognition.onend = () => {
        this.isListening = false;
        this.updateUIState();
      };
    } else {
      console.warn("Speech Recognition API not supported.");
    }
  }

  setLanguage(langCode) {
    this.lang = langCode;
    if (this.recognition) {
      this.recognition.lang = this.lang;
    }
  }

  toggleListening() {
    if (this.isListening) {
      this.recognition.stop();
    } else {
      if (this.recognition) {
        try {
          this.recognition.start();
        } catch(e) {
          this.showToast("Microphone error. Please try again.");
        }
      } else {
        this.showToast("Voice commands are not supported on this device.");
      }
    }
  }

  updateUIState() {
    const btn = document.getElementById('voiceWidgetBtn');
    if (btn) {
      if (this.isListening) btn.classList.add('listening');
      else btn.classList.remove('listening');
    }
  }


  showToast(msg) {
    let toast = document.createElement('div');
    toast.className = 'voice-toast';
    toast.innerText = msg;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.remove();
    }, 3000);
  }

  async processCommand(transcript) {
    this.showToast("Thinking...");
    
    try {
      const response = await fetch('/api/v1/voice/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: transcript,
          language: this.lang
        })
      });
      
      const data = await response.json();
      
      if (data && data.voice_response_text) {
        this.speak(data.voice_response_text);
        
        // Trigger specific UI events if needed based on intent
        if (data.detected_intent === 'BOOK_SLOT' && typeof window.triggerSlotBooking === 'function') {
           setTimeout(() => window.triggerSlotBooking(), 2000);
        } else if (data.detected_intent === 'CHECK_STATUS' && typeof window.triggerQueueStatus === 'function') {
           setTimeout(() => window.triggerQueueStatus(), 2000);
        }
      } else {
        this.speak("I couldn't process your request. Please try again.");
      }
    } catch (err) {
      console.error("AI Voice API Error:", err);
      this.speak("Network error. Could not reach the AI.");
    }
  }

  toggleAnnouncer() {
    if (this.isSpeaking) {
      window.speechSynthesis.cancel();
      this.isSpeaking = false;
      this.updateAnnouncerUI();
    } else {
      this.speak("Hello, your KYC is approved. You have a slot booked for tomorrow at 10 AM at Pune Mandi.");
    }
  }

  speak(text) {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      
      let voice = this.voices.find(v => v.lang.includes(this.lang));
      if (voice) utterance.voice = voice;
      else utterance.lang = this.lang;
      
      utterance.onstart = () => {
        this.isSpeaking = true;
        this.updateAnnouncerUI();
      };
      utterance.onend = () => {
        this.isSpeaking = false;
        this.updateAnnouncerUI();
      };
      utterance.onerror = () => {
        this.isSpeaking = false;
        this.updateAnnouncerUI();
      };

      window.speechSynthesis.speak(utterance);
    }
  }

  updateAnnouncerUI() {
    const btn = document.getElementById('voiceAnnouncerBtn');
    if (btn) {
      if (this.isSpeaking) {
        btn.classList.add('speaking');
        btn.innerHTML = '🔊 <span style="font-size:12px; margin-left:4px;">Stop</span>';
      } else {
        btn.classList.remove('speaking');
        btn.innerHTML = '🔊 <span style="font-size:12px; margin-left:4px;">Read</span>';
      }
    }
  }

  initUI() {
    if (document.getElementById('voiceWidgetBtn')) return;

    // Inject CSS
    const style = document.createElement('style');
    style.innerHTML = `
      .voice-widget {
        position: fixed; bottom: 20px; right: 20px; z-index: 1000;
        width: 60px; height: 60px; background: var(--primary-blue, #0284c7); border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 8px 24px rgba(2, 132, 199, 0.4); cursor: pointer; color: white; font-size: 24px; border: none;
        transition: all 0.2s;
      }
      .voice-widget:hover { transform: scale(1.05); }
      .voice-widget.listening { animation: pulse-voice-blue 1.5s infinite; background: #38bdf8; }
      
      .voice-announcer {
        position: fixed; bottom: 90px; right: 20px; z-index: 1000;
        background: #f59e0b; border-radius: 20px; padding: 10px 16px;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4); cursor: pointer; color: white; font-size: 18px; border: none; font-weight: bold;
        transition: all 0.2s;
      }
      .voice-announcer.speaking { animation: pulse-voice-orange 1s infinite; background: #fbbf24; }
      
      @keyframes pulse-voice-blue {
        0% { box-shadow: 0 0 0 0 rgba(14, 165, 233, 0.6); }
        100% { box-shadow: 0 0 0 20px rgba(14, 165, 233, 0); }
      }
      @keyframes pulse-voice-orange {
        0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.6); }
        100% { box-shadow: 0 0 0 20px rgba(245, 158, 11, 0); }
      }
      

      .voice-toast {
        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
        background: #334155; color: white; padding: 10px 20px; border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 9999; font-size: 14px;
        animation: fadein 0.3s, fadeout 0.3s 2.7s;
      }
      @keyframes fadein { from { opacity: 0; bottom: 0; } to { opacity: 1; bottom: 20px; } }
      @keyframes fadeout { from { opacity: 1; bottom: 20px; } to { opacity: 0; bottom: 0; } }
    `;
    document.head.appendChild(style);

    // Announcer Widget
    const announcerBtn = document.createElement('button');
    announcerBtn.id = 'voiceAnnouncerBtn';
    announcerBtn.className = 'voice-announcer';
    announcerBtn.title = 'Read Alerts & Status';
    announcerBtn.innerHTML = '🔊 <span style="font-size:12px; margin-left:4px;">Read</span>';
    announcerBtn.onclick = () => this.toggleAnnouncer();
    document.body.appendChild(announcerBtn);



    // Mic Widget
    const btn = document.createElement('button');
    btn.id = 'voiceWidgetBtn';
    btn.className = 'voice-widget';
    btn.title = 'Tap to speak command';
    btn.innerHTML = '🎤';
    btn.onclick = () => this.toggleListening();
    document.body.appendChild(btn);
  }


}

// Initialize globally
window.addEventListener('DOMContentLoaded', () => {
    let lang = localStorage.getItem('doca_lang') || 'en-IN';
    // Normalize simple lang codes to full locale for Speech API
    const langMap = {
      'en': 'en-IN', 'hi': 'hi-IN', 'mr': 'mr-IN', 'pa': 'pa-IN',
      'ta': 'ta-IN', 'te': 'te-IN', 'bn': 'bn-IN', 'gu': 'gu-IN', 'kn': 'kn-IN'
    };
    if (langMap[lang]) lang = langMap[lang];
    window.voiceAssistant = new VoiceEngine(lang);
});
