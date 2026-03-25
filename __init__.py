"""VectArt Import & Preview - Blender 5.1 Extension"""

import bpy
import os
from bpy.props import PointerProperty
from . import properties, operators, ui, handlers, utils

# Global preview collections
if "preview_collections" not in globals():
    preview_collections = {}

def generate_previews():
    """Generate preview icons for SVG files"""
    from .utils import get_base_path, normalize_path
    
    # Clear existing previews
    if "vectart_previews" in preview_collections:
        preview_collections["vectart_previews"].close()
        del preview_collections["vectart_previews"]
    
    pcoll = bpy.utils.previews.new()
    preview_collections["vectart_previews"] = pcoll
    enum_items = []
    
    try:
        # Check if context is valid
        if not bpy.context or not bpy.context.scene:
            return enum_items
            
        scene = bpy.context.scene
        if not hasattr(scene, 'vectart_library_props'):
            return enum_items
            
        props = scene.vectart_library_props
        base_path = get_base_path()
        
        if not props.current_folder or not base_path:
            return enum_items
            
        folder_path = normalize_path(os.path.join(base_path, props.current_folder))
        if not os.path.exists(folder_path):
            return enum_items
            
        for i, file in enumerate(sorted(os.listdir(folder_path))):
            if not file.lower().endswith('.svg'):
                continue
                
            filepath = normalize_path(os.path.join(folder_path, file))
            try:
                icon = pcoll.load(filepath, filepath, 'IMAGE')
                enum_items.append((filepath, os.path.splitext(file)[0], "", icon.icon_id, i))
            except Exception as e:
                print(f"Error loading preview for {file}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error generating previews: {str(e)}")
        return enum_items
    
    pcoll.enum_items = enum_items
    return enum_items

def clear_previews():
    """Properly cleanup preview collections"""
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

# Registration order is important
classes = (
    properties.VectartUpdateSettings,
    properties.VectartAddonPreferences,
    properties.VectartProceduralSettings,
    properties.VectartLayerSettings,
    properties.VectartLayerItem,
    properties.VectartFolderItem,
    properties.VectartLibraryProperties,
    properties.VectartProperties,
    
    operators.VECTART_OT_ImportSVG,
    operators.VECTART_OT_LiveUpdate,
    operators.VECTART_OT_ImportLibrarySVG,
    operators.VECTART_OT_RefreshLibrary,
    operators.VECTART_OT_AddLayer,
    operators.VECTART_OT_RemoveLayer,
    operators.VECTART_OT_ClearLayers,
    operators.VECTART_OT_ConvertAndClear,
    operators.VECTART_OT_MoveLayers,
    operators.VECTART_OT_SelectLayerCurves,
    operators.VECTART_OT_SelectAllCurves,
    operators.VECTART_OT_SelectLayer,
    operators.VECTART_OT_FocusSelected,
    operators.VECTART_OT_AssignToLayer,
    operators.VECTART_OT_DuplicateLayer,
    operators.VECTART_OT_SplitToLayers,
    operators.VECTART_OT_CreateEmpty,
    operators.VECTART_OT_EditSVG,
    operators.VECTART_OT_ReimportEditedSVG,
    operators.VECTART_OT_ExportCurvesAsSVG,
    operators.VECTART_OT_ReimportSVG,

    ui.VECTART_UL_LayerList,
    ui.VECTART_PT_LibraryPanel,
    ui.VECTART_PT_PreviewPanel,
    ui.VECTART_PT_LayerPanel,
    ui.VECTART_PT_LayerTools,
    ui.VECTART_MT_SelectionMenu,
    ui.VECTART_PT_SVGEditorPanel,
    ui.VECTART_PT_GlobalSettingsHelp
)

def register():
    """Register all classes and properties"""
    # 1. Register classes
    for cls in classes:
        bpy.utils.register_class(cls)

    # 2. Register properties
    bpy.types.Scene.vectart_library_props = PointerProperty(type=properties.VectartLibraryProperties)
    bpy.types.Scene.vectart_props = PointerProperty(type=properties.VectartProperties)
    bpy.types.Scene.vectart_update_settings = PointerProperty(type=properties.VectartUpdateSettings)

    # 3. Add to UI menus
    bpy.types.VIEW3D_MT_object_context_menu.append(ui.draw_selection_menu)

    # 4. Register handlers
    if handlers.load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(handlers.load_handler)
    if handlers.scene_update_handler not in bpy.app.handlers.depsgraph_update_post:
        # Use depsgraph_update_post as the standard Blender update handler
        bpy.app.handlers.depsgraph_update_post.append(handlers.scene_update_handler)

    # 5. Initialize previews
    generate_previews()

    print("VectArt Extension (Modular) registered")

def unregister():
    """Unregister all classes and properties"""
    # 1. Stop background processes
    from .watcher import VectArtFileWatcher
    VectArtFileWatcher.stop()
    
    # 2. Remove from UI menus
    bpy.types.VIEW3D_MT_object_context_menu.remove(ui.draw_selection_menu)

    # 2. Remove handlers
    if handlers.load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(handlers.load_handler)
    if handlers.scene_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(handlers.scene_update_handler)

    # 3. Clear previews
    clear_previews()

    # 4. Remove properties
    del bpy.types.Scene.vectart_update_settings
    del bpy.types.Scene.vectart_library_props
    del bpy.types.Scene.vectart_props

    # 5. Unregister classes in reverse
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    print("VectArt Extension (Modular) unregistered")

if __name__ == "__main__":
    register()
