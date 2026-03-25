import bpy
import os
from bpy.types import Panel, UIList, Menu
from .utils import get_base_path, get_layer_curves

class VECTART_UL_LayerList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            icon = 'HIDE_OFF' if item.active else 'HIDE_ON'
            row.prop(item, "active", text="", icon=icon, emboss=False)
            row.prop(item, "name", text="", emboss=True, icon='GREASEPENCIL')
            if item.active:
                sub = row.row(align=True)
                sub.scale_x = 0.7
                sub.prop(item.settings, "extrude_height", text="")

class VECTART_PT_LibraryPanel(Panel):
    bl_label = "VectArt Library"
    bl_idname = "VECTART_PT_library"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VectArt'
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.vectart_library_props
        base_path = get_base_path()
        
        if not base_path:
            box = layout.box()
            col = box.column(align=True)
            col.label(text="Library path not set!", icon='ERROR')
            col.operator("preferences.addon_show", text="Open Preferences", icon='PREFERENCES').module = __package__
            return
            
        path_box = layout.box()
        path_box.row().label(text="Library Path:", icon='FILE_FOLDER')
        path_text = base_path if len(base_path) <= 30 else "..." + base_path[-27:]
        path_box.label(text=path_text)
            
        col = layout.column(align=True)
        col.separator(factor=0.5)
        box = col.box()
        box.label(text="SVG Collections", icon='OUTLINER_OB_GROUP_INSTANCE')
        box.row(align=True).prop_menu_enum(props, "current_folder", text=props.current_folder or "Select Folder")
        layout.row(align=True).operator("object.refresh_library", text="Refresh Library", icon='FILE_REFRESH')

class VECTART_PT_PreviewPanel(Panel):
    bl_label = "SVG Preview"
    bl_idname = "VECTART_PT_preview"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VectArt'
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.vectart_library_props
        vprops = context.scene.vectart_props
        base_path = get_base_path()  
        
        if not props.current_folder:
            layout.column().label(text="Select a folder to view SVGs", icon='INFO')
            return
            
        preview_box = layout.box()
        preview_box.label(text="Available SVGs:", icon='IMAGE_DATA')
        preview_box.row().template_icon_view(props, "preview_index", show_labels=True, scale=6, scale_popup=2)
        
        settings_box = layout.box()
        settings_box.row().prop(vprops, "scale_factor", text="Import Scale")

        col = layout.column(align=True)
        col.separator(factor=0.5)
        row = col.row(align=True)
        if props.preview_index:
            row.operator("object.import_library_svg", text="Import Selected", icon='IMPORT')
        row.operator("object.import_svg", icon='FILEBROWSER', text="Import New")

