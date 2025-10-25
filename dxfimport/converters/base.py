""
Base converter class for DXF entities.

This module defines the base converter interface that all DXF entity converters should implement.
"""

import bpy
from typing import Any, Dict, List, Optional, Tuple, Union
from mathutils import Vector, Matrix, Color

from ..utils.geo import GeoReference

# Type aliases
Vec3 = Tuple[float, float, float]
ColorRGB = Tuple[float, float, float]

class ConversionOptions:
    """Options for DXF entity conversion."""
    
    def __init__(self, **kwargs):
        # General options
        self.scale = kwargs.get('scale', 1.0)  # Scale factor for coordinates
        self.import_invisible = kwargs.get('import_invisible', False)  # Import invisible entities
        self.import_hatches = kwargs.get('import_hatches', True)  # Import hatch patterns
        self.import_text = kwargs.get('import_text', True)  # Import text entities
        self.import_blocks = kwargs.get('import_blocks', True)  # Import block definitions
        self.import_layouts = kwargs.get('import_layouts', True)  # Import paper space layouts
        
        # Layer options
        self.create_layers = kwargs.get('create_layers', True)  # Create Blender layers for DXF layers
        self.layer_filter = kwargs.get('layer_filter', None)  # Function to filter layers
        
        # Geometry options
        self.curve_segments = kwargs.get('curve_segments', 12)  # Number of segments for curves
        self.bezier_steps = kwargs.get('bezier_steps', 8)  # Steps for bezier curves
        self.import_materials = kwargs.get('import_materials', True)  # Import materials
        self.smooth_angle = kwargs.get('smooth_angle', 30.0)  # Smoothing angle in degrees
        
        # Coordinate system options
        self.georef = kwargs.get('georef')  # GeoReference object for coordinate transformation
        self.y_up = kwargs.get('y_up', False)  # Y-up coordinate system (vs. Z-up)
        
        # Debug options
        self.verbose = kwargs.get('verbose', False)  # Print debug information


class BaseConverter:
    """Base class for DXF entity converters.
    
    This class defines the interface that all DXF entity converters should implement.
    """
    
    # Map of DXF entity type to converter class
    DXF_TYPES = {}
    
    @classmethod
    def register_converter(cls, dxf_type):
        """Decorator to register a converter class for a DXF entity type."""
        def decorator(converter_class):
            cls.DXF_TYPES[dxf_type] = converter_class
            return converter_class
        return decorator
    
    @classmethod
    def get_converter(cls, entity, options: Optional[ConversionOptions] = None):
        """Get the appropriate converter for a DXF entity."""
        if not options:
            options = ConversionOptions()
            
        dxf_type = entity.dxftype()
        converter_class = cls.DXF_TYPES.get(dxf_type)
        
        if not converter_class:
            # Try to find a converter by superclass
            for dxf_type, conv_class in cls.DXF_TYPES.items():
                if hasattr(entity, 'dxftype') and entity.dxftype() == dxf_type:
                    return conv_class(entity, options)
            return None
            
        return converter_class(entity, options)
    
    def __init__(self, entity, options: Optional[ConversionOptions] = None):
        """Initialize the converter with a DXF entity and options."""
        self.entity = entity
        self.options = options or ConversionOptions()
        self._materials = {}
    
    def convert(self, collection, parent=None, **kwargs) -> List[bpy.types.Object]:
        """Convert the DXF entity to Blender object(s).
        
        Args:
            collection: The Blender collection to add the object(s) to
            parent: Optional parent object
            **kwargs: Additional conversion options
            
        Returns:
            List of created Blender objects
        """
        raise NotImplementedError("Subclasses must implement convert()")
    
    def create_object(self, data, name: str, collection, parent=None, **kwargs) -> bpy.types.Object:
        """Create a Blender object with the given data.
        
        Args:
            data: The Blender data (e.g., mesh, curve, etc.)
            name: Name for the object
            collection: Collection to add the object to
            parent: Optional parent object
            **kwargs: Additional object properties
            
        Returns:
            The created Blender object
        """
        obj = bpy.data.objects.new(name, data)
        
        # Set object properties from kwargs
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        
        # Set location, rotation, scale
        if 'matrix_world' in kwargs:
            obj.matrix_world = kwargs['matrix_world']
        else:
            if 'location' in kwargs:
                obj.location = kwargs['location']
            if 'rotation_euler' in kwargs:
                obj.rotation_euler = kwargs['rotation_euler']
            if 'rotation_quaternion' in kwargs:
                obj.rotation_quaternion = kwargs['rotation_quaternion']
            if 'scale' in kwargs:
                obj.scale = kwargs['scale']
        
        # Link to collection and set parent
        if collection:
            collection.objects.link(obj)
        
        if parent:
            obj.parent = parent
        
        return obj
    
    def get_material(self, name: str, color: Optional[ColorRGB] = None) -> bpy.types.Material:
        """Get or create a material with the given name and color.
        
        Args:
            name: Name of the material
            color: Optional RGB color tuple (0.0-1.0)
            
        Returns:
            The Blender material
        """
        if not self.options.import_materials:
            return None
            
        if name in self._materials:
            return self._materials[name]
        
        # Create new material
        mat = bpy.data.materials.get(name)
        if not mat:
            mat = bpy.data.materials.new(name=name)
            mat.use_nodes = True
            
            # Set up principled BSDF
            nodes = mat.node_tree.nodes
            principled = nodes.get('Principled BSDF')
            if principled:
                if color:
                    principled.inputs['Base Color'].default_value = (*color, 1.0)
                principled.inputs['Metallic'].default_value = 0.0
                principled.inputs['Specular'].default_value = 0.5
                principled.inputs['Roughness'].default_value = 0.5
        
        self._materials[name] = mat
        return mat
    
    def get_layer_collection(self, layer_name: str, collection, parent=None) -> bpy.types.Collection:
        """Get or create a collection for the specified layer.
        
        Args:
            layer_name: Name of the layer
            collection: Parent collection
            parent: Parent object (optional)
            
        Returns:
            The layer collection
        """
        if not self.options.create_layers:
            return collection
        
        # Apply layer filter if specified
        if self.options.layer_filter and not self.options.layer_filter(layer_name):
            return None
        
        # Clean up layer name for Blender
        clean_name = self.clean_name(layer_name)
        
        # Check if collection already exists
        if clean_name in bpy.data.collections:
            layer_collection = bpy.data.collections[clean_name]
        else:
            # Create new collection
            layer_collection = bpy.data.collections.new(clean_name)
            collection.children.link(layer_collection)
        
        return layer_collection
    
    def clean_name(self, name: str) -> str:
        """Clean up a name for use in Blender."""
        # Replace invalid characters with underscore
        import re
        return re.sub(r'[\\/:"*?<>|]', '_', name.strip())
    
    def transform_point(self, point: Vec3) -> Vec3:
        """Transform a point from DXF to Blender coordinates."""
        x, y, z = point
        
        # Apply coordinate system transformation (Y-up to Z-up if needed)
        if self.options.y_up:
            x, y, z = x, z, -y
        
        # Apply scale
        x *= self.options.scale
        y *= self.options.scale
        z *= self.options.scale
        
        # Apply georeference transformation if available
        if self.options.georef:
            # TODO: Implement coordinate transformation using pyproj
            pass
        
        return (x, y, z)
