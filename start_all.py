import subprocess
import threading
import time
import sys
import os

def start_api():
    subprocess.run([sys.executable, "api_server.py"])

def start_bot():
    subprocess.run([sys.executable, "bot_main.py"])

def start_php():
    if os.name == 'nt':
        subprocess.run(["php", "-S", "localhost:8080", "shark_api.php"])
    else:
        subprocess.run(["php", "-S", "localhost:8080", "shark_api.php"])

if __name__ == "__main__":
    print("🦈 Starting SHARK...")
    
    threads = []
    
    threads.append(threading.Thread(target=start_api))
    threads.append(threading.Thread(target=start_bot))
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
