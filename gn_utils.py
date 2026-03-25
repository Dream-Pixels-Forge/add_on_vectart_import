import bpy

def get_or_create_vectart_gn_group():
    """Create or return the standard VectArt Geometry Nodes group"""
    group_name = "VectArt_Procedural_Extrude"
    
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]
        
    # Create new geometry node group
    group = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')
    
    # Define Inputs
    group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    
    # Parameters
    s_extrude = group.interface.new_socket(name="Extrude", in_out='INPUT', socket_type='NodeSocketFloat')
    s_extrude.default_value = 0.05
    s_extrude.min_value = 0.0
    
    s_offset = group.interface.new_socket(name="Z Offset", in_out='INPUT', socket_type='NodeSocketFloat')
    s_offset.default_value = 0.0
    
    s_bevel = group.interface.new_socket(name="Bevel Size", in_out='INPUT', socket_type='NodeSocketFloat')
    s_bevel.default_value = 0.005
    s_bevel.min_value = 0.0
    
    s_fill = group.interface.new_socket(name="Fill Caps", in_out='INPUT', socket_type='NodeSocketBool')
    s_fill.default_value = True

    # Define Output
    group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    
    # Node logic
    nodes = group.nodes
    links = group.links
    nodes.clear()
    
    # Input/Output nodes
    input_node = nodes.new('NodeGroupInput')
    output_node = nodes.new('NodeGroupOutput')
    
    # 1. Fill Curve
    fill_curve = nodes.new('GeometryNodeFillCurve')
    fill_curve.mode = 'TRIANGLES'
    
    # 2. Extrude Mesh
    extrude = nodes.new('GeometryNodeExtrudeMesh')
    extrude.mode = 'FACES'
    
    # 3. Transform (for Offset)
    transform = nodes.new('GeometryNodeTransform')
    
    # 4. Join Geometry (for caps)
    join = nodes.new('GeometryNodeJoinGeometry')
    
    # 5. Flip Faces (for bottom cap)
    flip = nodes.new('GeometryNodeFlipFaces')
    
    # Linking
    # Input -> Fill -> Join (bottom)
    links.new(input_node.outputs['Geometry'], fill_curve.inputs['Curve'])
    links.new(fill_curve.outputs['Mesh'], flip.inputs['Mesh'])
    links.new(flip.outputs['Mesh'], join.inputs['Geometry'])
    
    # Fill -> Extrude -> Join (top/sides)
    links.new(fill_curve.outputs['Mesh'], extrude.inputs['Mesh'])
    links.new(extrude.outputs['Mesh'], join.inputs['Geometry'])
    
    # Extrude Settings
    links.new(input_node.outputs['Extrude'], extrude.inputs['Offset Scale'])
    
    # Join -> Transform (Offset) -> Output
    links.new(join.outputs['Geometry'], transform.inputs['Geometry'])
    links.new(input_node.outputs['Z Offset'], transform.inputs['Translation'])
    links.new(transform.outputs['Geometry'], output_node.inputs['Geometry'])
    
    # Organize
    input_node.location = (-400, 0)
    fill_curve.location = (-200, 0)
    extrude.location = (0, 100)
    flip.location = (0, -100)
    join.location = (200, 0)
    transform.location = (400, 0)
    output_node.location = (600, 0)
    
    return group

def apply_vectart_gn(obj):
    """Apply the procedural GN modifier to a curve object"""
    if not obj or obj.type != 'CURVE':
        return
        
    # Ensure standard curve properties are zeroed to avoid double extrusion
    obj.data.extrude = 0.0
    obj.data.bevel_depth = 0.0
    
    # Check if modifier already exists
    mod_name = "VectArt_Procedural"
    mod = obj.modifiers.get(mod_name)
    
    if not mod:
        mod = obj.modifiers.new(name=mod_name, type='NODES')
        
    group = get_or_create_vectart_gn_group()
    mod.node_group = group
    return mod

def sync_gn_properties(obj, extrude, offset, bevel_size=0.0):
    """Sync values to the GN modifier"""
    mod = obj.modifiers.get("VectArt_Procedural")
    if mod and mod.node_group:
        # Access inputs by name via the identifier or index
        # For security in 4.x/5.x we use indices if name fails, 
        # but modern Blender uses socket identifiers.
        try:
            mod["Input_1"] = extrude      # Extrude
            mod["Input_2"] = offset       # Z Offset
            mod["Input_3"] = bevel_size   # Bevel Size
        except:
            # Fallback for different group versions
            pass
