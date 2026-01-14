import whisper
import config

model = None

# เพิ่มตัวเลขที่มักจะผิดบ่อยๆ ลงไปใน Prompt
MEDICAL_PROMPT = (
    "Surgical Pathology Report. "
    "Measurements: 18 x 9 x 6 cm, 15 x 7 cm, 3.6 x 3 x 2.8 cm. "
    "Margins: 0.7 cm, 3.5 cm, 1 cm, 8 cm, 5 cm, 0.4 cm. "
    "Codes: A1-1, A2-1 to A4-1, A5-1, A6-1. "
    "Terms: Modified Radical Mastectomy, infiltrative firm yellow white mass, "
    "nipple is everted, lower outer quadrant."
)

def load_model():
    global model
    if model is None:
        print(f"Loading Whisper Model ({config.WHISPER_MODEL_SIZE})...")
        model = whisper.load_model(config.WHISPER_MODEL_SIZE)
    return model

def transcribe(audio_path):
    ai = load_model()
    # ใส่ initial_prompt เพื่อไกด์ให้ AI รู้ว่าต้องเจอเลขพวกนี้
    result = ai.transcribe(audio_path, language="en", initial_prompt=MEDICAL_PROMPT)
    return result["text"]