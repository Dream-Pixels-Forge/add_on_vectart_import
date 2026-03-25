import bpy
import os
from bpy.props import (StringProperty, 
                      BoolProperty,
                      EnumProperty, 
                      FloatProperty, 
                      IntProperty,
                      CollectionProperty,
                      PointerProperty)
from bpy.types import (PropertyGroup, AddonPreferences)
from mathutils import Vector
from .utils import get_base_path, normalize_path, get_layer_curves

def update_editor_path(self, context):
    """Update editor path when type changes"""
    from .utils import find_svg_editor_path
    if self.svg_editor_type != 'CUSTOM':
        path = find_svg_editor_path(self.svg_editor_type)
        if path:
            self.svg_editor_path = path

def update_layer_settings(self, context):
    """Update settings for curves in the layer (Standard, Procedural, or GPv3)"""
    if not context.scene.vectart_props.live_update_enabled:
        return
        
    try:
        props = context.scene.vectart_props
        layer_idx = -1
        is_proc_sub_update = hasattr(self, "extrude") # VectartProceduralSettings
        
        for idx, layer in enumerate(props.layers):
            if layer.settings == self or (is_proc_sub_update and layer.settings.procedural == self):
                layer_idx = idx
                break
                
        if layer_idx == -1: return
            
        layer = props.layers[layer_idx]
        curves = get_layer_curves(layer_idx)
        
        for curve in curves:
            if curve.type == 'CURVE':
                if props.engine_type == 'PROCEDURAL':
                    from .gn_utils import apply_vectart_gn, sync_gn_properties
                    apply_vectart_gn(curve)
                    sync_gn_properties(curve, layer.settings.procedural.extrude, props.get_layer_offset(layer_idx), layer.settings.procedural.bevel_size)
                elif props.engine_type == 'STANDARD':
                    curve.scale = Vector((layer.settings.scale,) * 3)
                    curve.data.extrude = layer.settings.extrude_height
                    curve.location.z = props.get_layer_offset(layer_idx)
                    curve.data.bevel_depth = props.bevel_depth
                    curve.data.bevel_resolution = props.bevel_resolution
                
    except Exception as e:
        print(f"Error updating layer settings: {str(e)}")

def update_curve_properties(self, context):
    """Update all curve properties (Global)"""
    if not context.scene.vectart_props.live_update_enabled:
        return
    try:
        props = context.scene.vectart_props
        for idx, layer in enumerate(props.layers):
            if layer.active:
                curves = get_layer_curves(idx)
                for curve in curves:
                    if curve.type == 'CURVE' and props.engine_type != 'GREASEPENCIL':
                        if props.engine_type == 'PROCEDURAL':
                            from .gn_utils import sync_gn_properties
                            sync_gn_properties(curve, layer.settings.procedural.extrude, props.get_layer_offset(idx), layer.settings.procedural.bevel_size)
                        else:
                            curve.data.bevel_depth = props.bevel_depth
                            curve.data.bevel_resolution = props.bevel_resolution
    except Exception as e:
        print(f"Error updating curve properties: {str(e)}")

def update_layer_visibility(self, context):
    """Update curve visibility when layer visibility changes"""
    try:
        layer_idx = context.scene.vectart_props.active_layer_index
        curves = get_layer_curves(layer_idx)
        for curve in curves:
            curve.hide_viewport = not self.active
            curve.hide_render = not self.active
    except Exception as e:
        print(f"Error updating visibility: {str(e)}")

def update_all_layers(self, context):
    """Update all layers when global settings change"""
    if not context.scene.vectart_props.live_update_enabled:
        return
    try:
        props = context.scene.vectart_props
        for idx, layer in enumerate(props.layers):
            if layer.active:
                curves = get_layer_curves(idx)
                for curve in curves:
                    if curve.type == 'CURVE':
                        if props.engine_type == 'PROCEDURAL':
                            from .gn_utils import sync_gn_properties
                            sync_gn_properties(curve, layer.settings.procedural.extrude, props.get_layer_offset(idx), layer.settings.procedural.bevel_size)
                        elif props.engine_type == 'STANDARD':
                            curve.location.z = props.get_layer_offset(idx)
    except Exception as e:
        print(f"Error updating layers: {str(e)}")

def update_z_offset(self, context):
    """Update z positions when z_offset changes"""
    if not context.scene.vectart_props.live_update_enabled:
        return
    try:
        props = context.scene.vectart_props
        layer_idx = -1
        is_proc_sub = hasattr(self, "z_offset") and not hasattr(self, "scale")
        for idx, layer in enumerate(props.layers):
            if layer.settings == self or (is_proc_sub and layer.settings.procedural == self):
                layer_idx = idx
                break
        if layer_idx == -1: return
        for idx in range(layer_idx, len(props.layers)):
            curves = get_layer_curves(idx)
            for curve in curves:
                if curve.type == 'CURVE':
                    if props.engine_type == 'PROCEDURAL':
                        from .gn_utils import sync_gn_properties
                        sync_gn_properties(curve, props.layers[idx].settings.procedural.extrude, props.get_layer_offset(idx), props.layers[idx].settings.procedural.bevel_size)
                    elif props.engine_type == 'STANDARD':
                        curve.location.z = props.get_layer_offset(idx)  
    except Exception as e:
        print(f"Error updating z offset: {str(e)}")

def update_layer_selection(self, context):
    """Update selection when active layer changes"""
    if hasattr(context, 'scene'):
        bpy.ops.object.select_layer(layer_index=self.active_layer_index)

