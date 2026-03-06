import subprocess
import sys
import time
import webbrowser
import socket
import urllib.request
import urllib.error
from pathlib import Path
import pystray
from PIL import Image

def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def wait_for_server(port: int, timeout: int = 15) -> bool:
    start_time = time.time()
    url = f"http://localhost:{port}/_stcore/health"
    while time.time() - start_time < timeout:
        try:
            response = urllib.request.urlopen(url)
            if response.getcode() == 200:
                return True
        except (urllib.error.URLError, ConnectionResetError):
            pass
        time.sleep(0.5)
    return False

def start_dashboard_server(port: int) -> subprocess.Popen:
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running from source (src/alphaforge/launcher.pyw)
        base_path = Path(__file__).parent.parent.parent
    
    app_path = base_path / "dashboard" / "app.py"
    
    if not app_path.exists():
        # Last resort check for dashboard at same level as launcher.pyw
        app_path = Path(__file__).parent / "dashboard" / "app.py"

    # CREATE_NO_WINDOW = 0x08000000
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(app_path), 
         "--server.port", str(port), "--server.headless", "true"],
        creationflags=0x08000000,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def create_tray_icon(port: int, server_process: subprocess.Popen):
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent.parent
        
    icon_path = base_path / "assets" / "icon.png"

    if not icon_path.exists():
        image = Image.new('RGB', (64, 64), color=(73, 109, 137))
    else:
        image = Image.open(icon_path)

    def on_open_dashboard(icon, item):
        webbrowser.open(f"http://localhost:{port}")

    def on_open_data(icon, item):
        try:
            from alphaforge.config import settings
            data_dir = settings.data_dir
        except ImportError:
            # Fallback for frozen app if imports are tricky
            data_dir = Path.home() / "AlphaForge" / "data"
            
        data_dir.mkdir(parents=True, exist_ok=True)
        import os
        os.startfile(data_dir)

    def on_quit(icon, item):
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_process.kill()
        icon.stop()

    menu = (
        pystray.MenuItem("Open Dashboard", on_open_dashboard, default=True),
        pystray.MenuItem("Open Data Folder", on_open_data),
        pystray.MenuItem("Quit", on_quit)
    )
    
    icon = pystray.Icon("AlphaForge", image, "AlphaForge", menu)
    icon.run()

def init_db_if_needed():
    try:
        #CLI approach might not work if not in PATH. Programmatic approach:
        from alphaforge.database import init_db
        from alphaforge.models import Base
        Base.metadata.create_all(bind=init_db().bind)
    except Exception as e:
        print(f"Could not initialize DB: {e}")

def main():
    init_db_if_needed()
    port = find_free_port()
    proc = start_dashboard_server(port)
    if wait_for_server(port):
        webbrowser.open(f"http://localhost:{port}")
    create_tray_icon(port, proc)
    sys.exit(0)

if __name__ == "__main__":
    main()
