""
Converters for DXF block definitions and insertions.

This module provides converters for BLOCK and INSERT entities.
"""

import bpy
import math
import mathutils
from mathutils import Vector, Matrix, Euler
from typing import List, Optional, Tuple, Dict, Any, Set

from .base import BaseConverter, ConversionOptions
from ..importer import DXFImporter

# Type aliases
Vec3 = Tuple[float, float, float]

@BaseConverter.register_converter('BLOCK')
class BlockConverter(BaseConverter):
    """Converter for DXF BLOCK definitions."""
    
    def __init__(self, entity, options: Optional[ConversionOptions] = None):
        """Initialize the block converter."""
        super().__init__(entity, options)
        self._processed_blocks = set()  # Track processed blocks to prevent recursion
    
    def convert(self, collection, parent=None, **kwargs) -> List[bpy.types.Object]:
        """Convert a DXF BLOCK definition to a Blender collection.
        
        Note: BLOCK definitions don't create visible objects by themselves.
        They are stored in the block cache for later use by INSERT entities.
        """
        block_name = self.entity.dxf.name
        
        # Skip processing if already processed
        if block_name in self._processed_blocks:
            return []
            
        self._processed_blocks.add(block_name)
        
        # Skip anonymous blocks (e.g., hatch patterns) if not requested
        if not self.options.import_blocks and block_name.startswith('*'):
            return []
        
        # Create a new collection for the block
        block_collection = bpy.data.collections.new(f"Block_{block_name}")
        collection.children.link(block_collection)
        
        # Convert block entities
        importer = DXFImporter(None, self.options)
        importer.convert_entities(
            self.entity,
            block_collection,
            parent=None,  # No parent for block contents
            block_reference_point=self.entity.dxf.base_point
        )
        
        # Store block collection in the cache
        if not hasattr(bpy.context.scene, 'dxf_blocks'):
            bpy.context.scene.dxf_blocks = {}
        
        bpy.context.scene.dxf_blocks[block_name] = block_collection
        
        return []

@BaseConverter.register_converter('INSERT')
class InsertConverter(BaseConverter):
    """Converter for DXF INSERT entities."""
    
    def convert(self, collection, parent=None, **kwargs) -> List[bpy.types.Object]:
        """Convert a DXF INSERT to Blender objects by instancing a block."""
        block_name = self.entity.dxf.name
        
        # Skip if block import is disabled
        if not self.options.import_blocks:
            return []
        
        # Get block collection from cache
        block_collection = self._get_block_collection(block_name)
        if not block_collection:
            return []
        
        # Create an empty to represent the insert
        empty = bpy.data.objects.new(f"Insert_{block_name}", None)
        
        # Set transform
        location = self.transform_point(self.entity.dxf.insert)
        scale = self._get_scale()
        rotation = self._get_rotation()
        
        empty.location = location
        empty.rotation_euler = rotation
        empty.scale = scale
        
        # Link to collection and set parent
        collection.objects.link(empty)
        if parent:
            empty.parent = parent
        
        # Instance the block collection
        instance = bpy.data.objects.new(f"Instance_{block_name}", None)
        instance.instance_type = 'COLLECTION'
        instance.instance_collection = block_collection
        instance.parent = empty
        
        # Apply the same transform to the instance
        instance.location = location
        instance.rotation_euler = rotation
        instance.scale = scale
        
        collection.objects.link(instance)
        
        # Handle attributes
        self._process_attributes(empty, instance)
        
        return [empty, instance]
    
    def _get_block_collection(self, block_name: str) -> Optional[bpy.types.Collection]:
        """Get or create a block collection."""
        # Check if block is already loaded
        if hasattr(bpy.context.scene, 'dxf_blocks') and block_name in bpy.context.scene.dxf_blocks:
            return bpy.context.scene.dxf_blocks[block_name]
        
        # If block is not found, try to find and convert it
        doc = self.entity.doc
        if doc and block_name in doc.blocks:
            block = doc.blocks.get(block_name)
            if block:
                # Create a temporary converter for the block
                converter = BlockConverter(block, self.options)
                converter.convert(bpy.context.collection)
                
                # Try to get the block collection again
                if hasattr(bpy.context.scene, 'dxf_blocks') and block_name in bpy.context.scene.dxf_blocks:
                    return bpy.context.scene.dxf_blocks[block_name]
        
        return None
    
    def _get_scale(self) -> Tuple[float, float, float]:
        """Get the scale factors from the INSERT entity."""
        x_scale = self.entity.dxf.get('xscale', 1.0)
        y_scale = self.entity.dxf.get('yscale', 1.0)
        z_scale = self.entity.dxf.get('zscale', 1.0)
        
        # Apply global scale
        return (x_scale * self.options.scale, 
                y_scale * self.options.scale, 
                z_scale * self.options.scale)
    
    def _get_rotation(self) -> Tuple[float, float, float]:
        """Get the rotation from the INSERT entity."""
        # Get rotation angle (in degrees, around Z-axis for 2D)
        rotation_angle = math.radians(self.entity.dxf.get('rotation', 0.0))
        
        # For 3D rotations, we would need to handle the extrusion vector
        # This is a simplified 2D rotation
        return (0.0, 0.0, rotation_angle)
    
    def _process_attributes(self, parent_obj, instance_obj):
        """Process ATTRIB entities associated with this INSERT."""
        if not hasattr(self.entity, 'attribs'):
            return
            
        for attrib in self.entity.attribs:
            tag = attrib.dxf.tag
            value = attrib.dxf.text
            
            # Store as custom property on the parent object
            parent_obj[tag] = value
            
            # For visibility, you could also create text objects
            if self.options.import_text:
                self._create_attribute_text(attrib, parent_obj)
    
    def _create_attribute_text(self, attrib, parent):
        """Create a text object for an attribute."""
        text_content = attrib.dxf.text
        position = self.transform_point(attrib.dxf.insert)
        height = attrib.dxf.height * self.options.scale
        rotation = math.radians(attrib.dxf.get('rotation', 0.0))
        
        # Skip empty text
        if not text_content.strip():
            return
        
        # Create a text object
        text_data = bpy.data.curves.new(name=f"Attribute_{attrib.dxf.handle}", type='FONT')
        text_data.body = text_content
        text_data.size = height
        text_data.align_x = 'LEFT'
        
        # Create object
        text_obj = bpy.data.objects.new(f"Attribute_{attrib.dxf.tag}", text_data)
        text_obj.location = position
        text_obj.rotation_euler = (0, 0, rotation)
        text_obj.parent = parent
        
        # Link to the same collection as the parent
        if parent.users_collection:
            parent.users_collection[0].objects.link(text_obj)
    
    def get_object_attributes(self) -> Dict[str, Any]:
        """Get attributes for the Blender object."""
        return {
            'dxf_type': 'INSERT',
            'dxf_handle': self.entity.dxf.handle,
            'dxf_layer': self.entity.dxf.layer,
            'dxf_block_name': self.entity.dxf.name,
            'dxf_insert_point': self.entity.dxf.insert,
        }
