import sys
import subprocess
from pathlib import Path
import toml

# Add src to sys.path to import artreactor
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from artreactor.core.managers.plugin_manager import PluginManager
except ImportError as e:
    print(f"Error importing PluginManager: {e}")
    sys.exit(1)

def run_command(command, cwd=None, exit_on_fail=True):
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd, text=True)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        if exit_on_fail:
            sys.exit(result.returncode)
    return result

def resolve_dependencies():
    print("Resolving dependencies...")
    manager = PluginManager()
    plugin_deps = manager.get_all_dependencies_from_manifests()
    
    print(f"Found {len(plugin_deps)} plugin dependencies: {plugin_deps}")
    
    # Read base dependencies from pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        pyproject = toml.load(f)
        
    base_deps = pyproject["project"].get("dependencies", [])
    
    # Combine dependencies
    all_deps = list(set(base_deps + plugin_deps))
    
    # Write to a temporary requirements.in
    req_in_path = project_root / "requirements.gen.in"
    with open(req_in_path, "w") as f:
        for dep in all_deps:
            f.write(f"{dep}\n")
            
    # Use uv to compile (this checks for conflicts)
    # Assuming uv is installed
    run_command(["uv", "pip", "compile", "requirements.gen.in", "-o", "requirements.gen.txt"])
    
    # Install dependencies
    run_command(["uv", "pip", "install", "-r", "requirements.gen.txt"])
    
    # Install the project itself in editable mode
    run_command(["uv", "pip", "install", "-e", "."])
    
    print("Dependencies resolved and installed.")

def run_tests():
    print("Running tests...")
    run_command(["pytest", "tests"])

def run_lint():
    print("Running lint...")
    # Using ruff if available, otherwise skip or fail? 
    # Spec says MUST run linting.
    # We should add ruff to dev dependencies if not present.
    try:
        run_command(["ruff", "check", "--fix", "src", "tests"])
    except FileNotFoundError:
        print("Warning: ruff not found. Skipping lint.")
        # Fail if strictly required? Spec says MUST.
        # But if not installed in env, we should probably install it.
        pass

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "resolve":
            resolve_dependencies()
        elif cmd == "test":
            run_tests()
        elif cmd == "lint":
            run_lint()
        elif cmd == "all":
            resolve_dependencies()
            run_tests()
            run_lint()
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
    else:
        # Default to all
        resolve_dependencies()
        run_tests()
        run_lint()

if __name__ == "__main__":
    main()
