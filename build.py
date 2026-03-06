import subprocess
import shutil
from pathlib import Path

def main():
    print("Cleaning old builds...")
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)
    
    print("Running PyInstaller...")
    subprocess.run(["python", "-m", "uv", "run", "pyinstaller", "build_launcher.spec", "--clean", "--noconfirm"], check=True)
    
    print("Copying configuration templates...")
    dist_dir = Path("dist/AlphaForge")
    if Path("config.yaml").exists():
        shutil.copy("config.yaml", dist_dir / "config.yaml")
        
    print("Creating README-dist.txt...")
    readme_path = dist_dir / "README-dist.txt"
    readme_path.write_text("AlphaForge Desktop Application\n\nRun AlphaForge.exe to start the application. A system tray icon will appear.")
    
    print("Build complete: dist/AlphaForge/")

if __name__ == "__main__":
    main()
