import os
from pydub import AudioSegment

def convert_to_wav(input_path):
    """แปลงไฟล์เสียงใดๆ เป็น WAV มาตรฐาน"""
    try:
        sound = AudioSegment.from_file(input_path)
        output_path = os.path.splitext(input_path)[0] + "_converted.wav"
        sound.export(output_path, format="wav")
        return output_path
    except Exception as e:
        print(f"Audio Error: {e}")
        return None