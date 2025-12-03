from typing import List, Optional

import bpy


def save_blend_file(filepath) -> None:
    """
    Save the current blend file

    :param filepath: file path to save
    """

    bpy.ops.wm.save_as_mainfile(filepath=filepath)


# adapted from BlenderProc
def get_nodes_created_in_func(nodes: List[bpy.types.Node], created_in_func: str) -> List[bpy.types.Node]:
    """
    Returns all nodes which are created in the given function

    :param nodes: list of nodes of the current material
    :param created_in_func: return all nodes created in the given function
    :return: The list of nodes with the given type.
    """

    return [node for node in nodes if "created_in_func" in node and node["created_in_func"] == created_in_func]


def get_nodes_with_type(nodes: List[bpy.types.Node], node_type: str,
                        created_in_func: Optional[str] = None) -> List[bpy.types.Node]:
    """
    Returns all nodes which are of the given node_type

    :param nodes: list of nodes of the current material
    :param node_type: node types
    :param created_in_func: Only return nodes created by the specified function
    :return: list of nodes, which belong to the type
    """

    nodes_with_type = [node for node in nodes if node_type in node.bl_idname]
    if created_in_func:
        nodes_with_type = get_nodes_created_in_func(nodes_with_type, created_in_func)
    return nodes_with_type


def get_the_one_node_with_type(nodes: List[bpy.types.Node], node_type: str,
                               created_in_func: str = "") -> bpy.types.Node:
    """
    Returns the one node which is of the given node_type

    This function will only work if there is only one of the nodes of this type.

    :param nodes: list of nodes of the current material
    :param node_type: node types
    :param created_in_func: only return node created by the specified function
    :return: node of the node type
    """

    node = get_nodes_with_type(nodes, node_type, created_in_func)
    if node and len(node) == 1:
        return node[0]
    raise RuntimeError(f"There is not only one node of this type: {node_type}, there are: {len(node)}")


def render_depth_map(output_dir, file_prefix='depth') -> None:
    """
    Render depth map

    :param output_dir: output directory
    :param file_prefix: file prefix, default is 'depth'
    """

    # disable material override
    bpy.context.scene.view_layers["ViewLayer"].material_override = None

    bpy.context.scene.render.use_compositing = True
    bpy.context.scene.use_nodes = True

    tree = bpy.context.scene.node_tree
    links = tree.links
    # Use existing render layer
    render_layer_node = get_the_one_node_with_type(tree.nodes, 'CompositorNodeRLayers')

    # Enable z-buffer pass
    bpy.context.view_layer.use_pass_z = True

    # Build output node
    output_file = tree.nodes.new("CompositorNodeOutputFile")
    output_file.base_path = output_dir
    output_file.format.file_format = "OPEN_EXR"
    # set a different path (in case overwrite last file)
    bpy.context.scene.render.filepath = f'{output_dir}/rgb_for_{file_prefix}.png'
    output_file.file_slots.values()[0].path = file_prefix

    # Feed the Z-Buffer output of the render layer to the input of the file IO layer
    links.new(render_layer_node.outputs["Depth"], output_file.inputs['Image'])
    bpy.ops.render.render(animation=False, write_still=True)

    # Clean up
    for link in output_file.inputs[0].links:
        links.remove(link)
    tree.nodes.remove(output_file)
    bpy.context.scene.render.use_compositing = False
    bpy.context.scene.use_nodes = False
    bpy.context.view_layer.use_pass_z = False


