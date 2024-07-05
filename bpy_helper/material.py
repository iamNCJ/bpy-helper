import bpy
from importlib.metadata import version

IS_BLENDER_4 = version('bpy').split('.')[0] == '4'


def clear_emission_and_alpha_nodes() -> None:
    """
    Clear all emission and alpha nodes in the scene, including all objects' materials
    """

    # Loop through all materials in the scene
    for material in bpy.data.materials:
        # Check if the material has an emission shader
        if material.use_nodes:
            for node in material.node_tree.nodes:
                if 'Emission Strength' in node.inputs.keys():
                    while node.inputs['Emission Strength'].is_linked:
                        material.node_tree.links.remove(node.inputs['Emission Strength'].links[0])
                    node.inputs['Emission Strength'].default_value = 0.
                if 'Alpha' in node.inputs.keys():
                    while node.inputs['Alpha'].is_linked:
                        material.node_tree.links.remove(node.inputs['Alpha'].links[0])
                    node.inputs['Alpha'].default_value = 1.
                if node.type == 'EMISSION':
                    while node.inputs['Strength'].is_linked:
                        material.node_tree.links.remove(node.inputs['Strength'].links[0])
                    node.inputs['Strength'].default_value = 0.


def override_normal_map_op(material, normal_map_path) -> None:
    """
    Override normal map for the material (to attach a precomputed world-space normal map)
    """

    # Create texture coordinate node
    tex_coord = material.node_tree.nodes.new('ShaderNodeTexCoord')

    # Load normal exr
    normal_map = material.node_tree.nodes.new('ShaderNodeTexImage')
    normal_map.image = bpy.data.images.load(normal_map_path)
    material.node_tree.links.new(tex_coord.outputs['Window'], normal_map.inputs['Vector'])

    # Vector multiply by 2
    vector_math = material.node_tree.nodes.new('ShaderNodeVectorMath')
    vector_math.operation = 'MULTIPLY'
    vector_math.inputs[1].default_value = (2., 2., 2.)
    material.node_tree.links.new(normal_map.outputs['Color'], vector_math.inputs[0])

    # Vector subtract by 1
    vector_math_2 = material.node_tree.nodes.new('ShaderNodeVectorMath')
    vector_math_2.operation = 'SUBTRACT'
    vector_math_2.inputs[1].default_value = (1., 1., 1.)
    material.node_tree.links.new(vector_math.outputs['Vector'], vector_math_2.inputs[0])

    bsdf = material.node_tree.nodes["Principled BSDF"]
    material.node_tree.links.new(vector_math_2.outputs['Vector'], bsdf.inputs['Normal'])


def create_white_diffuse_material(override_normal_map=False, normal_map_path=None) -> bpy.types.Material:
    """
    Create white diffuse material

    :param override_normal_map: override normal map
    :param normal_map_path: normal map path
    :return: white diffuse material
    """

    material = bpy.data.materials.new(name="White_Diffuse_Material")
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]

    if IS_BLENDER_4:
        bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)
        bsdf.inputs['Specular IOR Level'].default_value = 0
        bsdf.inputs['Roughness'].default_value = 1
    else:
        bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)
        bsdf.inputs['Specular'].default_value = 0
        bsdf.inputs['Roughness'].default_value = 1

    if override_normal_map:
        override_normal_map_op(material, normal_map_path)

    return material


def create_white_emmissive_material(strength=100., override_normal_map=False, normal_map_path=None) -> bpy.types.Material:
    """
    Create white emissive material

    :param override_normal_map: override normal map
    :param normal_map_path: normal map path
    :return: white emissive material
    """

    material = bpy.data.materials.new(name="White_Emissive_Material")
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]

    if IS_BLENDER_4:
        bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)
        bsdf.inputs['Specular IOR Level'].default_value = 0
        bsdf.inputs['Roughness'].default_value = 1
        bsdf.inputs['Emission Color'].default_value = (1, 1, 1, 1)
        bsdf.inputs['Emission Strength'].default_value = strength
    else:
        bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)
        bsdf.inputs['Specular'].default_value = 0
        bsdf.inputs['Roughness'].default_value = 1
        bsdf.inputs['Emission'].default_value = (1, 1, 1, 1)
        bsdf.inputs['Emission Strength'].default_value = strength

    if override_normal_map:
        override_normal_map_op(material, normal_map_path)

    return material


def create_specular_ggx_material(r=0.34, override_normal_map=False, normal_map_path=None) -> bpy.types.Material:
    """
    Create specular GGX material

    :param r: roughness, default is 0.34
    :param override_normal_map: whether to override normal map, default is False
    :param normal_map_path: normal map path, if override_normal_map is True
    :return: specular GGX material
    """

    material = bpy.data.materials.new(name="Specular_GGX_Material")
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]

    if IS_BLENDER_4:
        # Keys have been remapped, ref: https://wiki.blender.org/wiki/Reference/Release_Notes/4.0/Python_API
        bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
        bsdf.inputs['Subsurface Weight'].default_value = 0
        bsdf.inputs['Metallic'].default_value = 0
        bsdf.inputs['Specular IOR Level'].default_value = 1
        bsdf.inputs['Specular Tint'].default_value = (1, 1, 1, 1)
        bsdf.inputs['Roughness'].default_value = r
        bsdf.inputs['Anisotropic'].default_value = 0
        bsdf.inputs['Anisotropic Rotation'].default_value = 0.5
        bsdf.inputs['Sheen Weight'].default_value = 0
        bsdf.inputs['Sheen Tint'].default_value = (0, 0, 0, 1)
        bsdf.inputs['Coat Weight'].default_value = 0
        bsdf.inputs['Coat Roughness'].default_value = 0
        bsdf.inputs['Transmission Weight'].default_value = 0
        bsdf.inputs['Emission Color'].default_value = (0, 0, 0, 1)
        bsdf.inputs['Alpha'].default_value = 1
    else:
        bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
        bsdf.inputs['Subsurface'].default_value = 0
        bsdf.inputs['Metallic'].default_value = 0
        bsdf.inputs['Specular'].default_value = 1
        bsdf.inputs['Specular Tint'].default_value = 1
        bsdf.inputs['Roughness'].default_value = r
        bsdf.inputs['Anisotropic'].default_value = 0
        bsdf.inputs['Anisotropic Rotation'].default_value = 0.5
        bsdf.inputs['Sheen'].default_value = 0
        bsdf.inputs['Sheen Tint'].default_value = 0
        bsdf.inputs['Clearcoat'].default_value = 0
        bsdf.inputs['Clearcoat Roughness'].default_value = 0
        bsdf.inputs['Transmission'].default_value = 0
        bsdf.inputs['Transmission Roughness'].default_value = 0
        bsdf.inputs['Emission'].default_value = (0, 0, 0, 1)
        bsdf.inputs['Alpha'].default_value = 1

    if override_normal_map:
        override_normal_map_op(material, normal_map_path)

    return material
