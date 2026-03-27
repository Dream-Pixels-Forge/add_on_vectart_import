import bpy
import os
import sys
import subprocess
import tempfile
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty
from bpy.types import Operator
from mathutils import Vector
from .utils import (
    get_layer_curves, 
    find_svg_editor_path, 
    get_objects_bounding_box,
    normalize_path,
    match_and_cleanup_material
)

# Global session storage for SVG edit/export workflow
_vectart_session = {}

class VECTART_OT_ImportSVG(Operator):
    bl_idname = "object.import_svg"
    bl_label = "Import SVG"
    bl_description = "Import SVG file"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        subtype='FILE_PATH',
        default=""
    )
    filter_glob: StringProperty(default="*.svg", options={'HIDDEN'})

    def auto_assign_layer(self, context, curves):
        try:
            props = context.scene.vectart_props
            if len(props.layers) == 0:
                bpy.ops.object.add_layer()
            
            for curve_obj in curves:
                # Find closest layer by Z position
                z_pos = curve_obj.location.z
                closest_layer_idx = 0
                smallest_diff = float('inf')
                
                for idx, layer in enumerate(props.layers):
                    layer_z = props.get_layer_offset(idx)
                    diff = abs(z_pos - layer_z)
                    if diff < smallest_diff:
                        smallest_diff = diff
                        closest_layer_idx = idx
                
                curve_obj["vectart_layer"] = closest_layer_idx
                curve_obj["is_vectart"] = True
                
                # Apply layer settings
                layer = props.layers[closest_layer_idx]
                curve_obj.data.extrude = layer.settings.extrude_height
                curve_obj.scale = Vector((layer.settings.scale,) * 3)
                curve_obj.location.z = props.get_layer_offset(closest_layer_idx)
        except Exception as e:
            print(f"Error in auto_assign_layer: {str(e)}")

    def execute(self, context):
        if not self.filepath or not os.path.exists(self.filepath):
            self.report({'ERROR'}, f"SVG file not found: {self.filepath}")
            return {'CANCELLED'}
            
        try:
            # Store existing objects to find new ones
            existing = set(bpy.data.objects[:])
            
            # Use the standard SVG importer (Curve based)
            try:
                bpy.ops.import_curve.svg(filepath=self.filepath)
            except AttributeError:
                self.report({'ERROR'}, "SVG Importer (import_curve.svg) not found. Please enable the 'Scalable Vector Graphics (SVG)' extension.")
                return {'CANCELLED'}

            new_objs = set(bpy.data.objects[:]) - existing
            imported_curves = [obj for obj in new_objs if obj.type == 'CURVE']
            
            if not imported_curves:
                self.report({'WARNING'}, "No curves were imported from the SVG.")
                return {'CANCELLED'}
            
            props = context.scene.vectart_props
            for curve in imported_curves:
                if hasattr(curve.data, "bevel_depth"):
                    curve.data.bevel_depth = props.bevel_depth
                    curve.data.bevel_resolution = props.bevel_resolution
                for spline in curve.data.splines:
                    spline.use_cyclic_u = props.use_cyclic
            
            self.auto_assign_layer(context, imported_curves)
            self.report({'INFO'}, f"Imported {len(imported_curves)} curves")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class VECTART_OT_LiveUpdate(Operator):
    bl_idname = "object.live_update"
    bl_label = "Live Update"
    bl_description = "Toggle live update mode"
    
    def execute(self, context):
        props = context.scene.vectart_props
        props.live_update_enabled = not props.live_update_enabled
        return {'FINISHED'}

