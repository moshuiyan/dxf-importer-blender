"""
Main DXF Importer Implementation

This module provides the main DXF importer implementation using ezdxf.
"""
import os
import re
from typing import Any, Dict, Iterator, Optional, Tuple, List

import bpy
from mathutils import Vector

from .base_importer import BaseDXFImporter

# Import ezdxf with fallback to dxfgrabber if not available
try:
    import ezdxf
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False

# Import options constants
BY_LAYER = 0
BY_DXFTYPE = 1
BY_CLOSED_NO_BULGE_POLY = 2
SEPARATED = 3
LINKED_OBJECTS = 4
GROUP_INSTANCES = 5
BY_BLOCK = 6

class DXFImporter(BaseDXFImporter):
    """Main DXF importer implementation using ezdxf."""
    
    def __init__(self, filepath: str, options: Optional[Dict[str, Any]] = None):
        """Initialize the DXF importer.
        
        Args:
            filepath: Path to the DXF file
            options: Dictionary of import options
        """
        super().__init__(filepath, options)
        self.doc = None
        self.modelspace = None
        self.blocks = {}
        self._unit_scale = 1.0
        
    def read(self) -> bool:
        """Read and parse the DXF file.
        
        Returns:
            bool: True if the file was read successfully, False otherwise
        """
        print(f"\n=== DXF Import Debug ===")
        print(f"Reading file: {self.filepath}")
        
        if not os.path.exists(self.filepath):
            error_msg = f"File not found: {self.filepath}"
            print(f"[ERROR] {error_msg}")
            self.add_error(error_msg)
            return False
            
        try:
            # Check file size
            file_size = os.path.getsize(self.filepath)
            print(f"File size: {file_size / 1024:.2f} KB")
            
            if file_size == 0:
                error_msg = "DXF file is empty"
                print(f"[ERROR] {error_msg}")
                self.add_error(error_msg)
                return False
                
            # Read the DXF file with error recovery
            try:
                print("Attempting to read DXF file with ezdxf...")
                self.doc = ezdxf.readfile(self.filepath)
                print("Successfully parsed DXF file")
            except ezdxf.DXFStructureError as e:
                print(f"Warning: DXF structure error, attempting recovery: {str(e)}")
                try:
                    from ezdxf import recover
                    print("Attempting to recover DXF file...")
                    self.doc, _ = recover.readfile(self.filepath)
                    print("Successfully recovered DXF file")
                except Exception as recover_error:
                    error_msg = f"Failed to recover DXF file: {str(recover_error)}"
                    print(f"[ERROR] {error_msg}")
                    self.add_error(error_msg)
                    return False
            
            # Check if document was loaded
            if not hasattr(self, 'doc') or self.doc is None:
                error_msg = "Failed to load DXF document"
                print(f"[ERROR] {error_msg}")
                self.add_error(error_msg)
                return False
            
            # Get modelspace and check if it's valid
            try:
                self.modelspace = self.doc.modelspace()
                print(f"Modelspace contains {len(self.modelspace)} entities")
            except Exception as e:
                error_msg = f"Error accessing modelspace: {str(e)}"
                print(f"[ERROR] {error_msg}")
                self.add_error(error_msg)
                return False
            
            # Get block definitions
            try:
                self.blocks = {block.name: block for block in self.doc.blocks}
                print(f"Found {len(self.blocks)} block definitions")
            except Exception as e:
                error_msg = f"Error reading block definitions: {str(e)}"
                print(f"[ERROR] {error_msg}")
                self.add_error(error_msg)
                # Continue even if blocks can't be read
                self.blocks = {}
            
            # Get unit conversion factor
            try:
                self._unit_scale = self._get_unit_scale()
                print(f"Unit scale factor: {self._unit_scale}")
            except Exception as e:
                error_msg = f"Error getting unit scale: {str(e)}"
                print(f"[WARNING] {error_msg}")
                self._unit_scale = 1.0  # Default to 1.0 if unit scale can't be determined
            
            print("DXF file read successfully")
            return True
            
        except IOError as e:
            error_msg = f"IO Error reading DXF file: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.add_error(error_msg)
            return False
            
        except ezdxf.DXFError as e:
            error_msg = f"DXF Error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.add_error(error_msg)
            return False
            
        except Exception as e:
            import traceback
            error_msg = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            print(f"[ERROR] {error_msg}")
            self.add_error(error_msg)
            return False
        finally:
            print("=== End of DXF Import Debug ===\n")
    
    def _get_unit_scale(self) -> float:
        """Get the scale factor to convert DXF units to Blender units.
        
        Returns:
            float: Scale factor
        """
        # Default to meters (1 unit = 1 meter)
        unit = self.doc.header.get('$INSUNITS', 6)  # 6 = meters
        
        # Conversion factors to meters
        unit_scales = {
            1: 0.0254,    # inches
            2: 25.4,      # feet
            3: 1609.34,   # miles
            4: 0.001,     # millimeters
            5: 0.01,      # centimeters
            6: 1.0,       # meters
            7: 1000.0,    # kilometers
            8: 0.0000254, # microinches
            9: 0.3048,    # mils
            10: 0.9144,   # yards
            11: 1852.0,   # angstroms
            12: 1e-10,    # nanometers
            13: 1e-6,     # microns
            14: 0.01,     # decimeters
            15: 0.001,    # decameters
            16: 0.0001,   # hectometers
            17: 1e-7,     # gigameters
            18: 149597870.691,  # astronomical units
            19: 9.461e+15,      # light years
            20: 3.086e+16,      # parsecs
        }
        
        return unit_scales.get(unit, 1.0)
    
    def get_entities(self) -> Iterator[Any]:
        """Get an iterator over all entities in the DXF file.
        
        Yields:
            Entity objects from the DXF file
        """
        if not self.doc:
            if not self.read():
                return
                
        for entity in self.modelspace:
            yield entity
    
    def get_blocks(self) -> Dict[str, Any]:
        """Get all block definitions from the DXF file.
        
        Returns:
            Dictionary mapping block names to block definitions
        """
        if not self.doc:
            if not self.read():
                return {}
                
        return self.blocks
    
    def import_to_scene(self, scene, collection, options: Optional[Dict[str, Any]] = None) -> list:
        """Import the DXF file into the given Blender scene and collection.
        
        Args:
            scene: The Blender scene to import into
            collection: The Blender collection to add objects to
            options: Additional import options
            
        Returns:
            List of error messages, if any
        """
        if not self.doc and not self.read():
            return self.get_errors()
            
        # Set default options
        options = options or {}
        combination = options.get('combination', BY_LAYER)
        recenter = options.get('recenter', False)
        
        try:
            # Store original objects for recentering if needed
            if recenter:
                original_objects = set(scene.objects)
            
            # Process entities based on combination mode
            if combination == BY_BLOCK:
                self._import_by_block(scene, collection, options)
            elif combination != SEPARATED:
                # Import combined and separated entities separately
                self._import_combined_entities(scene, collection, options)
                self._import_separated_entities(scene, collection, options)
            else:
                # Import all entities as separate objects
                self._import_separated_entities(scene, collection, options)
            
            # Handle recentering if needed
            if recenter:
                self._recenter_objects(scene, original_objects)
                
            # Apply georeferencing if specified
            if 'georeference' in options:
                self._apply_georeference(scene, options['georeference'])
                
        except Exception as e:
            self.add_error(f"Error during import: {str(e)}")
            
        return self.get_errors()
    
    def _import_by_block(self, scene, collection, options):
        """Import entities grouped by block."""
        # Implement block-based import logic
        pass
    
    def _import_combined_entities(self, scene, collection, options):
        """Import entities that should be combined."""
        # Implement combined entities import logic
        pass
    
    def _import_separated_entities(self, scene, collection, options):
        """Import entities as separate objects."""
        import bpy
        import mathutils
        from mathutils import Vector, Matrix
        
        # Get the scale factor
        scale = options.get('scale', 1.0)
        
        # Get all entities
        for entity in self.get_entities():
            try:
                dxf_type = entity.dxftype()
                
                # Skip unsupported entity types
                if dxf_type not in ['LINE', 'CIRCLE', 'ARC', 'LWPOLYLINE', 'POLYLINE', 'INSERT']:
                    continue
                
                # Create a new mesh and object
                mesh = bpy.data.meshes.new(name=f"DXF_{dxf_type}")
                obj = bpy.data.objects.new(f"DXF_{dxf_type}", mesh)
                
                # Link the object to the collection
                collection.objects.link(obj)
                
                # Convert DXF entity to mesh data
                if dxf_type == 'LINE':
                    # Create a simple line
                    start = Vector(entity.dxf.start) * scale
                    end = Vector(entity.dxf.end) * scale
                    
                    # Create a curve for the line
                    curve_data = bpy.data.curves.new('line', type='CURVE')
                    curve_data.dimensions = '3D'
                    
                    # Create a new spline in the curve
                    spline = curve_data.splines.new('NURBS')
                    spline.points.add(1)  # Add one point for the end
                    
                    # Set the start and end points
                    spline.points[0].co = (*start, 1.0)
                    spline.points[1].co = (*end, 1.0)
                    
                    # Create a new object with the curve data
                    obj = bpy.data.objects.new('DXF_LINE', curve_data)
                    collection.objects.link(obj)
                    
                elif dxf_type in ['CIRCLE', 'ARC']:
                    # Create a circle or arc
                    center = Vector(entity.dxf.center) * scale
                    radius = entity.dxf.radius * scale
                    
                    if dxf_type == 'CIRCLE':
                        bpy.ops.mesh.primitive_circle_add(
                            vertices=32,
                            radius=radius,
                            location=center,
                            rotation=(0, 0, 0)
                        )
                    else:  # ARC
                        start_angle = math.radians(entity.dxf.start_angle)
                        end_angle = math.radians(entity.dxf.end_angle)
                        
                        # Create a curve for the arc
                        curve_data = bpy.data.curves.new('arc', type='CURVE')
                        curve_data.dimensions = '3D'
                        
                        # Create a new spline in the curve
                        spline = curve_data.splines.new('NURBS')
                        
                        # Add points to the spline
                        segments = 32
                        angle_step = (end_angle - start_angle) / segments
                        
                        for i in range(segments + 1):
                            angle = start_angle + i * angle_step
                            x = center.x + radius * math.cos(angle)
                            y = center.y + radius * math.sin(angle)
                            spline.points.add(1)
                            spline.points[-1].co = (x, y, center.z, 1.0)
                        
                        # Create a new object with the curve data
                        obj = bpy.data.objects.new('DXF_ARC', curve_data)
                        collection.objects.link(obj)
                
                elif dxf_type in ['LWPOLYLINE', 'POLYLINE']:
                    # Create a polyline
                    points = []
                    
                    for vertex in entity.vertices():
                        point = Vector(vertex.dxf.location) * scale
                        points.append(point)
                    
                    # Create a new curve
                    curve_data = bpy.data.curves.new('polyline', type='CURVE')
                    curve_data.dimensions = '3D'
                    
                    # Create a new spline in the curve
                    spline = curve_data.splines.new('NURBS')
                    
                    # Add points to the spline
                    for point in points:
                        spline.points.add(1)
                        spline.points[-1].co = (*point, 1.0)
                    
                    # Close the spline if the polyline is closed
                    if entity.closed:
                        spline.use_cyclic_u = True
                    
                    # Create a new object with the curve data
                    obj = bpy.data.objects.new('DXF_POLYLINE', curve_data)
                    collection.objects.link(obj)
                
                elif dxf_type == 'INSERT':
                    # Handle block references
                    block_name = entity.dxf.name
                    if block_name in self.blocks:
                        # Get the block definition
                        block = self.blocks[block_name]
                        
                        # Get the insertion point and scale
                        insert_point = Vector(entity.dxf.insert) * scale
                        scale_x = entity.dxf.xscale * scale
                        scale_y = entity.dxf.yscale * scale
                        scale_z = entity.dxf.zscale * scale
                        
                        # Create a new collection for the block instance
                        block_collection = bpy.data.collections.new(f"BLOCK_{block_name}")
                        collection.children.link(block_collection)
                        
                        # Import the block entities
                        for block_entity in block:
                            # Recursively import block entities
                            # (This is a simplified version - you might need to handle transformations)
                            if hasattr(block_entity, 'dxftype'):
                                # Create a temporary importer for the block
                                temp_importer = DXFImporter("")
                                temp_importer.doc = self.doc
                                temp_importer.blocks = self.blocks
                                temp_importer._unit_scale = self._unit_scale
                                
                                # Import the entity
                                temp_importer._import_separated_entities(
                                    scene, 
                                    block_collection, 
                                    options
                                )
                        
                        # Apply the transformation to the entire block collection
                        for obj in block_collection.objects:
                            obj.location += insert_point
                            obj.scale = (scale_x, scale_y, scale_z)
            
            except Exception as e:
                self.add_error(f"Error importing {entity.dxftype()}: {str(e)}")
                import traceback
                traceback.print_exc()
    
    def _recenter_objects(self, scene, original_objects):
        """Recenter imported objects in the scene."""
        # Get all new objects
        new_objects = [obj for obj in scene.objects if obj not in original_objects]
        
        if not new_objects:
            return
            
        # Calculate bounding box of all new objects
        min_co = Vector((float('inf'),) * 3)
        max_co = -min_co
        
        for obj in new_objects:
            # Skip objects without bound_box (like cameras, lights, etc.)
            if not hasattr(obj, 'bound_box') or not obj.bound_box:
                continue
                
            # Get world space coordinates of the bounding box
            world_verts = [obj.matrix_world @ Vector(v) for v in obj.bound_box]
            
            # Update min and max coordinates
            for v in world_verts:
                min_co.x = min(min_co.x, v.x)
                min_co.y = min(min_co.y, v.y)
                min_co.z = min(min_co.z, v.z)
                max_co.x = max(max_co.x, v.x)
                max_co.y = max(max_co.y, v.y)
                max_co.z = max(max_co.z, v.z)
        
        # Calculate center
        center = (min_co + max_co) / 2
        
        # Move all objects to center them
        for obj in new_objects:
            if hasattr(obj, 'matrix_world'):
                obj.matrix_world.translation -= center
    
    def _apply_georeference(self, scene, georef_data):
        """Apply georeferencing information to the scene."""
        if 'srid' in georef_data:
            scene['SRID'] = georef_data['srid']
        elif 'proj' in georef_data:
            # Handle proj string
            match = re.search(r"\+init=(\w+):\w+", georef_data['proj'])
            if match:
                scene['SRID'] = match.group(1)