def render_normal_map(output_dir, file_prefix="normal") -> None:
    """
    Render normal map

    :param output_dir: output directory
    :param file_prefix: file prefix, default is 'normal'
    """

    # disable material override
    bpy.context.scene.view_layers["ViewLayer"].material_override = None

    bpy.context.scene.render.use_compositing = True
    bpy.context.scene.use_nodes = True

    tree = bpy.context.scene.node_tree
    links = tree.links
    # Use existing render layer
    render_layer_node = get_the_one_node_with_type(tree.nodes, 'CompositorNodeRLayers')

    # Enable normal pass
    bpy.context.view_layer.use_pass_normal = True

    # Separate into RGB
    separate_rgba = tree.nodes.new("CompositorNodeSepRGBA")
    links.new(render_layer_node.outputs["Normal"], separate_rgba.inputs["Image"])

    combine_rgba = tree.nodes.new("CompositorNodeCombRGBA")
    for row_index in range(3):
        map_range = tree.nodes.new("CompositorNodeMapRange")
        map_range.inputs["From Min"].default_value = -1.0
        map_range.inputs["From Max"].default_value = 1.0
        map_range.inputs["To Min"].default_value = 0.0
        map_range.inputs["To Max"].default_value = 1.0
        links.new(separate_rgba.outputs[row_index], map_range.inputs["Value"])
        links.new(map_range.outputs["Value"], combine_rgba.inputs[row_index])

    # Build output node
    output_file = tree.nodes.new("CompositorNodeOutputFile")
    output_file.base_path = output_dir
    output_file.format.file_format = "OPEN_EXR"
    # set a different path (in case overwrite last file)
    bpy.context.scene.render.filepath = f'{output_dir}/rgb_for_{file_prefix}.png'
    output_file.file_slots.values()[0].path = file_prefix

    # Feed the combined rgb output to the input of the file IO layer
    links.new(combine_rgba.outputs["Image"], output_file.inputs['Image'])
    bpy.ops.render.render(animation=False, write_still=True)

    # Clean up
    for link in output_file.inputs[0].links:
        links.remove(link)
    tree.nodes.remove(output_file)
    bpy.context.scene.render.use_compositing = False
    bpy.context.scene.use_nodes = False
    bpy.context.view_layer.use_pass_normal = False


# Constants for compositing node names
RGB_OUTPUT_NODE_NAME = "BPYHelperRGBOutput"
DEPTH_OUTPUT_NODE_NAME = "BPYHelperDepthOutput"
NORMAL_OUTPUT_NODE_NAME = "BPYHelperNormalOutput"
DIFFUSE_OUTPUT_NODE_NAME = "BPYHelperDiffuseOutput"
GLOSSY_OUTPUT_NODE_NAME = "BPYHelperGlossyOutput"
ALBEDO_OUTPUT_NODE_NAME = "BPYHelperAlbedoOutput"


