"""
DXF Importer for Blender

This module provides functionality to import DXF files into Blender.
"""

"""
DXF Importer for Blender

This module provides functionality to import DXF files into Blender.
"""

# Import the main importer class and constants
from .importer.dxf_importer import DXFImporter, BY_LAYER, BY_BLOCK, SEPARATED, BY_CLOSED_NO_BULGE_POLY

# Version information
__version__ = '0.1.0'

# Clean up namespace
__all__ = [
    'DXFImporter',
    'BY_LAYER',
    'BY_BLOCK',
    'SEPARATED',
    'BY_CLOSED_NO_BULGE_POLY'
]
