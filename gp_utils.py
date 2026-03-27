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
        frame = gp_layer.frames.new(1)
        
        # In 5.1, drawings are managed via the Drawings collection
        drawing = gp_data.drawings.new("Drawing")
        frame.drawing = drawing

        # Convert curve splines to GP strokes
        mat = curve_obj.matrix_world
        for spline in curve_obj.data.splines:
            stroke = drawing.strokes.new()
            
            # Transfer points with sampling for Bezier for better visual results
            points_coords = []
            if spline.type == 'BEZIER':
                # Higher resolution for bezier sampling
                resolution = spline.resolution_u
                for i in range(len(spline.bezier_points) - (0 if spline.use_cyclic_u else 1)):
                    p1 = spline.bezier_points[i]
                    p2 = spline.bezier_points[(i + 1) % len(spline.bezier_points)]
                    
                    for step in range(resolution):
                        t = step / resolution
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
                for p in spline.points:
                    points_coords.append(mat @ Vector(p.co[:3]))
            
            if not points_coords: continue
            
            # Use 5.1 point addition API
            stroke.points.add(len(points_coords))
            
            # Assign coordinates
            for j, co in enumerate(points_coords):
                stroke.points[j].co = co
                
            stroke.use_cyclic = spline.use_cyclic_u
            
    # Apply global settings from properties
    props = bpy.context.scene.vectart_props
    
    # In 5.1, use GREASE_PENCIL_THICKNESS
    mod = gp_obj.modifiers.new(name="Thickness", type='GREASE_PENCIL_THICKNESS')
    mod.thickness = props.gp_thickness
            
    return gp_obj

def apply_gpv3_modifiers(gp_obj):
    """Add standard GPv3 modifiers for SVG-like rendering"""
    if not gp_obj:
        return
        
    # 1. Fill modifier (if needed)
    # 2. Thickness modifier
    # 3. Build modifier for animation
    pass
