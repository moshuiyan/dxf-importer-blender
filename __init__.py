bl_info = {
    "name": "DXF Import Pro",
    "author": "moshi",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "File > Import > DXF (.dxf)",
    "description": "Advanced DXF importer with support for layers, blocks, text, and precise geometry",
    "warning": "",
    "doc_url": "https://github.com/moshi/import_autocad_dxf_format_dxf",
    "tracker_url": "https://github.com/moshi/import_autocad_dxf_format_dxf/issues",
    "category": "Import-Export",
}

import bpy
import os
import sys
import subprocess
import importlib
from pathlib import Path
from bpy_extras.io_utils import ImportHelper
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    EnumProperty,
    PointerProperty,
)
from bpy.types import Operator, Panel, PropertyGroup, AddonPreferences
import importlib.util
import tempfile
import traceback
from typing import Dict, Any, Optional, List, Tuple, Set, Union

# Check for required dependencies
REQUIRED_PACKAGES = [
    'ezdxf>=1.3.0',
    'pyproj>=3.0.0',
]

# Import the DXF importer and constants
from .dxfimport.importer.dxf_importer import DXFImporter, BY_LAYER, BY_BLOCK, SEPARATED, BY_CLOSED_NO_BULGE_POLY


def check_dependencies():
    """Check if all required packages are installed.
    
    Returns:
        list: List of missing package requirements
    """
    missing = []
    
    for package in REQUIRED_PACKAGES:
        # Extract package name and version requirements
        if '>=' in package:
            pkg_name, req_version = package.split('>=')
            pkg_name = pkg_name.strip()
            req_version = tuple(map(int, req_version.split('.')))
        else:
            pkg_name = package.split('==')[0].strip()
            req_version = None
        
        # First try pkg_resources for more accurate version checking
        try:
            import pkg_resources
            try:
                installed = pkg_resources.get_distribution(pkg_name)
                if req_version:
                    installed_version = tuple(map(int, installed.version.split('.')))
                    if installed_version < req_version:
                        missing.append(f"{pkg_name}>={'.'.join(map(str, req_version))} (installed: {installed.version})")
                continue  # Package is installed with correct version
            except pkg_resources.DistributionNotFound:
                missing.append(package)
                continue
            except Exception as e:
                print(f"Error checking {pkg_name}: {e}")
        except ImportError:
            pass  # pkg_resources not available, fall through to importlib
        
        # Fallback to importlib if pkg_resources fails
        try:
            module = importlib.import_module(pkg_name)
            if req_version and hasattr(module, '__version__'):
                installed_version = tuple(map(int, module.__version__.split('.')))
                if installed_version < req_version:
                    missing.append(f"{pkg_name}>={'.'.join(map(str, req_version))} (installed: {module.__version__})")
        except ImportError:
            missing.append(package)
        except Exception as e:
            print(f"Error checking {pkg_name}: {e}")
            missing.append(f"{package} (check failed: {str(e)})")
    
    return missing

class DXFImportPreferences(AddonPreferences):
    bl_idname = __package__
    
    def draw(self, context):
        layout = self.layout
        missing = check_dependencies()
        
        if missing:
            box = layout.box()
            box.label(text="Missing Dependencies", icon='ERROR')
            for pkg in missing:
                box.label(text=f"- {pkg}")
            
            box.operator("wm.install_dxf_dependencies", 
                        text="Install Dependencies", 
                        icon='CONSOLE')
        else:
            box = layout.box()
            box.label(text="All dependencies are installed", icon='CHECKMARK')

