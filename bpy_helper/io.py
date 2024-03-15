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


# some helper functions
mat2list = lambda x: [[float(xxx) for xxx in xx] for xx in x]
array2list = lambda x: [float(xx) for xx in x]
