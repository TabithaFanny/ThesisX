
import sys
import os
import time
sys.path.insert(0, ".")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from app.core.ai_service import AiWorker, build_continue_messages

class Test:
    def __init__(self):
        self.start = time.time()
        self.first_chunk = None
        self.count = 0
        
    def on_chunk(self, text):
        if self.count == 0:
            self.first_chunk = time.time() - self.start
            print(f"First chunk: {self.first_chunk:.2f}s")
        self.count += 1
        if self.count % 5 == 0:
            print(f"Chunks: {self.count}")
            
    def on_done(self, text):
        total = time.time() - self.start
        print(f"
Total time: {total:.2f}s")
        print(f"Total chunks: {self.count}")
        print(f"Response length: {len(text)}")
        print(f"
Preview: {text[:150]}...")
        
        if self.first_chunk and self.first_chunk < 5:
            print("
[GOOD] First chunk < 5s")
        else:
            print("
[SLOW] First chunk >= 5s")
        QApplication.quit()
        
    def on_error(self, err):
        print(f"Error: {err}")
        QApplication.quit()
        
    def run(self):
        print("Starting AI request...")
        msgs = build_continue_messages("AI technology is developing.", "")
        w = AiWorker(msgs, max_tokens=150, temperature=0.7)
        w.chunk_received.connect(self.on_chunk)
        w.finished_ok.connect(self.on_done)
        w.error_occurred.connect(self.on_error)
        w.start()

app = QApplication(sys.argv)
t = Test()
QTimer.singleShot(100, t.run)
QTimer.singleShot(45000, lambda: (print("TIMEOUT"), app.quit()))
sys.exit(app.exec())