class VECTART_OT_ImportLibrarySVG(Operator):
    bl_idname = "object.import_library_svg"
    bl_label = "Import Library SVG"
    bl_description = "Import selected SVG from library"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.vectart_library_props
        vprops = context.scene.vectart_props
        
        if not props.preview_index or not os.path.exists(props.preview_index):
            self.report({'ERROR'}, f"Selected SVG file not found: {props.preview_index}")
            return {'CANCELLED'}
            
        try:
            # Store existing objects to find new ones
            existing = set(bpy.data.objects[:])
            
            # Use the standard SVG importer (Curve based) which is the basis for VectArt's processing
            try:
                bpy.ops.import_curve.svg(filepath=props.preview_index)
            except AttributeError:
                self.report({'ERROR'}, "SVG Importer (import_curve.svg) not found. Please enable the 'Scalable Vector Graphics (SVG)' extension.")
                return {'CANCELLED'}

            new_objs = set(bpy.data.objects[:]) - existing
            curves = [obj for obj in new_objs if obj.type == 'CURVE']
            
            if not curves:
                self.report({'WARNING'}, "No curves were imported from the SVG.")
                return {'CANCELLED'}
            
            # Initial setup for imported curves
            bpy.ops.object.select_all(action='DESELECT')
            for c in curves:
                c.select_set(True)
                # Apply base settings
                c.scale = Vector((vprops.scale_factor,) * 3)
                if hasattr(c.data, "bevel_depth"):
                    c.data.bevel_depth = vprops.bevel_depth
                    c.data.bevel_resolution = vprops.bevel_resolution
                for s in c.data.splines:
                    s.use_cyclic_u = vprops.use_cyclic
            
            # Apply transforms before engine-specific processing
            context.view_layer.objects.active = curves[0]
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            
            if vprops.engine_type == 'GREASEPENCIL':
                from .gp_utils import convert_curves_to_gpv3
                gp_obj = convert_curves_to_gpv3(curves, target_collection=context.collection)
                
                if gp_obj:
                    # Deselect everything first
                    bpy.ops.object.select_all(action='DESELECT')
                    # Select original curves for deletion
                    for c in curves:
                        if c.name in bpy.data.objects:
                            c.select_set(True)
                    
                    # Safer to use operator for removal as it handles selection/unlinking better
                    bpy.ops.object.delete()
                    
                    # Now set the new GP object as active
                    context.view_layer.objects.active = gp_obj
                    gp_obj.select_set(True)
                else:
                    self.report({'ERROR'}, "Grease Pencil conversion failed.")
                    return {'CANCELLED'}
            else:
                bpy.ops.object.split_to_layers()
                
            bpy.ops.object.focus_selected()
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Import error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}

class VECTART_OT_RefreshLibrary(Operator):
    bl_idname = "object.refresh_library"
    bl_label = "Refresh Library"
    
    def execute(self, context):
        from . import generate_previews
        generate_previews()
        return {'FINISHED'}

class VECTART_OT_AddLayer(Operator):
    bl_idname = "object.add_layer"
    bl_label = "Add Layer"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        props = context.scene.vectart_props
        layer = props.layers.add()
        layer.name = f"Layer {len(props.layers)}"
        props.active_layer_index = len(props.layers) - 1
        return {'FINISHED'}

class VECTART_OT_RemoveLayer(Operator):
    bl_idname = "object.remove_layer"
    bl_label = "Remove Layer"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        props = context.scene.vectart_props
        if 0 <= props.active_layer_index < len(props.layers):
            curves = get_layer_curves(props.active_layer_index)
            for c in curves: bpy.data.objects.remove(c, do_unlink=True)
            props.layers.remove(props.active_layer_index)
            props.active_layer_index = max(0, props.active_layer_index - 1)
        return {'FINISHED'}

class VECTART_OT_MoveLayers(Operator):
    bl_idname = "object.move_layers"
    bl_label = "Move Layer"
    direction: EnumProperty(items=[('UP','Up',''),('DOWN','Down','')])
    def execute(self, context):
        props = context.scene.vectart_props
        idx = props.active_layer_index
        if self.direction == 'UP' and idx > 0:
            props.layers.move(idx, idx - 1)
            props.active_layer_index -= 1
        elif self.direction == 'DOWN' and idx < len(props.layers)-1:
            props.layers.move(idx, idx + 1)
            props.active_layer_index += 1
        return {'FINISHED'}

class VECTART_OT_ClearLayers(Operator):
    bl_idname = "object.clear_layers"
    bl_label = "Clear Layers"
    def execute(self, context):
        context.scene.vectart_props.layers.clear()
        return {'FINISHED'}