class VECTART_PT_LayerPanel(Panel):
    bl_label = "VectArt Layers"
    bl_idname = "VECTART_PT_layer_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VectArt"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.vectart_props  
        layout.row().prop(props, "live_update_enabled", text="Live Update", icon='AUTO', toggle=True)
        layout.separator(factor=0.7)
        box = layout.box()
        box.label(text="Layers", icon='OUTLINER_OB_LIGHTPROBE')
        row = box.row()
        row.template_list("VECTART_UL_LayerList", "", props, "layers", props, "active_layer_index", rows=6)
        
        col = row.column(align=True)
        col.operator("object.add_layer", icon='ADD', text="")
        col.operator("object.remove_layer", icon='REMOVE', text="")
        col.separator()
        col.operator("object.move_layers", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("object.move_layers", icon='TRIA_DOWN', text="").direction = 'DOWN'
        col.separator()
        col.operator("object.duplicate_layer", icon='DUPLICATE', text="")
        col.operator("object.clear_layers", icon='TRASH', text="")

        box = layout.box()
        row = box.row(align=True)
        row.operator("object.select_all_curves", icon='OUTLINER_OB_CURVE', text="Select All")
        row.operator("object.split_to_layers", icon='OUTLINER_OB_MESH', text="Split to Layers")
        row.operator("object.focus_selected", icon='ZOOM_SELECTED', text="Focus")
        
        layout.row().operator("object.convert_and_clear", text="Convert to Mesh", icon='MESH_DATA')
        
        box = layout.box()
        box.row().prop(props, "show_global_help", text="Global Settings", icon='WORLD', toggle=True)
        split = box.split()
        col1 = split.column(align=True); col1.use_property_split = True
        col1.prop(props, "base_z_offset", text="BH")
        col1.prop(props, "layer_spacing", text="LG")
        col2 = split.column(align=True); col2.use_property_split = True
        col2.prop(props, "bevel_depth", text="BD")
        col2.prop(props, "bevel_resolution", text="BR")
        col2.prop(props, "use_cyclic", text="UC")
        
class VECTART_PT_LayerTools(Panel):
    bl_label = "Layer Tools"
    bl_idname = "VECTART_PT_layer_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VectArt"
    bl_parent_id = "VECTART_PT_layer_panel"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.vectart_props
        
        # Engine Selection
        box = layout.box()
        row = box.row(align=True)
        row.prop(props, "engine_type", expand=True)
        
        if props.layers:
            layer = props.layers[props.active_layer_index]
            box = layout.box()
            box.label(text=f"Settings: {layer.name}", icon='OPTIONS')
            
            col = box.column(align=True); col.use_property_split = True
            
            if props.engine_type == 'PROCEDURAL':
                # GN Engine Controls
                col.prop(layer.settings.procedural, "extrude", text="Procedural Depth")
                col.prop(layer.settings.procedural, "bevel_size", text="Proc. Bevel")
                col.prop(layer.settings.procedural, "z_offset", text="Layer Z Offset")
            elif props.engine_type == 'GREASEPENCIL':
                # GPv3 Global Controls (since conversion is destructive to curves)
                col.label(text="GPv3 Settings (Global)", icon='GREASEPENCIL')
                col.prop(props, "gp_thickness", text="Stroke Thickness")
                col.prop(props, "gp_use_fill", text="Use Fills")
            else:
                # Standard Engine Controls
                col.prop(layer.settings, "scale", text="Scale")
                col.prop(layer.settings, "extrude_height", text="Extrude")
                col.prop(layer.settings, "z_offset", text="Z Offset")

        box = layout.box()
        box.label(text="Grouping Tools", icon='EMPTY_AXIS')
        col = box.column(align=True)
        col.row(align=True).prop(props, "empty_type", text="")
        col.row(align=True).prop(props, "empty_name", text="")
        col.operator("object.create_empty", icon='EMPTY_DATA', text="Create Empty Parent")

class VECTART_MT_SelectionMenu(Menu):
    bl_label = "VectArt Selection"
    bl_idname = "VECTART_MT_selection_menu"
    def draw(self, context):
        layout = self.layout
        layout.operator("object.select_all_curves", icon='OUTLINER_OB_CURVE')
        layout.operator("object.select_layer_curves", icon='LAYER_ACTIVE')
        layout.separator()
        layout.operator("object.assign_to_layer", icon='LAYER_ACTIVE')
        layout.operator("object.create_empty", icon='EMPTY_DATA')
        layout.operator("object.focus_selected", icon='ZOOM_SELECTED')
        
class VECTART_PT_SVGEditorPanel(Panel):
    bl_label = "SVG Editor Link"
    bl_idname = "VECTART_PT_svg_editor"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VectArt'
    def draw(self, context):
        layout = self.layout
        props = context.scene.vectart_props
        
        # External Editor Settings
        box = layout.box()
        box.label(text="External Editor", icon='GREASEPENCIL')
        box.prop(props, "svg_editor_type", text="Editor")
        box.prop(props, "svg_editor_path", text="Path")
        
        # Interactive Workflow
        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("object.edit_svg", icon='OUTLINER_OB_GREASEPENCIL', text="Edit Selection")
        row.operator("object.reimport_edited_svg", icon='FILE_REFRESH', text="Finish Edit")
        
        # Manual Export/Import
        layout.separator()
        box = layout.box()
        box.label(text="Manual Operations", icon='IMPORT')
        row = box.row(align=True)
        row.operator("object.export_curves_svg", text="Export SVG", icon='EXPORT')
        row.operator("object.reimport_svg", text="Reimport SVG", icon='IMPORT')

class VECTART_PT_GlobalSettingsHelp(Panel):
    bl_label = "Global Settings Help"
    bl_idname = "VECTART_PT_global_settings_help"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VectArt"
    bl_parent_id = "VECTART_PT_layer_panel"
    @classmethod
    def poll(cls, context):
        return getattr(context.scene.vectart_props, "show_global_help", False)
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="BH = Base Height"); box.label(text="LG = Layer Gap")
        box.label(text="BD = Bevel Depth"); box.label(text="BR = Bevel Resolution")
        box.label(text="UC = Use Cyclic")

def draw_selection_menu(self, context):
    self.layout.separator()
    self.layout.menu(VECTART_MT_SelectionMenu.bl_idname, icon='RESTRICT_SELECT_OFF')
