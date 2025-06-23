import subprocess

# Replace the path below with the full path to your Python executable
python_path = r"C:\Users\anton\Desktop\projects\TarotScoreTracker\.venv\Scripts\python.exe"
subprocess.run([python_path, "-m", "streamlit", "run", "app.py"])
