import sys
from pathlib import Path
import winshell
from win32com.client import Dispatch

def create_start_menu_shortcut(exe_path: Path):
    start_menu_dir = Path(winshell.programs()) / "AlphaForge"
    start_menu_dir.mkdir(parents=True, exist_ok=True)
    
    shortcut_path = start_menu_dir / "AlphaForge.lnk"
    
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.Targetpath = str(exe_path)
    shortcut.WorkingDirectory = str(exe_path.parent)
    shortcut.IconLocation = str(exe_path)
    shortcut.save()
    print(f"Created shortcut at: {shortcut_path}")

if __name__ == "__main__":
    if sys.platform == "win32":
        dist_exe = Path(__file__).parent.parent.parent.parent / "dist" / "AlphaForge" / "AlphaForge.exe"
        if dist_exe.exists():
            create_start_menu_shortcut(dist_exe)
        else:
            print(f"Exe not found at {dist_exe}, please build first.")
