import subprocess
import time

with open('server_start.log', 'w') as f:
    process = subprocess.Popen(['python', '-u', 'app.py'], stdout=f, stderr=f)
    time.sleep(10)
    process.poll()
    if process.returncode is not None:
        f.write(f"\nProcess exited with code {process.returncode}")
    else:
        f.write("\nProcess is still running")
