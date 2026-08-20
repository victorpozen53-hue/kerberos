#!/usr/bin/env python3
# 🫧 Guard Bubble Shield — Protection HDD
import time, threading, psutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class BubbleShield:
    def __init__(self):
        self.protected_folders = [Path.home() / "Documents", Path.home() / "Desktop"]
        print("🫧 [Bubble Shield] Actif")

class BubbleHandler(FileSystemEventHandler):
    def __init__(self, shield):
        self.shield = shield
    def on_any_event(self, event):
        if event.is_directory:
            return
        print(f"🫧 [Bubble] Événement : {event.src_path}")

def start_guard():
    shield = BubbleShield()
    handler = BubbleHandler(shield)
    observer = Observer()
    for folder in shield.protected_folders:
        if folder.exists():
            observer.schedule(handler, str(folder), recursive=True)
    observer.start()
    print("✅ [Bubble Shield] Guard actif")
    return observer

if __name__ == "__main__":
    start_guard()
    while True:
        time.sleep(1)