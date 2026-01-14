from jiwer import wer

# Ground Truth (สิ่งที่มนุษย์ถอดความไว้ถูกต้อง)
reference = "the specimen consists of a mastectomy with a mass measuring five centimeters"

# Hypothesis (สิ่งที่ AI Whisper ถอดความได้)
hypothesis = "the specimen consists of a mastectomy with a mass measuring 5 cm"

# คำนวณค่า WER
error_rate = wer(reference, hypothesis)
print(f"Word Error Rate (WER): {error_rate * 100:.2f}%")