def get_subfolders(self, context):
    """Get list of subfolders in the library path"""
    items = []
    try:
        path = get_base_path()
        if path and os.path.exists(path):
            folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
            items = [(f, f, "") for f in sorted(folders)]
    except Exception as e:
        print(f"Error loading folders: {str(e)}")
    return items if items else [("", "No folders found", "")]

def get_preview_items(self, context):
    """Get preview items for SVG files"""
    from . import preview_collections
    pcoll = preview_collections.get("vectart_previews")
    if pcoll is None: return []
    return pcoll.enum_items if hasattr(pcoll, "enum_items") else []

class VectartAddonPreferences(AddonPreferences):
    bl_idname = __package__
    base_path: StringProperty(name="Library Path", subtype='DIR_PATH', default="", description="Base path for SVG library")
    def draw(self, context):
        self.layout.prop(self, "base_path")

class VectartUpdateSettings(PropertyGroup):
    is_updating: BoolProperty(default=False)
    last_update: FloatProperty(default=0.0)
    update_delay: FloatProperty(default=0.1, min=0.01)

class VectartProceduralSettings(PropertyGroup):
    """Procedural GN Settings for each layer"""
    extrude: FloatProperty(name="Extrude", default=0.05, min=0.0, update=update_layer_settings)
    z_offset: FloatProperty(name="Z Offset", default=0.0, update=update_z_offset)
    bevel_size: FloatProperty(name="Bevel", default=0.005, min=0.0, update=update_layer_settings)

class VectartLayerSettings(PropertyGroup):
    scale: FloatProperty(name="Scale", default=1.0, min=0.001, max=100.0, update=update_layer_settings)
    z_offset: FloatProperty(name="Z Offset", default=0.0, description="Vertical position offset", update=update_z_offset)
    extrude_height: FloatProperty(name="Extrude Height", default=0.01, min=0.0, update=update_layer_settings)
    procedural: PointerProperty(type=VectartProceduralSettings)

class VectartLayerItem(PropertyGroup):
    name: StringProperty(name="Name", default="Layer")
    active: BoolProperty(name="Active", default=True, update=update_layer_visibility)
    settings: PointerProperty(type=VectartLayerSettings)

class VectartFolderItem(PropertyGroup):
    name: StringProperty()

class VectartLibraryProperties(PropertyGroup):
    current_folder: EnumProperty(name="Current Folder", items=get_subfolders, description="Select SVG folder") 
    preview_index: EnumProperty(items=get_preview_items, name="Preview Index")

class VectartProperties(PropertyGroup):
    layers: CollectionProperty(type=VectartLayerItem)
    active_layer_index: IntProperty(update=update_layer_selection)
    
    engine_type: EnumProperty(
        name="Engine",
        items=[
            ('STANDARD', "Standard", "Standard curve properties", 'CURVE_DATA', 0),
            ('PROCEDURAL', "Procedural", "Geometry Nodes engine", 'NODETREE', 1),
            ('GREASEPENCIL', "Grease Pencil", "Grease Pencil v3 engine", 'GREASEPENCIL', 2),
        ],
        default='PROCEDURAL'
    )
    
    base_z_offset: FloatProperty(name="Base Height", default=0.0, update=update_all_layers)
    layer_spacing: FloatProperty(name="Layer Gap", default=0.01, min=0.0, update=update_all_layers)
    scale_factor: FloatProperty(name="Scale Factor", default=10.0, min=0.01, max=100.0, update=update_all_layers)
    
    live_update_enabled: BoolProperty(name="Live Update", default=True)
    bevel_depth: FloatProperty(name="Bevel Depth", default=0.0002, update=update_curve_properties)
    bevel_resolution: IntProperty(name="Bevel Resolution", default=4, update=update_curve_properties)
    use_cyclic: BoolProperty(name="Use Cyclic", default=True, update=update_curve_properties)

    # GPv3 Specific
    gp_thickness: FloatProperty(name="Stroke Thickness", default=0.01, min=0.0)
    gp_use_fill: BoolProperty(name="Use Fills", default=True)

    empty_name: StringProperty(name="Name", default="VectArt_Group")
    empty_type: EnumProperty(
        name="Empty Type",
        items=[('PLAIN_AXES', "Plain Axes", ""), ('ARROWS', "Arrows", ""), ('SINGLE_ARROW', "Single Arrow", ""), 
               ('CIRCLE', "Circle", ""), ('CUBE', "Cube", ""), ('SPHERE', "Sphere", "")],
        default='CUBE'
    )

    svg_editor_type: EnumProperty(
        name="Editor Type",
        items=[('ILLUSTRATOR', "Illustrator", ""), ('AFFINITY', "Affinity", ""), 
               ('INKSCAPE', "Inkscape", ""), ('CUSTOM', "Custom", "")],
        default='INKSCAPE',
        update=update_editor_path
    )
    svg_editor_path: StringProperty(name="Editor Path", subtype='FILE_PATH')
    auto_update_svg: BoolProperty(name="Auto Update", default=True)
    show_global_help: BoolProperty(name="Show Help", default=False)
    
    def get_layer_offset(self, layer_index):
        base_offset = self.base_z_offset
        layer_offset = layer_index * self.layer_spacing
        for i in range(layer_index):
            if i < len(self.layers):
                l = self.layers[i]
                if l.active:
                    layer_offset += l.settings.z_offset
                    if self.engine_type == 'PROCEDURAL':
                        layer_offset += l.settings.procedural.z_offset
        return base_offset + layer_offset
