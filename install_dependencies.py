import bpy
import sys
import subprocess
import os
import importlib
from pathlib import Path

def check_package_installed(package_name):
    """Check if a package is installed in Blender's Python environment.
    
    Args:
        package_name: Name of the package to check (without version specifiers)
    Returns:
        bool: True if package is installed, False otherwise
    """
    # First try using pkg_resources which is more reliable for checking installed packages
    try:
        import pkg_resources
        try:
            pkg_resources.get_distribution(package_name)
            print(f"Package found via pkg_resources: {package_name}")
            return True
        except pkg_resources.DistributionNotFound:
            pass
    except ImportError:
        # pkg_resources is not available, fallback to importlib
        pass
    
    # Fallback to importlib with proper error handling
    try:
        importlib.import_module(package_name)
        print(f"Package found via importlib: {package_name}")
        return True
    except ImportError as e:
        # Check if the error is actually about a missing dependency
        if f"No module named '{package_name}'".lower() in str(e).lower():
            return False
        # If there's a different import error, the package might be partially installed
        print(f"Import error for {package_name}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error checking {package_name}: {e}")
        return False

def install_package(package):
    """Install a package using pip in Blender's Python environment."""
    # Use the Python executable that's running this script (Blender's Python)
    python_exe = Path(sys.executable)
    print(f"Using Python executable: {python_exe}")
    
    # Extract the base package name (without version specifiers)
    package_name = package.split('>=')[0].split('==')[0]
    
    # Check if package is already installed in Blender's Python
    if check_package_installed(package_name):
        print(f"{package_name} is already installed in Blender's Python")
        return True
        
    print(f"Installing {package}...")
    try:
        # Get Blender's user scripts directory
        import bpy
        target_dir = bpy.utils.user_resource('SCRIPTS', "addons")
        
        # Create a lib directory in the addon folder
        lib_dir = os.path.join(os.path.dirname(target_dir), 'lib')
        os.makedirs(lib_dir, exist_ok=True)
        
        # Add the lib directory to Python path if not already there
        if lib_dir not in sys.path:
            sys.path.append(lib_dir)
        
        # Install with --target to the user's addon lib directory
        cmd = [
            str(python_exe),
            "-m",
            "pip",
            "install",
            "--no-warn-script-location",
            "--target", lib_dir,
            "--upgrade",
            "--no-cache-dir",
            "--user",
            package
        ]
        print(f"Running: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        
        # Verify installation
        if check_package_installed(package_name):
            print(f"Successfully installed {package} in Blender's Python")
            return True
        else:
            print(f"Failed to verify installation of {package}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error installing {package}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error installing {package}: {e}")
        return False

def register():
    """Install required packages."""
    # Get the directory of the current addon
    addon_dir = Path(__file__).parent
    requirements_file = addon_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print("Requirements file not found")
        return False
    
    # Read requirements
    with open(requirements_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # Install each package
    success = True
    for req in requirements:
        if not install_package(req):
            success = False
    
    if success:
        print("All dependencies installed successfully")
    else:
        print("Some dependencies failed to install. Please check the console for details.")
    
    return success

if __name__ == "__main__":
    register()