def create_compositing_nodes(
    enable_depth=False,
    enable_normal=False,
    enable_diffuse=False,
    enable_glossy=False,
    enable_albedo=False,
    use_denoising=True,
):
    """
    Create compositing nodes

    :param enable_depth: enable depth pass
    :param enable_normal: enable normal pass
    :param enable_diffuse: enable diffuse-only pass (view-independent effects)
    :param enable_glossy: enable glossy-only pass (view-dependent effects)
    :param enable_albedo: enable albedo pass
    :param use_denoising: use denoising
    """
    
    bpy.context.scene.render.use_compositing = True
    bpy.context.scene.use_nodes = True
    
    tree = bpy.context.scene.node_tree
    links = tree.links
    
    # Clear existing nodes to avoid conflicts
    for node in tree.nodes:
        tree.nodes.remove(node)
    
    # Create render layer node
    render_layer_node = tree.nodes.new("CompositorNodeRLayers")
    
    # Create composite output node
    composite_output = tree.nodes.new("CompositorNodeComposite")
    composite_output.location = (400, 0)
    
    # Create RGB file output node
    rgb_output = tree.nodes.new("CompositorNodeOutputFile")
    rgb_output.name = RGB_OUTPUT_NODE_NAME
    rgb_output.base_path = "/tmp"  # placeholder path
    rgb_output.format.file_format = "OPEN_EXR"
    rgb_output.file_slots.values()[0].path = "rgb"
    rgb_output.location = (400, -100)
    
    # Connect render layer to both composite and file output for RGB
    links.new(render_layer_node.outputs["Image"], composite_output.inputs["Image"])
    links.new(render_layer_node.outputs["Image"], rgb_output.inputs["Image"])
    
    if enable_depth:
        # Enable z-buffer pass
        bpy.context.view_layer.use_pass_z = True
        
        # Create file output node for depth
        depth_output = tree.nodes.new("CompositorNodeOutputFile")
        depth_output.name = DEPTH_OUTPUT_NODE_NAME
        depth_output.base_path = "/tmp"  # placeholder path
        depth_output.format.file_format = "OPEN_EXR"
        depth_output.file_slots.values()[0].path = "depth"
        depth_output.location = (400, -250)
        
        # Connect depth output
        links.new(render_layer_node.outputs["Depth"], depth_output.inputs['Image'])
    
    if enable_normal:
        # Enable normal pass
        bpy.context.view_layer.use_pass_normal = True
        
        # Separate into RGB
        separate_rgba = tree.nodes.new("CompositorNodeSepRGBA")
        separate_rgba.location = (200, -400)
        links.new(render_layer_node.outputs["Normal"], separate_rgba.inputs["Image"])
        
        # Create map range nodes for each channel
        map_range_nodes = []
        for i in range(3):
            map_range = tree.nodes.new("CompositorNodeMapRange")
            map_range.inputs["From Min"].default_value = -1.0
            map_range.inputs["From Max"].default_value = 1.0
            map_range.inputs["To Min"].default_value = 0.0
            map_range.inputs["To Max"].default_value = 1.0
            map_range.location = (400, -400 - i * 200)
            map_range_nodes.append(map_range)
            links.new(separate_rgba.outputs[i], map_range.inputs["Value"])
        
        # Combine back to RGBA
        combine_rgba = tree.nodes.new("CompositorNodeCombRGBA")
        combine_rgba.location = (600, -400)
        for i, map_range in enumerate(map_range_nodes):
            links.new(map_range.outputs["Value"], combine_rgba.inputs[i])
        
        # Create file output node for normal
        normal_output = tree.nodes.new("CompositorNodeOutputFile")
        normal_output.name = NORMAL_OUTPUT_NODE_NAME
        normal_output.base_path = "/tmp"  # placeholder path
        normal_output.format.file_format = "OPEN_EXR"
        normal_output.file_slots.values()[0].path = "normal"
        normal_output.location = (800, -400)
        
        # Connect normal output
        links.new(combine_rgba.outputs["Image"], normal_output.inputs['Image'])

    if enable_diffuse:
        # Enable diffuse pass
        bpy.context.view_layer.use_pass_diffuse_direct = True
        bpy.context.view_layer.use_pass_diffuse_indirect = True
        bpy.context.view_layer.use_pass_diffuse_color = True
        
        # Create file output node for diffuse
        diffuse_output = tree.nodes.new("CompositorNodeOutputFile")
        diffuse_output.name = DIFFUSE_OUTPUT_NODE_NAME
        diffuse_output.base_path = "/tmp"  # placeholder path
        diffuse_output.format.file_format = "OPEN_EXR"
        diffuse_output.file_slots.values()[0].path = "diffuse"
        diffuse_output.location = (1000, 0)

        # Compose diffuse output
        vecter_add = tree.nodes.new("ShaderNodeVectorMath")
        vecter_add.operation = "ADD"
        vecter_add.location = (600, 0)
        links.new(render_layer_node.outputs["DiffDir"], vecter_add.inputs[0])
        links.new(render_layer_node.outputs["DiffInd"], vecter_add.inputs[1])

        vector_multiply = tree.nodes.new("ShaderNodeVectorMath")
        vector_multiply.operation = "MULTIPLY"
        vector_multiply.location = (800, 0)
        links.new(vecter_add.outputs[0], vector_multiply.inputs[0])
        links.new(render_layer_node.outputs["DiffCol"], vector_multiply.inputs[1])

        if use_denoising:
            # enable denoising data
            bpy.context.view_layer.cycles.denoising_store_passes = True

            # create denoising node
            denoising = tree.nodes.new("CompositorNodeDenoise")
            denoising.location = (1000, 0)
            diffuse_output.location = (1200, 0)

            # connect diffuse output and albedo/normal for denoising
            links.new(vector_multiply.outputs[0], denoising.inputs['Image'])
            links.new(render_layer_node.outputs["Denoising Albedo"], denoising.inputs['Albedo'])
            links.new(render_layer_node.outputs["Denoising Normal"], denoising.inputs['Normal'])

            # output denoising image
            links.new(denoising.outputs['Image'], diffuse_output.inputs['Image'])
        else:
            links.new(vector_multiply.outputs[0], diffuse_output.inputs['Image'])

    if enable_glossy:
        # Enable glossy pass
        bpy.context.view_layer.use_pass_glossy_direct = True
        bpy.context.view_layer.use_pass_glossy_indirect = True
        bpy.context.view_layer.use_pass_glossy_color = True
        
        # Create file output node for glossy
        glossy_output = tree.nodes.new("CompositorNodeOutputFile")
        glossy_output.name = GLOSSY_OUTPUT_NODE_NAME
        glossy_output.base_path = "/tmp"  # placeholder path
        glossy_output.format.file_format = "OPEN_EXR"
        glossy_output.file_slots.values()[0].path = "glossy"
        glossy_output.location = (1000, -200)
        
        # Compose glossy output
        vecter_add = tree.nodes.new("ShaderNodeVectorMath")
        vecter_add.operation = "ADD"
        vecter_add.location = (600, -200)
        links.new(render_layer_node.outputs["GlossDir"], vecter_add.inputs[0])
        links.new(render_layer_node.outputs["GlossInd"], vecter_add.inputs[1])
        
        vector_multiply = tree.nodes.new("ShaderNodeVectorMath")
        vector_multiply.operation = "MULTIPLY"
        vector_multiply.location = (800, -200)
        links.new(vecter_add.outputs[0], vector_multiply.inputs[0])
        links.new(render_layer_node.outputs["GlossCol"], vector_multiply.inputs[1])
        
        if use_denoising:
            # enable denoising data
            bpy.context.view_layer.cycles.denoising_store_passes = True
            
            # create denoising node
            denoising = tree.nodes.new("CompositorNodeDenoise")
            denoising.location = (1000, -250)
            glossy_output.location = (1200, -250)
            
            # connect glossy output and albedo/normal for denoising
            links.new(vector_multiply.outputs[0], denoising.inputs['Image'])
            links.new(render_layer_node.outputs["Denoising Albedo"], denoising.inputs['Albedo'])
            links.new(render_layer_node.outputs["Denoising Normal"], denoising.inputs['Normal'])
            
            # output denoising image
            links.new(denoising.outputs['Image'], glossy_output.inputs['Image'])
        else:
            links.new(vector_multiply.outputs[0], glossy_output.inputs['Image'])

    if enable_albedo:
        # Enable albedo pass
        bpy.context.view_layer.use_pass_diffuse_color = True
        
        # Create file output node for albedo
        albedo_output = tree.nodes.new("CompositorNodeOutputFile")
        albedo_output.name = ALBEDO_OUTPUT_NODE_NAME
        albedo_output.base_path = "/tmp"  # placeholder path
        albedo_output.format.file_format = "OPEN_EXR"
        albedo_output.file_slots.values()[0].path = "albedo"
        albedo_output.location = (1000, -400)

        # Connect albedo output
        links.new(render_layer_node.outputs["DiffCol"], albedo_output.inputs['Image'])

def render_with_compositing_nodes(output_folder_path, verbose=False):
    output_nodes = get_nodes_with_type(bpy.context.scene.node_tree.nodes, "CompositorNodeOutputFile")
    for node in output_nodes:
        node.base_path = output_folder_path
        if verbose:
            print(f"Setting {node.name} output path to {node.base_path}")
    bpy.ops.render.render(animation=False, write_still=True)

# some helper functions
mat2list = lambda x: [[float(xxx) for xxx in xx] for xx in x]
array2list = lambda x: [float(xx) for xx in x]
