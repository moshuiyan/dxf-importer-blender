""
Converters for DXF text entities.

This module provides converters for TEXT and MTEXT entities.
"""

import bpy
import math
from mathutils import Vector, Matrix, Euler
from typing import List, Optional, Tuple, Dict, Any

from .base import BaseConverter, ConversionOptions

# Type aliations
Vec3 = Tuple[float, float, float]

@BaseConverter.register_converter('TEXT')
class TextConverter(BaseConverter):
    """Converter for DXF TEXT entities."""
    
    def convert(self, collection, parent=None, **kwargs) -> List[bpy.types.Object]:
        """Convert a DXF TEXT to a Blender text object."""
        if not self.options.import_text:
            return []
            
        # Get text properties
        text_content = self.entity.dxf.text
        position = self.transform_point(self.entity.dxf.insert)
        height = self.entity.dxf.height * self.options.scale
        rotation = math.radians(self.entity.dxf.rotation)
        
        # Skip empty text
        if not text_content.strip():
            return []
            
        # Create a new text object
        text_data = bpy.data.curves.new(name=f"Text_{self.entity.dxf.handle}", type='FONT')
        text_data.body = text_content
        text_data.size = height
        text_data.align_x = 'CENTER'  # Default alignment
        
        # Handle text alignment
        self._set_text_alignment(text_data, self.entity.dxf.halign, self.entity.dxf.valign)
        
        # Create object
        obj = self.create_object(
            text_data,
            f"Text_{self.entity.dxf.handle}",
            collection,
            parent=parent,
            location=position,
            rotation_euler=(0, 0, rotation),
            **self.get_object_attributes()
        )
        
        return [obj]
    
    def _set_text_alignment(self, text_data, halign, valign):
        """Set text alignment based on DXF halign/valign values."""
        # Horizontal alignment
        if halign == 0:  # Left
            text_data.align_x = 'LEFT'
        elif halign == 1:  # Center
            text_data.align_x = 'CENTER'
        elif halign == 2:  # Right
            text_data.align_x = 'RIGHT'
        elif halign == 3:  # Aligned
            text_data.align_x = 'JUSTIFY'
        elif halign == 4:  # Middle
            text_data.align_x = 'CENTER'
        elif halign == 5:  # Fit
            text_data.align_x = 'JUSTIFY'
        
        # Vertical alignment (approximate in Blender)
        if valign == 1:  # Top
            text_data.offset_y = -0.5
        elif valign == 2:  # Middle
            text_data.offset_y = 0
        elif valign == 3:  # Bottom
            text_data.offset_y = 0.5
    
    def get_object_attributes(self) -> Dict[str, Any]:
        """Get attributes for the Blender object."""
        return {
            'dxf_type': 'TEXT',
            'dxf_handle': self.entity.dxf.handle,
            'dxf_layer': self.entity.dxf.layer,
            'dxf_text': self.entity.dxf.text,
            'dxf_height': self.entity.dxf.height,
            'dxf_rotation': self.entity.dxf.rotation,
        }

@BaseConverter.register_converter('MTEXT')
class MTextConverter(BaseConverter):
    """Converter for DXF MTEXT entities."""
    
    def convert(self, collection, parent=None, **kwargs) -> List[bpy.types.Object]:
        """Convert a DXF MTEXT to a Blender text object."""
        if not self.options.import_text:
            return []
            
        # Get text properties
        text_content = self._clean_mtext(self.entity.text)
        position = self.transform_point(self.entity.dxf.insert)
        height = self.entity.dxf.char_height * self.options.scale
        rotation = math.radians(self.entity.dxf.rotation)
        
        # Skip empty text
        if not text_content.strip():
            return []
            
        # Create a new text object
        text_data = bpy.data.curves.new(name=f"MText_{self.entity.dxf.handle}", type='FONT')
        text_data.body = text_content
        text_data.size = height
        text_data.align_x = 'LEFT'  # Default alignment
        
        # Handle text alignment
        self._set_text_alignment(text_data, self.entity.dxf.attachment_point)
        
        # Create object
        obj = self.create_object(
            text_data,
            f"MText_{self.entity.dxf.handle}",
            collection,
            parent=parent,
            location=position,
            rotation_euler=(0, 0, rotation),
            **self.get_object_attributes()
        )
        
        return [obj]
    
    def _clean_mtext(self, text: str) -> str:
        """Clean up MTEXT formatting codes."""
        # Remove formatting codes like {\H0.7x;text} or \P for newlines
        import re
        
        # Replace newline markers
        text = text.replace('\P', '\n')
        
        # Remove formatting codes
        text = re.sub(r'\{[^\}]*\}', '', text)  # Remove {\...} blocks
        text = re.sub(r'\\[A-Za-z0-9\.]+;?', '', text)  # Remove \...; codes
        
        return text.strip()
    
    def _set_text_alignment(self, text_data, attachment_point):
        """Set text alignment based on MTEXT attachment point."""
        # MTEXT attachment points:
        # 1 = Top left, 2 = Top center, 3 = Top right
        # 4 = Middle left, 5 = Middle center, 6 = Middle right
        # 7 = Bottom left, 8 = Bottom center, 9 = Bottom right
        
        # Horizontal alignment
        if attachment_point in (1, 4, 7):  # Left
            text_data.align_x = 'LEFT'
        elif attachment_point in (2, 5, 8):  # Center
            text_data.align_x = 'CENTER'
        else:  # Right
            text_data.align_x = 'RIGHT'
            
        # Vertical alignment (approximate in Blender)
        if attachment_point in (1, 2, 3):  # Top
            text_data.offset_y = -0.5
        elif attachment_point in (4, 5, 6):  # Middle
            text_data.offset_y = 0
        else:  # Bottom
            text_data.offset_y = 0.5
    
    def get_object_attributes(self) -> Dict[str, Any]:
        """Get attributes for the Blender object."""
        return {
            'dxf_type': 'MTEXT',
            'dxf_handle': self.entity.dxf.handle,
            'dxf_layer': self.entity.dxf.layer,
            'dxf_text': self.entity.text,
            'dxf_height': self.entity.dxf.char_height,
            'dxf_rotation': self.entity.dxf.rotation,
        }