class INSTALL_OT_DXFDependencies(Operator):
    """Install missing dependencies"""
    bl_idname = "wm.install_dxf_dependencies"
    bl_label = "Install Dependencies"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def execute(self, context):
        python_exe = Path(sys.executable)
        self.report({'INFO'}, f"Installing dependencies using: {python_exe}")
        
        for package in REQUIRED_PACKAGES:
            try:
                # Install directly to Blender's Python
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
                self.report({'INFO'}, f"Successfully installed {package}")
                
            except subprocess.CalledProcessError as e:
                self.report({'ERROR'}, f"Failed to install {package}. Error: {e}")
                # Continue with next package instead of failing completely
                continue
            except Exception as e:
                self.report({'ERROR'}, f"Unexpected error installing {package}: {e}")
                continue
        
        # Check if all dependencies are now installed
        missing = check_dependencies()
        if missing:
            self.report({'WARNING'}, f"Some dependencies failed to install: {', '.join(missing)}")
            return {'CANCELLED'}
        
        # Only reload if all dependencies are installed
        try:
            bpy.ops.preferences.addon_disable(module=__package__)
            bpy.ops.preferences.addon_enable(module=__package__)
        except Exception as e:
            self.report({'ERROR'}, f"Error reloading add-on: {e}")
            return {'CANCELLED'}
        
        self.report({'INFO'}, "All dependencies installed successfully!")
        return {'FINISHED'}



class DXFImportSettings(PropertyGroup):
    """Container for DXF import settings."""
    
    # File settings
    filepath: StringProperty(
        name="File Path",
        description="Path to the DXF file",
        maxlen=1024,
        subtype='FILE_PATH',
    )
    
    # Import options
    import_blocks: BoolProperty(
        name="Import Blocks",
        description="Import block definitions and references",
        default=True,
    )
    
    import_text: BoolProperty(
        name="Import Text",
        description="Import text entities",
        default=True,
    )
    
    import_invisible: BoolProperty(
        name="Import Invisible",
        description="Import entities on hidden or frozen layers",
        default=False,
    )
    
    # Geometry options
    scale: FloatProperty(
        name="Scale",
        description="Scale factor for imported geometry",
        default=1.0,
        min=0.0001,
        max=1000.0,
    )
    
    curve_segments: bpy.props.IntProperty(
        name="Curve Segments",
        description="Number of segments for curves and circles",
        default=12,
        min=3,
        max=128,
    )
    
    # Layer options
    create_layers: BoolProperty(
        name="Create Layers",
        description="Create Blender collections for DXF layers",
        default=True,
    )
    
    # Coordinate system
    y_up: BoolProperty(
        name="Y Up",
        description="Convert from Y-up to Z-up coordinate system",
        default=True,
    )
    
    # Advanced options
    verbose: BoolProperty(
        name="Verbose",
        description="Print debug information to the console",
        default=False,
    )


