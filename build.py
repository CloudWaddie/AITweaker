import sys
import os
import shutil
import subprocess

def build():
    """Packages the application using PyInstaller."""
    print("--- Starting PyInstaller Build Process ---")
    
    script_path = 'gui.py'
    app_name = "AITweaker"
    output_dir = "dist"

    # Ensure the output directory is clean
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)

    # PyInstaller command
    command = [
        "pyinstaller",
        script_path,
        "--noconfirm", # Overwrite previous builds without asking
        "--onedir",    # Create a one-folder bundle (reduces false positives)
        f"--name={app_name}",
        f"--distpath={output_dir}",
        "--add-data=proxy.py;.",
        "--add-data=profiles.json;.",
        "--add-data=rules.json;.",
        "--hidden-import=customtkinter", # Explicitly include customtkinter
        "--hidden-import=mitmproxy",     # Explicitly include mitmproxy
    ]

    print(f"\nRunning PyInstaller build for {app_name}...")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"--- PyInstaller Execution Failed ---")
        print(e)
        print("-------------------------------------")
        sys.exit(1)

    print("\n--- Build process complete! ---")
    print(f"The application is located in the '{output_dir}' folder.")
    print("On first run, it will generate 'profiles.json' and 'rules.json' in that folder.")

if __name__ == "__main__":
    build()
