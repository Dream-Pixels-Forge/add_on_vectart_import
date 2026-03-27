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
        mat = curve_obj.matrix_world
        for spline in curve_obj.data.splines:
            # Newer API uses add_stroke() or similar if new() is not available
            stroke = None
            if hasattr(drawing.strokes, "new"):
                stroke = drawing.strokes.new()
            elif hasattr(drawing, "add_stroke"):
                stroke = drawing.add_stroke()
            
            if not stroke: continue
            
            # Transfer points with sampling for Bezier for better visual results
            points_coords = []
            if spline.type == 'BEZIER':
                # Higher resolution for bezier sampling
                resolution = spline.resolution_u
                # Simple sampling: for each segment, get intermediate points
                for i in range(len(spline.bezier_points) - (0 if spline.use_cyclic_u else 1)):
                    p1 = spline.bezier_points[i]
                    p2 = spline.bezier_points[(i + 1) % len(spline.bezier_points)]
                    
                    # Add points for this segment
                    for step in range(resolution):
                        t = step / resolution
                        # Cubic Bezier formula
                        c0 = (1-t)**3
                        c1 = 3*t*(1-t)**2
                        c2 = 3*t**2*(1-t)
                        c3 = t**3
                        
                        co = (p1.co * c0 + 
                             p1.handle_right * c1 + 
                             p2.handle_left * c2 + 
                             p2.co * c3)
                        points_coords.append(mat @ co)
                
                if not spline.use_cyclic_u:
                    points_coords.append(mat @ spline.bezier_points[-1].co)
            else:
                # For POLY/NURBS splines
                for p in spline.points:
                    points_coords.append(mat @ Vector(p.co[:3]))
            
            if not points_coords: continue
            
            # Use the most robust way to add points to a stroke
            num_points = len(points_coords)
            if hasattr(stroke, "add_points"):
                stroke.add_points(num_points)
            elif hasattr(stroke.points, "add"):
                try:
                    stroke.points.add(count=num_points)
                except TypeError:
                    stroke.points.add(num_points)
            
            # Assign coordinates
            for j, co in enumerate(points_coords):
                if j < len(stroke.points):
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