class IMPORT_OT_dxf(Operator, ImportHelper):
    """Import a DXF file as a collection of Blender objects"""
    
    bl_idname = "import_scene.dxf"
    bl_label = "Import DXF"
    bl_options = {'PRESET', 'UNDO'}
    
    # File dialog filter
    filename_ext = ".dxf"
    filter_glob: StringProperty(
        default="*.dxf",
        options={'HIDDEN'},
        maxlen=255,
    )
    
    # Import settings
    settings: PointerProperty(
        type=DXFImportSettings,
        name="DXF Import Settings",
        description="Import settings",
    )
    
    def draw(self, context):
        """Draw the import dialog."""
        layout = self.layout
        settings = self.settings
        
        # Main options
        box = layout.box()
        box.label(text="Import Options", icon='IMPORT')
        box.prop(settings, "import_blocks")
        box.prop(settings, "import_text")
        box.prop(settings, "import_invisible")
        
        # Geometry options
        box = layout.box()
        box.label(text="Geometry", icon='MESH_DATA')
        box.prop(settings, "scale")
        box.prop(settings, "curve_segments")
        
        # Layer options
        box = layout.box()
        box.label(text="Layers", icon='OUTLINER_COLLECTION')
        box.prop(settings, "create_layers")
        
        # Coordinate system
        box = layout.box()
        box.label(text="Coordinate System", icon='WORLD')
        box.prop(settings, "y_up")
        
        # Advanced options
        box = layout.box()
        box.prop(settings, "verbose")
    
    def execute(self, context):
        """Execute the import operation."""
        # Get import settings
        settings = self.settings
        filepath = self.filepath
        
        # Check if file exists
        if not os.path.isfile(filepath):
            self.report({'ERROR'}, f"File not found: {filepath}")
            return {'CANCELLED'}
        
        # Create a new collection for the import
        import_name = os.path.splitext(os.path.basename(filepath))[0]
        collection = bpy.data.collections.new(import_name)
        context.scene.collection.children.link(collection)
        
        # Set up import options
        options = {
            'import_blocks': settings.import_blocks,
            'import_text': settings.import_text,
            'import_invisible': settings.import_invisible,
            'scale': settings.scale,
            'curve_segments': settings.curve_segments,
            'create_layers': settings.create_layers,
            'y_up': settings.y_up,
            'verbose': settings.verbose,
        }
        
        # Import the DXF file
        try:
            # Print debug info
            print(f"\n=== Starting DXF Import ===")
            print(f"File: {filepath}")
            print(f"Options: {options}")
            
            # Initialize importer
            try:
                importer = DXFImporter(filepath, options)
                print("DXFImporter initialized successfully")
            except Exception as e:
                print(f"\n!!! Error creating DXFImporter: {str(e)}")
                import traceback
                traceback.print_exc()
                self.report({'ERROR'}, f"初始化DXF导入器失败: {str(e)}")
                return {'CANCELLED'}
            
            # Read DXF file
            try:
                print("Reading DXF file...")
                success = importer.read()
                print(f"DXF read result: {success}")
            except Exception as e:
                print(f"\n!!! Error reading DXF file: {str(e)}")
                import traceback
                traceback.print_exc()
                self.report({'ERROR'}, f"读取DXF文件失败: {str(e)}")
                return {'CANCELLED'}
            
            # Import to scene
            if success:
                try:
                    print("Importing to Blender scene...")
                    importer.import_to_scene(context.scene, collection)
                    print("Import completed successfully")
                    self.report({'INFO'}, f"成功导入 {filepath}")
                    return {'FINISHED'}
                except Exception as e:
                    print(f"\n!!! Error importing to scene: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    self.report({'ERROR'}, f"导入到场景时出错: {str(e)}")
                    return {'CANCELLED'}
            else:
                self.report({'ERROR'}, f"无法导入DXF文件: 文件可能已损坏或不支持此格式")
                return {'CANCELLED'}
                
        except Exception as e:
            error_msg = f"导入DXF时发生错误: {str(e)}"
            print(f"\n!!! Unexpected error: {error_msg}")
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, error_msg)
            return {'CANCELLED'}
        finally:
            print("=== DXF Import Finished ===\n")


def menu_func_import(self, context):
    """Add the import option to the File > Import menu."""
    self.layout.operator(IMPORT_OT_dxf.bl_idname, text="AutoCAD DXF (.dxf)")


classes = (
    DXFImportSettings,
    DXFImportPreferences,
    INSTALL_OT_DXFDependencies,
    IMPORT_OT_dxf,
)

def register():
    """Register the add-on."""
    from bpy.utils import register_class
    
    # Register all classes
    for cls in classes:
        try:
            register_class(cls)
        except Exception as e:
            print(f"Error registering class {cls.__name__}: {e}")
    
    # Add to import menu
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    
    # Register properties
    if not hasattr(bpy.types.Scene, 'dxf_import_settings'):
        bpy.types.Scene.dxf_import_settings = PointerProperty(type=DXFImportSettings)
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Please install them from the add-on preferences.")
    else:
        print("All dependencies are installed.")


def unregister():
    """Unregister the add-on."""
    from bpy.utils import unregister_class
    
    # Remove from import menu - use a more reliable method
    try:
        bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    except (AttributeError, ValueError):
        # If the menu function is not in the list or menu doesn't exist, just pass
        pass
    
    # Unregister all classes in reverse order
    for cls in reversed(classes):
        try:
            unregister_class(cls)
        except (RuntimeError, ValueError):
            # Class not registered or already unregistered
            pass
    
    # Unregister properties
    if hasattr(bpy.types.Scene, 'dxf_import_settings'):
        try:
            del bpy.types.Scene.dxf_import_settings
        except:
            pass


if __name__ == "__main__":
    register()
