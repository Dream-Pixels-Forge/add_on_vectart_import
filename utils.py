import bpy
import os
import platform
import shutil
import subprocess
import sys
from mathutils import Vector

# SVG Scale Constants (Standard DPIs)
SVG_DPI_96 = 96.0  # Inkscape / Modern standard
SVG_DPI_72 = 72.0  # Illustrator / Legacy standard

def normalize_path(path):
    """Normalize path for cross-platform compatibility"""
    if path:
        return os.path.normpath(path)
    return path

def get_svg_scale_factor(dpi=96.0):
    """Calculate scale factor to convert SVG pixels to Blender meters (assuming 1px = 1mm or custom)"""
    # Blender default: 1 pixel = 1 Blender unit (usually 1 meter)
    # We want something more reasonable like 1px = 0.001 units (1mm)
    return 1.0 / dpi

def get_addon_prefs():
    """Get addon preferences"""
    return bpy.context.preferences.addons[__package__].preferences

_base_path_warned = False

def get_base_path():
    """Get base path from preferences or scene"""
    global _base_path_warned
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        
        if prefs and prefs.base_path and os.path.exists(prefs.base_path):
            _base_path_warned = False
            return normalize_path(os.path.abspath(prefs.base_path))
            
        scene = bpy.context.scene
        if (hasattr(scene, 'vectart_library_props') and 
            hasattr(scene.vectart_library_props, "base_path") and
            scene.vectart_library_props.base_path and 
            os.path.exists(scene.vectart_library_props.base_path)):
            _base_path_warned = False
            return normalize_path(os.path.abspath(scene.vectart_library_props.base_path))
            
    except Exception as e:
        print(f"Error getting base path: {str(e)}")
        
    # Show user-friendly message only once per session
    if not _base_path_warned:
        print("VectArt: Please set the library path in the add-on preferences (Edit > Preferences > Add-ons > VectArt Import & Preview).")
        _base_path_warned = True
        
    return ""

def find_svg_editor_path(editor_type):
    """Find path to SVG editor based on platform and editor type"""
    system = platform.system()
    
    # Default paths by platform and editor type
    paths = {
        'Windows': {
            'ILLUSTRATOR': [
                "C:\\Program Files\\Adobe\\Adobe Illustrator 2023\\Support Files\\Contents\\Windows\\Illustrator.exe",
                "C:\\Program Files\\Adobe\\Adobe Illustrator 2022\\Support Files\\Contents\\Windows\\Illustrator.exe"
            ],
            'AFFINITY': [
                "C:\\Program Files\\Affinity\\Designer\\Designer.exe"
            ],
            'INKSCAPE': [
                "C:\\Program Files\\Inkscape\\inkscape.exe",
                "C:\\Program Files\\Inkscape\\bin\\inkscape.exe"
            ]
        },
        'Darwin': {  # macOS
            'ILLUSTRATOR': [
                "/Applications/Adobe Illustrator.app/Contents/MacOS/Adobe Illustrator"
            ],
            'AFFINITY': [
                "/Applications/Affinity Designer.app/Contents/MacOS/Affinity Designer"
            ],
            'INKSCAPE': [
                "/Applications/Inkscape.app/Contents/MacOS/Inkscape"
            ]
        },
        'Linux': {
            'INKSCAPE': [
                "/usr/bin/inkscape"
            ]
        }
    }
    
    if system not in paths: return ""
    if editor_type not in paths[system]: return ""
        
    for path in paths[system][editor_type]:
        if os.path.exists(path):
            return path
            
    if editor_type == 'INKSCAPE':
        inkscape_path = shutil.which('inkscape')
        if inkscape_path: return inkscape_path
            
    return ""

def get_objects_bounding_box(objects):
    """Calculate the bounding box for a list of objects"""
    min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
    max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
    
    for obj in objects:
        matrix = obj.matrix_world
        for corner in obj.bound_box:
            world_corner = matrix @ Vector(corner)
            min_x = min(min_x, world_corner.x)
            min_y = min(min_y, world_corner.y)
            min_z = min(min_z, world_corner.z)
            max_x = max(max_x, world_corner.x)
            max_y = max(max_y, world_corner.y)
            max_z = max(max_z, world_corner.z)
    
    dimensions = Vector((max_x - min_x, max_y - min_y, max_z - min_z))
    center = Vector(((min_x + max_x)/2, (min_y + max_y)/2, (min_z + max_z)/2))
    
    return {
        'center': center,
        'dimensions': dimensions,
        'min': Vector((min_x, min_y, min_z)),
        'max': Vector((max_x, max_y, max_z))
    }

def get_layer_curves(layer_idx):
    """Get all curves assigned to a specific layer"""
    curves = []
    try:
        for obj in bpy.data.objects:
            if (obj.type == 'CURVE' and 
                "is_vectart" in obj and 
                "vectart_layer" in obj and 
                obj["vectart_layer"] == layer_idx):
                curves.append(obj)
    except Exception as e:
        print(f"Error getting layer curves: {str(e)}")
    return curves

def get_material_color(mat):
    """Extract RGB color from a material (handles Principled BSDF)"""
    if not mat or not mat.use_nodes:
        return None
    
    # Try to find Principled BSDF or Diffuse BSDF
    nodes = mat.node_tree.nodes
    for node in nodes:
        if node.type in {'BSDF_PRINCIPLED', 'BSDF_DIFFUSE'}:
            return list(node.inputs[0].default_value)[:3]
    return None

def match_and_cleanup_material(obj, original_mat_name):
    """
    Compares the newly imported material with the original one.
    If colors are identical, reuses original and deletes the new one.
    """
    if not obj or not obj.active_material:
        return
        
    new_mat = obj.active_material
    old_mat = bpy.data.materials.get(original_mat_name)
    
    if not old_mat:
        return
        
    new_color = get_material_color(new_mat)
    old_color = get_material_color(old_mat)
    
    # If colors match (with small tolerance), reuse the old material
    if new_color and old_color:
        diff = sum(abs(a - b) for a, b in zip(new_color, old_color))
        if diff < 0.001:
            obj.active_material = old_mat
            # Remove the newly created material if it has no other users
            if new_mat.users <= 1:
                bpy.data.materials.remove(new_mat)
            return True
            
    return False
