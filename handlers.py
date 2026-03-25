import bpy
import time
from bpy.app.handlers import persistent
from mathutils import Vector

@persistent
def load_handler(dummy):
    """Handler for file load"""
    from . import generate_previews
    generate_previews()
    
    try:
        # Initialize live update
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    with bpy.context.temp_override(window=window, screen=window.screen, area=area):
                        bpy.ops.object.live_update()
    except Exception as e:
        print(f"VectArt load handler error: {str(e)}")

@persistent
def scene_update_handler(scene):
    """Handle scene updates (driven by timer or frame change)"""
    try:
        # scene_update_handler is not standard in Blender 2.8+ like this, 
        # usually it's depsgraph_update_post, but we had it in original code.
        # Let's keep the logic but it might need to be called differently.
        if not scene.vectart_props.live_update_enabled:
            return
            
        update_settings = scene.vectart_update_settings
        if not update_settings.is_updating:
            return
            
        current_time = time.time()
        if current_time - update_settings.last_update < update_settings.update_delay:
            return
            
        # Update all vectart objects
        for obj in scene.objects:
            if obj.get("is_vectart"):
                update_vectart_object(obj, scene)
                
        update_settings.is_updating = False
        update_settings.last_update = current_time
        
    except Exception as e:
        print(f"Scene update error: {str(e)}")

def update_vectart_object(obj, scene):
    """Update individual vectart object"""
    try:
        props = scene.vectart_props
        layer_idx = obj.get("vectart_layer", 0)
        
        if layer_idx >= len(props.layers):
            return
            
        layer = props.layers[layer_idx]
        if not layer.active:
            return
            
        # Update object properties
        if obj.type == 'CURVE':
            obj.data.extrude = layer.settings.extrude_height
            obj.data.bevel_depth = props.bevel_depth
            obj.data.bevel_resolution = props.bevel_resolution
            # Update splines
            for spline in obj.data.splines:
                spline.use_cyclic_u = props.use_cyclic
                
        # Update transforms
        obj.location.z = props.get_layer_offset(layer_idx)
        obj.scale = Vector((layer.settings.scale,) * 3)
        
    except Exception as e:
        print(f"Object update error: {str(e)}")
