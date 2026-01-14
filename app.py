import os
from flask import Flask, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename
import whisper

# ✅ เรียกใช้งานทีมงานผู้เชี่ยวชาญ (Services)
from services.parser_service import normalize_text, extract_data
from services.pdf_service import fill_pdf

app = Flask(__name__)

# ตั้งค่าโฟลเดอร์
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ASSETS_FOLDER = 'assets'  # โฟลเดอร์เก็บ Template

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# โหลดโมเดล Whisper
print("Loading Whisper model...")
model = whisper.load_model("base")
print("Model loaded!")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'audio_file' not in request.files:
            return "No file part"
        file = request.files['audio_file']
        if file.filename == '':
            return "No selected file"

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # 1. ถอดเสียง (Ear) 👂
            print("Transcribing...")
            result = model.transcribe(filepath)
            raw_text = result["text"]
            print(f"Raw Text: {raw_text}")

            # 2. แปลงข้อมูล (Brain) 🧠 -> เรียกใช้ parser_service
            # แปลงคำพูดให้เป็นระเบียบ (one -> 1, cm, x)
            cleaned_text = normalize_text(raw_text)
            print(f"Cleaned: {cleaned_text}")
            
            # ดึงข้อมูลสำคัญออกมา (Measuring, margins, checkboxes)
            data_points = extract_data(cleaned_text)
            print(f"Extracted Data: {data_points}")

            # 3. เตรียมไฟล์ Template
            template_filename = "RCC_Wilms_Tumor_Template.pdf"
            template_path = os.path.join(ASSETS_FOLDER, template_filename)

            # (ระบบกันพลาด: ถ้าหาไม่เจอ ให้ใช้ไฟล์ blank)
            if not os.path.exists(template_path):
                print(f"Warning: Template not found at {template_path}, trying fallback...")
                template_path = "template.pdf" 

            output_filename = f"Report_{filename}.pdf"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

            # 4. เขียนลง PDF (Hand) ✍️ -> เรียกใช้ pdf_service
            # ส่งข้อมูลที่กลั่นกรองแล้ว ไปให้คนเขียน เขียนลงช่องเป๊ะๆ
            try:
                fill_pdf(template_path, output_path, data_points)
                print("PDF Generated Successfully!")
            except Exception as e:
                print(f"Error generating PDF: {e}")
                return f"Error: {e}"

            return render_template('index.html', 
                                   transcription=cleaned_text,  # โชว์ข้อความที่เกลาแล้ว
                                   pdf_filename=output_filename)

    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    # as_attachment=False เพื่อให้เปิดดูได้เลย ไม่ต้องโหลด
    return send_file(file_path, as_attachment=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)