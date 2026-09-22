#!/usr/bin/env python3
import os
import sys
import subprocess
import signal
import time

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    lpitutor_dir = os.path.join(root_dir, "LPITUTOR")
    backend_dir = os.path.join(lpitutor_dir, "backend")

    processes = []

    def cleanup(sig=None, frame=None):
        print("\n\n🛑 Stopping all PragTutor services...")
        for p, name in processes:
            print(f"  • Terminating {name} (PID {p.pid})...")
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        print("✅ All services stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("=" * 65)
    print("🚀  STARTING PRAGTUTOR FULL-STACK SYSTEM")
    print("=" * 65)

    # Detect python virtual environment binary
    venv_python = os.path.join(root_dir, "venv", "bin", "python")
    if not os.path.exists(venv_python):
        venv_python = os.path.join(backend_dir, "venv", "bin", "python")
    if not os.path.exists(venv_python):
        venv_python = sys.executable

    print(f"🔹 Using Python Environment: {venv_python}")

    # Launch Python AI Backend Server
    if os.path.exists(os.path.join(backend_dir, "main.py")):
        print("🔹 [1/2] Launching Python FastAPI Backend (Port 8000)...")
        py_proc = subprocess.Popen(f'HF_HUB_OFFLINE=1 "{venv_python}" main.py', cwd=backend_dir, shell=True)
        processes.append((py_proc, "Python Backend"))
    elif os.path.exists(os.path.join(root_dir, "app.py")):
        print("🔹 [1/2] Launching Python REST Backend app.py (Port 8000)...")
        py_proc = subprocess.Popen(f'HF_HUB_OFFLINE=1 "{venv_python}" app.py', cwd=root_dir, shell=True)
        processes.append((py_proc, "Python Backend"))
    time.sleep(1)

    # Launch React Frontend
    if os.path.exists(lpitutor_dir):
        print("🔹 [2/2] Launching React EdTech Frontend (Port 5173)...")
        fe_proc = subprocess.Popen("npm run dev", cwd=lpitutor_dir, shell=True)
        processes.append((fe_proc, "React Frontend"))

    print("\n" + "=" * 65)
    print("🎉 ALL PRAGTUTOR SERVICES STARTED SUCCESSFULLY!")
    print("  🌐 Modern React EdTech Web App: http://localhost:5173")
    print("  🤖 Python AI RAG Backend API:   http://localhost:8000")
    print("  Press Ctrl+C to stop all services simultaneously.")
    print("=" * 65 + "\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
