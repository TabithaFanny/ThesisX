import subprocess
import sys

result = subprocess.run(
    [r"C:\Python314\python.exe", r"C:\Users\Administrator\Desktop\文表智联\test_final_performance.py"],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Exit code:", result.returncode)
