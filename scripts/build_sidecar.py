import shutil
import PyInstaller.__main__
from pathlib import Path

# Define paths
# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
FINAL_BIN_DIR = PROJECT_ROOT / "src" / "ArcVision" / "src-tauri" / "backend"
TEMP_BUILD_DIR = PROJECT_ROOT / "build" / "sidecar_temp"

# Clean temp dir
if TEMP_BUILD_DIR.exists():
    shutil.rmtree(TEMP_BUILD_DIR)
TEMP_BUILD_DIR.mkdir(parents=True, exist_ok=True)

# Target executable name
TARGET_NAME = "artreactor-x86_64-pc-windows-msvc.exe"

print(f"Building Sidecar (OneDir) for {TARGET_NAME} in temp dir...")

# Run PyInstaller
PyInstaller.__main__.run([
    str(SRC_DIR / "artreactor" / "cli" / "main.py"),
    "--name=artreactor",
    "--onedir",
    "--clean",
    "--noconsole",
    f"--distpath={TEMP_BUILD_DIR}",
    f"--specpath={PROJECT_ROOT / 'scripts'}",
    "--collect-all=artreactor", 
    "--hidden-import=uvicorn.logging",
    "--hidden-import=uvicorn.loops",
    "--hidden-import=uvicorn.loops.auto",
    "--hidden-import=uvicorn.protocols",
    "--hidden-import=uvicorn.protocols.http",
    "--hidden-import=uvicorn.protocols.http.auto",
    "--hidden-import=uvicorn.lifespan",
    "--hidden-import=uvicorn.lifespan.on",
])

# Process in temp dir
GENERATED_DIR = TEMP_BUILD_DIR / "artreactor"
GENERATED_EXE = GENERATED_DIR / "artreactor.exe"

if GENERATED_EXE.exists():
    # Rename EXE to target triple
    GENERATED_EXE.rename(GENERATED_DIR / TARGET_NAME)
    
    # Clean final destination
    if FINAL_BIN_DIR.exists():
        try:
            shutil.rmtree(FINAL_BIN_DIR)
        except Exception as e:
            print(f"Warning: Failed to clean destination {FINAL_BIN_DIR}: {e}")
            # Try to continue? If generic locked, move will fail.
    
    FINAL_BIN_DIR.parent.mkdir(parents=True, exist_ok=True)
    
    # Move the directory
    # shutil.move(src, dst) where dst does not exist treats dst as name of new dir
    print(f"Moving artifacts to {FINAL_BIN_DIR}...")
    shutil.move(str(GENERATED_DIR), str(FINAL_BIN_DIR))
    
    # Clean temp root matches (distpath)
    shutil.rmtree(TEMP_BUILD_DIR)
    
    print(f"Successfully built and deployed: {FINAL_BIN_DIR / TARGET_NAME}")
else:
    print(f"Error: Expected output {GENERATED_EXE} not found.")
    exit(1)
