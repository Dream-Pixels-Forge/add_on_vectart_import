import bpy

def convert_curves_to_gpv3(curves, target_collection=None):
    """
    Convert a list of curve objects to a single Grease Pencil v3 object.
    Each curve becomes a separate layer or stroke in GPv3.
    """
    if not curves:
        return None
        
    # Create a new GPv3 object
    # In 5.1, 'GREASEPENCIL' is the type for GPv3
    gp_data = bpy.data.grease_pencils.new("VectArt_GP")
    gp_obj = bpy.data.objects.new("VectArt_GP", gp_data)
    
    if target_collection:
        target_collection.objects.link(gp_obj)
    else:
        bpy.context.collection.objects.link(gp_obj)
        
    # GPv3 uses 'layers' similar to curves but more advanced
    for i, curve_obj in enumerate(curves):
        layer_name = curve_obj.name
        # Ensure we don't duplicate layers if they exist
        gp_layer = gp_data.layers.get(layer_name) or gp_data.layers.new(layer_name)
        
        # In GPv3, we add frames and drawings
        # In newer API versions (4.3+), we must create a drawing and assign it
        frame = gp_layer.frames.new(1)
        
        # Check if drawing exists or needs to be created
        drawing = getattr(frame, "drawing", None)
        if drawing is None:
            # Create a new drawing in the grease_pencil_drawings collection
            # Note: The exact collection name might vary by dev version, but 'drawings' is common
            if hasattr(gp_data, "drawings"):
                drawing = gp_data.drawings.new("Drawing")
                frame.drawing = drawing
            elif hasattr(bpy.data, "grease_pencil_drawings"):
                drawing = bpy.data.grease_pencil_drawings.new("Drawing")
                frame.drawing = drawing
        
        if not drawing:
            print(f"Warning: Could not create/access GPv3 drawing for layer {layer_name}")
            continue

        # Convert curve splines to GP strokes
        for spline in curve_obj.data.splines:
            # Newer API uses add_stroke() or similar if new() is not available
            if hasattr(drawing.strokes, "new"):
                stroke = drawing.strokes.new()
            else:
                # Fallback for alternative GPv3 implementations
                stroke = drawing.add_stroke() if hasattr(drawing, "add_stroke") else None
            
            if not stroke: continue
            
            # Transfer points and handle handles for Bezier
            points = []
            if spline.type == 'BEZIER':
                # For GPv3 we sample the bezier or just take the points
                # For simplicity we take the points, but sampling is better for "smooth" looks
                for bp in spline.bezier_points:
                    points.append(bp.co)
            else:
                for p in spline.points:
                    points.append(p.co[:3])
            
            if not points: continue
            
            stroke.points.add(len(points))
            for j, co in enumerate(points):
                stroke.points[j].co = co
                
            stroke.use_cyclic = spline.use_cyclic_u
            
    # Apply global settings from properties
    props = bpy.context.scene.vectart_props
    
    # Try different modifier type identifiers for GPv3
    mod_type = 'GREASE_PENCIL_THICKNESS'
    # In 5.1/4.3+, it might be simplified or renamed
    if not hasattr(bpy.types, "GreasePencilThicknessModifier"):
        if hasattr(bpy.types, "ThicknessModifier"):
            mod_type = 'THICKNESS'
    
    try:
        mod = gp_obj.modifiers.new(name="Thickness", type=mod_type)
        mod.thickness = props.gp_thickness
    except Exception as e:
        print(f"Warning: Could not add thickness modifier: {str(e)}")
            
    return gp_obj

def apply_gpv3_modifiers(gp_obj):
    """Add standard GPv3 modifiers for SVG-like rendering"""
    if not gp_obj:
        return
        
    # 1. Fill modifier (if needed)
    # 2. Thickness modifier
    # 3. Build modifier for animation
    pass