class VECTART_OT_ConvertAndClear(Operator):
    bl_idname = "object.convert_and_clear"
    bl_label = "Convert to Mesh"
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event, message="Convert to mesh?")
    def execute(self, context):
        props = context.scene.vectart_props
        curves = []
        for i, l in enumerate(props.layers):
            if l.active: curves.extend(get_layer_curves(i))
        if not curves: return {'CANCELLED'}
        bpy.ops.object.select_all(action='DESELECT')
        for c in curves: c.select_set(True)
        context.view_layer.objects.active = curves[0]
        bpy.ops.object.convert(target='MESH')
        props.layers.clear()
        return {'FINISHED'}

class VECTART_OT_SelectAllCurves(Operator):
    bl_idname = "object.select_all_curves"
    bl_label = "Select All Curves"
    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        coll = context.view_layer.active_layer_collection.collection
        count = 0
        for obj in coll.objects:
            if obj.type == 'CURVE':
                obj.select_set(True)
                count += 1
        if count: self.report({'INFO'}, f"Selected {count} curves")
        return {'FINISHED'}

class VECTART_OT_CreateEmpty(Operator):
    bl_idname = "object.create_empty"
    bl_label = "Create Empty Parent"
    use_bounding_box: BoolProperty(name="Match Bounding Box", default=True)
    def execute(self, context):
        props = context.scene.vectart_props
        objs = [o for o in context.selected_objects if o.type in {'CURVE', 'MESH'}]
        if not objs: return {'CANCELLED'}
        
        # Center pivots
        for o in objs:
            bpy.ops.object.select_all(action='DESELECT')
            o.select_set(True)
            context.view_layer.objects.active = o
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            
        bbox = get_objects_bounding_box(objs)
        bpy.ops.object.empty_add(type=props.empty_type, location=bbox['center'])
        empty = context.active_object
        empty.name = props.empty_name
        if self.use_bounding_box:
            dim = bbox['dimensions']
            if props.empty_type in {'CUBE', 'SPHERE'}:
                empty.scale = Vector((dim.x/2, dim.y/2, dim.z/2))
            else:
                empty.empty_display_size = max(dim)/2
        
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs: o.select_set(True)
        empty.select_set(True)
        context.view_layer.objects.active = empty
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
        return {'FINISHED'}

class VECTART_OT_SelectLayerCurves(Operator):
    bl_idname = "object.select_layer_curves"
    bl_label = "Select Layer Curves"
    def execute(self, context):
        props = context.scene.vectart_props
        bpy.ops.object.select_all(action='DESELECT')
        curves = get_layer_curves(props.active_layer_index)
        for c in curves: c.select_set(True)
        if curves: context.view_layer.objects.active = curves[0]
        return {'FINISHED'}

class VECTART_OT_AssignToLayer(Operator):
    bl_idname = "object.assign_to_layer"
    bl_label = "Assign to Layer"
    def execute(self, context):
        props = context.scene.vectart_props
        idx = props.active_layer_index
        layer = props.layers[idx]
        curves = [o for o in context.selected_objects if o.type == 'CURVE']
        for c in curves:
            c["is_vectart"] = True
            c["vectart_layer"] = idx
            c.data.extrude = layer.settings.extrude_height
            c.scale = Vector((layer.settings.scale,) * 3)
            c.location.z = props.get_layer_offset(idx)
        return {'FINISHED'}

class VECTART_OT_DuplicateLayer(Operator):
    bl_idname = "object.duplicate_layer"
    bl_label = "Duplicate Layer"
    def execute(self, context):
        props = context.scene.vectart_props
        src_idx = props.active_layer_index
        src_layer = props.layers[src_idx]
        new_layer = props.layers.add()
        new_idx = len(props.layers)-1
        new_layer.name = f"{src_layer.name}_copy"
        
        curves = get_layer_curves(src_idx)
        for c in curves:
            nc = c.copy()
            nc.data = c.data.copy()
            nc["vectart_layer"] = new_idx
            context.scene.collection.objects.link(nc)
        props.active_layer_index = new_idx
        return {'FINISHED'}

class VECTART_OT_SplitToLayers(Operator):
    bl_idname = "object.split_to_layers"
    bl_label = "Split to Layers"
    def execute(self, context):
        props = context.scene.vectart_props
        curves = [o for o in context.selected_objects if o.type == 'CURVE']
        for c in curves:
            l = props.layers.add()
            idx = len(props.layers)-1
            l.name = f"Layer {idx+1} ({c.name})"
            c["is_vectart"] = True
            c["vectart_layer"] = idx
            c.location.z = props.get_layer_offset(idx)
        props.active_layer_index = len(props.layers)-1
        return {'FINISHED'}

