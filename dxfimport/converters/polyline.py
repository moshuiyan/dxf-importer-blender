""
Converters for DXF polyline entities.

This module provides converters for LWPOLYLINE and POLYLINE entities.
"""

import bpy
import bmesh
import math
import numpy as np
from mathutils import Vector, Matrix
from typing import List, Optional, Tuple, Dict, Any, Union

from .base import BaseConverter, ConversionOptions

# Type aliases
Vec3 = Tuple[float, float, float]

@BaseConverter.register_converter('LWPOLYLINE')
class LwPolylineConverter(BaseConverter):
    """Converter for DXF LWPOLYLINE entities."""
    
    def convert(self, collection, parent=None, **kwargs) -> List[bpy.types.Object]:
        """Convert a DXF LWPOLYLINE to a Blender curve or mesh."""
        # Get polyline points and properties
        points = self.entity.get_points()
        closed = self.entity.closed
        
        if not points or len(points) < 2:
            return []
        
        # Check if polyline has width or is 3D
        has_width = any(hasattr(p, 'start_width') and p.start_width > 0 or 
                       hasattr(p, 'end_width') and p.end_width > 0 
                       for p in points)
        
        has_elevation = hasattr(self.entity.dxf, 'elevation') and self.entity.dxf.elevation != 0
        
        # Convert to 3D points
        vertices = []
        for point in points:
            x, y = point[0], point[1]
            z = self.entity.dxf.elevation if has_elevation else 0.0
            vertices.append(self.transform_point((x, y, z)))
        
        # Handle closed polylines
        if closed and len(vertices) > 2:
            vertices.append(vertices[0])
        
        # Create curve or mesh based on properties
        if has_width:
            return self._create_mesh(vertices, collection, parent)
        else:
            return self._create_curve(vertices, closed, collection, parent)
    
    def _create_curve(self, vertices: List[Vec3], closed: bool, 
                     collection, parent=None) -> List[bpy.types.Object]:
        """Create a curve from polyline vertices."""
        # Create a new curve data
        curve_data = bpy.data.curves.new(f"Polyline_{self.entity.dxf.handle}", 'CURVE')
        curve_data.dimensions = '3D'
        
        # Create a new spline
        spline = curve_data.splines.new('POLY')
        spline.points.add(len(vertices) - 1)  # One point is already created
        
        # Set the points
        for i, vertex in enumerate(vertices):
            spline.points[i].co = (*vertex, 1.0)
        
        # Set closed property
        spline.use_cyclic_u = closed
        
        # Create object
        obj = self.create_object(
            curve_data,
            f"Polyline_{self.entity.dxf.handle}",
            collection,
            parent=parent,
            **self.get_object_attributes()
        )
        
        return [obj]
    
    def _create_mesh(self, vertices: List[Vec3], collection, parent=None) -> List[bpy.types.Object]:
        """Create a mesh from polyline with width."""
        # This is a simplified implementation
        # A more complete version would handle varying widths and bulges
        
        # Create a new mesh and object
        mesh = bpy.data.meshes.new(f"PolylineMesh_{self.entity.dxf.handle}")
        obj = bpy.data.objects.new(f"PolylineMesh_{self.entity.dxf.handle}", mesh)
        
        # Create a bmesh to build the mesh
        bm = bmesh.new()
        
        # Add vertices
        bm_verts = [bm.verts.new(vertex) for vertex in vertices]
        
        # Add edges
        for i in range(len(bm_verts) - 1):
            bm.edges.new((bm_verts[i], bm_verts[i + 1]))
        
        # Update the mesh
        bm.to_mesh(mesh)
        bm.free()
        
        # Set object properties
        obj.dxf_type = 'LWPOLYLINE'
        obj.dxf_handle = self.entity.dxf.handle
        obj.dxf_layer = self.entity.dxf.layer
        
        # Link to collection and set parent
        if collection:
            collection.objects.link(obj)
        if parent:
            obj.parent = parent
        
        return [obj]
    
    def get_object_attributes(self) -> Dict[str, Any]:
        """Get attributes for the Blender object."""
        return {
            'dxf_type': 'LWPOLYLINE',
            'dxf_handle': self.entity.dxf.handle,
            'dxf_layer': self.entity.dxf.layer,
            'dxf_closed': self.entity.closed,
        }

@BaseConverter.register_converter('POLYLINE')
class PolylineConverter(BaseConverter):
    """Converter for DXF POLYLINE entities."""
    
    def convert(self, collection, parent=None, **kwargs) -> List[bpy.types.Object]:
        """Convert a DXF POLYLINE to Blender objects."""
        # Check if this is a polyface mesh
        if self.entity.is_poly_face_mesh or self.entity.is_polygon_mesh:
            return self._convert_polyface_mesh(collection, parent)
        
        # Check if this is a 3D polyline
        if self.entity.dxf.hasattr('elevation') or any(v[2] != 0 for v in self.entity.points()):
            return self._convert_3d_polyline(collection, parent)
        
        # Default to 2D polyline
        return self._convert_2d_polyline(collection, parent)
    
    def _convert_2d_polyline(self, collection, parent=None) -> List[bpy.types.Object]:
        """Convert a 2D polyline to a Blender curve."""
        points = list(self.entity.points())
        closed = self.entity.is_closed
        
        if len(points) < 2:
            return []
        
        # Create a new curve data
        curve_data = bpy.data.curves.new(f"Polyline_{self.entity.dxf.handle}", 'CURVE')
        curve_data.dimensions = '3D'
        
        # Create a new spline
        spline = curve_data.splines.new('POLY')
        spline.points.add(len(points) - 1)  # One point is already created
        
        # Set the points
        for i, point in enumerate(points):
            x, y, _ = point
            spline.points[i].co = (*self.transform_point((x, y, 0)), 1.0)
        
        # Set closed property
        spline.use_cyclic_u = closed
        
        # Create object
        obj = self.create_object(
            curve_data,
            f"Polyline_{self.entity.dxf.handle}",
            collection,
            parent=parent,
            **self.get_object_attributes()
        )
        
        return [obj]
    
    def _convert_3d_polyline(self, collection, parent=None) -> List[bpy.types.Object]:
        """Convert a 3D polyline to a Blender curve."""
        points = [self.transform_point(p) for p in self.entity.points()]
        
        if len(points) < 2:
            return []
        
        # Create a new curve data
        curve_data = bpy.data.curves.new(f"3DPolyline_{self.entity.dxf.handle}", 'CURVE')
        curve_data.dimensions = '3D'
        
        # Create a new spline
        spline = curve_data.splines.new('POLY')
        spline.points.add(len(points) - 1)  # One point is already created
        
        # Set the points
        for i, point in enumerate(points):
            spline.points[i].co = (*point, 1.0)
        
        # Create object
        obj = self.create_object(
            curve_data,
            f"3DPolyline_{self.entity.dxf.handle}",
            collection,
            parent=parent,
            **self.get_object_attributes()
        )
        
        return [obj]
    
    def _convert_polyface_mesh(self, collection, parent=None) -> List[bpy.types.Object]:
        """Convert a polyface mesh to a Blender mesh."""
        # This is a simplified implementation
        # A more complete version would handle all polyface mesh features
        
        # Get vertices and faces
        vertices = [self.transform_point(v) for v in self.entity.vertices()]
        faces = []
        
        # Create a new mesh and object
        mesh = bpy.data.meshes.new(f"Polyface_{self.entity.dxf.handle}")
        obj = bpy.data.objects.new(f"Polyface_{self.entity.dxf.handle}", mesh)
        
        # Create a bmesh to build the mesh
        bm = bmesh.new()
        
        # Add vertices
        bm_verts = [bm.verts.new(vertex) for vertex in vertices]
        
        # For simplicity, just create edges between consecutive vertices
        # A real implementation would use the face information
        for i in range(len(bm_verts) - 1):
            bm.edges.new((bm_verts[i], bm_verts[i + 1]))
        
        # Update the mesh
        bm.to_mesh(mesh)
        bm.free()
        
        # Set object properties
        obj.dxf_type = 'POLYLINE'
        obj.dxf_handle = self.entity.dxf.handle
        obj.dxf_layer = self.entity.dxf.layer
        
        # Link to collection and set parent
        if collection:
            collection.objects.link(obj)
        if parent:
            obj.parent = parent
        
        return [obj]
    
    def get_object_attributes(self) -> Dict[str, Any]:
        """Get attributes for the Blender object."""
        return {
            'dxf_type': 'POLYLINE',
            'dxf_handle': self.entity.dxf.handle,
            'dxf_layer': self.entity.dxf.layer,
            'dxf_closed': self.entity.is_closed,
            'dxf_3d': self.entity.dxf.hasattr('elevation') or any(v[2] != 0 for v in self.entity.points()),
        }
