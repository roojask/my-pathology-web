import os

# หา Path ปัจจุบัน
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ตั้งค่าโฟลเดอร์
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
RESULT_FOLDER = os.path.join(BASE_DIR, 'results')
ASSETS_FOLDER = os.path.join(BASE_DIR, 'assets')

# *** เช็คชื่อไฟล์นี้ให้ตรงกับในโฟลเดอร์ assets ของคุณ ***
TEMPLATE_PDF = 'RCC_Wilms_Tumor_Template.pdf' 

# ตั้งค่า Model
WHISPER_MODEL_SIZE = "small"

# ตั้งค่า Path
os.environ["PATH"] += os.pathsep + BASE_DIR