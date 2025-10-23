import subprocess
import sys
import os
import shutil

def build():
    """Packages the application using PyInstaller."""
    print("--- Starting Build Process ---")
    
    script_path = 'gui.py'
    app_name = "AITweaker"

    # 1. Check for PyInstaller
    try:
        import PyInstaller
        print("PyInstaller found.")
    except ImportError:
        print("Error: PyInstaller is not installed. Please run 'pip install pyinstaller' to install it.")
        sys.exit(1)

    # 2. Run PyInstaller command
    command = [
        'pyinstaller',
        '--name', app_name,
        '--windowed',  # No console window for the GUI
        '--clean',     # Clean PyInstaller cache and remove temporary files
        script_path,
    ]

    print(f"\nRunning PyInstaller command: {' '.join(command)}")
    try:
        # Using capture_output to hide the verbose output unless there's an error
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("--- PyInstaller Execution Failed ---")
        print(e.stdout)
        print(e.stderr)
        print("------------------------------------")
        sys.exit(1)

    print("\nPyInstaller finished. Copying required script files...")

    # 3. Copy necessary data files into the output directory
    dist_path = os.path.join('dist', app_name)
    proxy_script_path = 'proxy.py'

    if os.path.exists(proxy_script_path):
        print(f"Copying '{proxy_script_path}' to '{dist_path}'")
        shutil.copy(proxy_script_path, dist_path)
    else:
        print(f"Warning: Could not find '{proxy_script_path}'. The bundled application may not work correctly.")

    print("\n--- Build process complete! ---")
    print(f"The application is located in the '{dist_path}' folder.")
    print("On first run, it will generate 'profiles.json' and 'rules.json' in that folder.")

if __name__ == "__main__":
    build()