class VECTART_OT_SelectLayer(Operator):
    bl_idname = "object.select_layer"
    bl_label = "Select Layer"
    layer_index: IntProperty()
    def execute(self, context):
        props = context.scene.vectart_props
        bpy.ops.object.select_all(action='DESELECT')
        curves = get_layer_curves(self.layer_index)
        for c in curves:
            c.select_set(True)
            c.hide_viewport = False
        if curves: context.view_layer.objects.active = curves[0]
        props.active_layer_index = self.layer_index
        return {'FINISHED'}

class VECTART_OT_FocusSelected(Operator):
    bl_idname = "object.focus_selected"
    bl_label = "Focus Selected"
    def execute(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                with context.temp_override(area=area):
                    bpy.ops.view3d.view_selected()
        return {'FINISHED'}

class VECTART_OT_EditSVG(Operator):
    bl_idname = "object.edit_svg"
    bl_label = "Edit in SVG Editor"
    def execute(self, context):
        props = context.scene.vectart_props
        coll = context.view_layer.active_layer_collection.collection
        curves = [o for o in coll.objects if o.type == 'CURVE']
        if not curves: return {'CANCELLED'}
        
        settings = []
        for o in curves:
            # Store material info to preserve custom shaders
            mat_name = o.active_material.name if o.active_material else None
            
            settings.append({
                "name": o.name,
                "vectart_layer": o.get("vectart_layer"),
                "is_vectart": o.get("is_vectart"),
                "bevel_depth": o.data.bevel_depth,
                "bevel_resolution": o.data.bevel_resolution,
                "extrude": o.data.extrude,
                "scale": tuple(o.scale),
                "location": tuple(o.location),
                "material_name": mat_name,
            })
            
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
            svg_path = tmp.name
            
        dups = []
        try:
            for o in curves:
                d = o.copy()
                d.data = o.data.copy()
                context.collection.objects.link(d)
                d.data.dimensions = '3D'
                dups.append(d)
            bpy.ops.object.select_all(action='DESELECT')
            for d in dups: d.select_set(True)
            context.view_layer.objects.active = dups[0]
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            bpy.ops.export_svg_format.svg(filepath=svg_path)
        finally:
            bpy.ops.object.delete()
            
        editor = props.svg_editor_path or find_svg_editor_path(props.svg_editor_type)
        if not editor: return {'CANCELLED'}
        
        try:
            subprocess.Popen([editor, svg_path])
            _vectart_session.update({
                "svg_edit_path": svg_path,
                "svg_edit_settings": settings,
                "svg_edit_collection": coll.name
            })
            
            # Start watching this file for changes
            from .watcher import VectArtFileWatcher
            VectArtFileWatcher.watch_file(svg_path)
            VectArtFileWatcher.start()
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

class VECTART_OT_ReimportEditedSVG(Operator):
    bl_idname = "object.reimport_edited_svg"
    bl_label = "Reimport Edited SVG"
    def execute(self, context):
        path = _vectart_session.get("svg_edit_path")
        settings = _vectart_session.get("svg_edit_settings")
        coll_name = _vectart_session.get("svg_edit_collection")
        if not path: return {'CANCELLED'}
        
        coll = bpy.data.collections.get(coll_name)
        if not coll: return {'CANCELLED'}
        
        # 1. Store existing materials mapping by name
        existing_mats = {m.name: m for m in bpy.data.materials}
        
        # 2. Cleanup old curves
        for o in [o for o in coll.objects if o.type == 'CURVE']:
            bpy.data.objects.remove(o, do_unlink=True)
            
        # 3. Import updated SVG
        existing_objs = set(bpy.data.objects[:])
        
        try:
            bpy.ops.import_curve.svg(filepath=path)
        except AttributeError:
            self.report({'ERROR'}, "SVG Importer (import_curve.svg) not found.")
            return {'CANCELLED'}

        imported = [o for o in (set(bpy.data.objects[:]) - existing_objs) if o.type == 'CURVE']
        
        # 4. Map back to layers and restore materials if possible
        for i, o in enumerate(imported):
            if i < len(settings):
                s = settings[i]
                o.name = s["name"]
                o["vectart_layer"] = s["vectart_layer"]
                o["is_vectart"] = s["is_vectart"]
                
                # Apply stored curve settings
                o.data.bevel_depth = s["bevel_depth"]
                o.data.bevel_resolution = s["bevel_resolution"]
                o.data.extrude = s["extrude"]
                o.scale = s["scale"]
                o.location = s["location"]
                
                # Material and Color Preservation:
                if s["material_name"]:
                    # This helper compares the new imported material color with the original.
                    # If colors are same, it reuses original and deletes the redundant new material.
                    match_and_cleanup_material(o, s["material_name"])
                
            if o.name not in coll.objects:
                coll.objects.link(o)
            
        # Clean up watcher
        from .watcher import VectArtFileWatcher
        VectArtFileWatcher.unwatch_file(path)
        
        return {'FINISHED'}

# Restored and Fixed Export/Reimport Operators
class VECTART_OT_ExportCurvesAsSVG(Operator):
    bl_idname = "object.export_curves_svg"
    bl_label = "Export Selected as SVG"
    bl_description = "Export selected curves with applied transforms for external editors"
    
    filepath: StringProperty(subtype='FILE_PATH')
    
    def execute(self, context):
        curves = [o for o in context.selected_objects if o.type == 'CURVE']
        if not curves: return {'CANCELLED'}
        
        # 1. Store original states
        originals = []
        for o in curves:
            originals.append({
                "obj": o,
                "matrix": o.matrix_world.copy(),
                "dimensions": o.data.dimensions
            })
        
        # 2. Prepare for export: Set to 3D and apply transforms
        dups = []
        try:
            for o in curves:
                d = o.copy()
                d.data = o.data.copy()
                context.collection.objects.link(d)
                d.data.dimensions = '3D' # Essential for transform_apply
                dups.append(d)
            
            bpy.ops.object.select_all(action='DESELECT')
            for d in dups: d.select_set(True)
            context.view_layer.objects.active = dups[0]
            
            # Apply all transforms to normalize coordinates for SVG
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            
            # Export using Blender's built-in SVG exporter
            bpy.ops.export_svg_format.svg(filepath=self.filepath)
            self.report({'INFO'}, f"Exported {len(curves)} curves to {os.path.basename(self.filepath)}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
        finally:
            # Cleanup duplicates
            bpy.ops.object.delete()
            # Restore selection
            for o in curves: o.select_set(True)
            
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "exported_vectart.svg"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class VECTART_OT_ReimportSVG(Operator):
    bl_idname = "object.reimport_svg"
    bl_label = "Reimport SVG"
    bl_description = "Reimport SVG and map back to existing layers"
    
    filepath: StringProperty(subtype='FILE_PATH')
    
    def execute(self, context):
        if not os.path.exists(self.filepath): 
            self.report({'ERROR'}, "File not found")
            return {'CANCELLED'}
            
        props = context.scene.vectart_props
        
        try:
            # 1. Track imported objects
            before = set(bpy.data.objects[:])
            
            try:
                bpy.ops.import_curve.svg(filepath=self.filepath)
            except AttributeError:
                self.report({'ERROR'}, "SVG Importer (import_curve.svg) not found.")
                return {'CANCELLED'}

            after = set(bpy.data.objects[:])
            imported = [o for o in (after - before) if o.type == 'CURVE']
            
            if not imported:
                self.report({'WARNING'}, "No curves found in SVG")
                return {'FINISHED'}

            # 2. Automated Layer Mapping
            # If we have 10 curves and 1 layer, assign all to layer 0
            # If we have 10 curves and 10 layers, assign each to its index
            for i, o in enumerate(imported):
                layer_idx = i if i < len(props.layers) else 0
                o["is_vectart"] = True
                o["vectart_layer"] = layer_idx
                
                # Apply current layer settings
                layer = props.layers[layer_idx]
                o.data.extrude = layer.settings.extrude_height
                o.scale = Vector((layer.settings.scale,) * 3)
                o.location.z = props.get_layer_offset(layer_idx)
                
            self.report({'INFO'}, f"Reimported {len(imported)} curves")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Reimport failed: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
