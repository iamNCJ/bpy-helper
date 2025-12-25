import bpy
from importlib.metadata import version

try:
    IS_BLENDER_4 = version('bpy').split('.')[0] == '4'
except:
    IS_BLENDER_4 = True  # assume bpy 4.0 if running inside Blender Extension


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


def create_white_diffuse_material(override_normal_map=False, normal_map_path=None, material_name="White_Diffuse_Material") -> bpy.types.Material:
    """
    Create white diffuse material

    :param override_normal_map: override normal map
    :param normal_map_path: normal map path
    :param material_name: material name, default is "White_Diffuse_Material"
    :return: white diffuse material
    """

    material = bpy.data.materials.new(name=material_name)
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


def create_white_emmissive_material(strength=100., override_normal_map=False, normal_map_path=None, material_name="White_Emissive_Material") -> bpy.types.Material:
    """
    Create white emissive material

    :param strength: emission strength
    :param override_normal_map: override normal map
    :param normal_map_path: normal map path
    :param material_name: material name, default is "White_Emissive_Material"
    :return: white emissive material
    """

    material = bpy.data.materials.new(name=material_name)
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


def create_emissive_material(strength=100., color=(1., 1., 1.), material_name="Emissive_Material") -> bpy.types.Material:
    """
    Create emissive material

    :param strength: emission strength
    :param color: emission color
    :param material_name: material name, default is "Emissive_Material"
    :return: emissive material
    """

    material = bpy.data.materials.new(name=material_name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]

    if IS_BLENDER_4:
        bsdf.inputs['Base Color'].default_value = (1., 1., 1., 1.)
        bsdf.inputs['Specular IOR Level'].default_value = 0
        bsdf.inputs['Roughness'].default_value = 1
        bsdf.inputs['Emission Color'].default_value = (color[0], color[1], color[2], 1.)
        bsdf.inputs['Emission Strength'].default_value = strength
    else:
        bsdf.inputs['Base Color'].default_value = (1., 1., 1., 1.)
        bsdf.inputs['Specular'].default_value = 0
        bsdf.inputs['Roughness'].default_value = 1
        bsdf.inputs['Emission'].default_value = (color[0], color[1], color[2], 1.)
        bsdf.inputs['Emission Strength'].default_value = strength

    return material


def create_specular_ggx_material(r=0.34, override_normal_map=False, normal_map_path=None, material_name="Specular_GGX_Material") -> bpy.types.Material:
    """
    Create specular GGX material

    :param r: roughness, default is 0.34
    :param override_normal_map: whether to override normal map, default is False
    :param normal_map_path: normal map path, if override_normal_map is True
    :param material_name: material name, default is "Specular_GGX_Material"
    :return: specular GGX material
    """

    material = bpy.data.materials.new(name=material_name)
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


def create_invisible_material(material_name="Invisible_Material") -> bpy.types.Material:
    """
    Create invisible material

    :param material_name: material name, default is "Invisible_Material"
    :return: invisible material
    """

    material = bpy.data.materials.new(name=material_name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]

    bsdf.inputs['Alpha'].default_value = 0.

    return material


def create_specular_roughness_bsdf():
    """
    Create specular-roughness workflow BSDF Node Group
    """

    if 'SpecularRoughnessBSDF' in bpy.data.node_groups:
        print('Already created specular roughness workflow BSDF')
        return

    # Create a new node group
    group = bpy.data.node_groups.new(type="ShaderNodeTree", name="SpecularRoughnessBSDF")
    
    # Create group inputs
    group_inputs = group.nodes.new('NodeGroupInput')
    group_inputs.location = (-600, -300)
    
    # Create group outputs
    group_outputs = group.nodes.new('NodeGroupOutput')
    group_outputs.location = (400, 0)
    
    # Create the group input sockets
    roughness_socket = group.interface.new_socket(
        name="Roughness",
        description="Roughness float value",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    )
    group.interface.items_tree["Roughness"].min_value = 0
    group.interface.items_tree["Roughness"].max_value = 1
    normal_socket = group.interface.new_socket(
        name="Normal",
        description="Normal vector",
        in_out='INPUT',
        socket_type='NodeSocketVector'
    )
    specular_socket = group.interface.new_socket(
        name="Specular",
        description="Specular vector",
        in_out='INPUT',
        socket_type='NodeSocketVector'
    )
    diffuse_socket = group.interface.new_socket(
        name="Diffuse",
        description="Diffuse vector",
        in_out='INPUT',
        socket_type='NodeSocketVector'
    )
    
    output_socket = group.interface.new_socket(
        name="Shader",
        description="Output shader",
        in_out='OUTPUT',
        socket_type='NodeSocketShader'
    )
    
    # Create nodes
    nodes = group.nodes
    links = group.links
    
    # Create Glossy BSDF node
    glossy = nodes.new('ShaderNodeBsdfGlossy')
    glossy.location = (-200, 0)
    glossy.distribution = 'MULTI_GGX'  # Set to Multiscatter GGX
    
    # Create Diffuse BSDF node
    diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.location = (-200, -200)
    
    # Create Add Shader node
    add_shader = nodes.new('ShaderNodeAddShader')
    add_shader.location = (200, 0)
    
    # Create links
    
    # Diffuse BSDF connections
    links.new(group_inputs.outputs['Diffuse'], diffuse.inputs['Color'])
    links.new(group_inputs.outputs['Normal'], diffuse.inputs['Normal'])
    diffuse.inputs['Roughness'].default_value = 0.0  # Disable Oren-Nayar BSDF
    
    # Glossy BSDF connections
    links.new(group_inputs.outputs['Specular'], glossy.inputs['Color'])
    links.new(group_inputs.outputs['Roughness'], glossy.inputs['Roughness'])
    links.new(group_inputs.outputs['Normal'], glossy.inputs['Normal'])
    
    # Add Shader connections
    links.new(glossy.outputs[0], add_shader.inputs[0])
    links.new(diffuse.outputs[0], add_shader.inputs[1])
    
    # Final output connection
    links.new(add_shader.outputs[0], group_outputs.inputs['Shader'])
    
    return group


def create_specular_roughness_material(diffuse_color=(1.0, 1.0, 1.0), specular_color=(0.0, 0.0, 0.0), roughness=1.0, material_name="Specular_Roughness_Material") -> bpy.types.Material:
    """
    Create specular-roughness material

    :param diffuse_color: diffuse color, default is (1.0, 1.0, 1.0)
    :param specular_color: specular color, default is (0.0, 0.0, 0.0)
    :param roughness: roughness, default is 1.0
    :param material_name: material name, default is "Specular_Roughness_Material"
    :return: specular-roughness material
    """

    assert IS_BLENDER_4, "This function is only tested in Blender 4.0"
    
    # Create new material
    material = bpy.data.materials.new(name=material_name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    specular_rough = nodes.new('ShaderNodeGroup')
    material_output = nodes.new('ShaderNodeOutputMaterial')
    
    # Set up Specular Roughness node
    if 'SpecularRoughnessBSDF' not in bpy.data.node_groups:
        create_specular_roughness_bsdf()
    specular_rough.node_tree = bpy.data.node_groups['SpecularRoughnessBSDF']
    
    # Set diffuse and specular colors
    specular_rough.inputs['Diffuse'].default_value = diffuse_color
    specular_rough.inputs['Specular'].default_value = specular_color
    specular_rough.inputs['Roughness'].default_value = roughness
    
    # Position nodes
    specular_rough.location = (0, 0)
    material_output.location = (300, 0)
    
    # Create links
    links.new(specular_rough.outputs['Shader'], material_output.inputs['Surface'])
    
    return material


def create_full_principled_bsdf_material(base_color=(0, 0, 0), metallic=0.0, roughness=1.0, transmission_weight=0.0, ior=1.5, material_name="Full_Principled_BSDF_Material") -> bpy.types.Material:
    """
    Create full principled BSDF material

    :param base_color: base color, default is (0, 0, 0)
    :param metallic: metallic, default is 0.0
    :param roughness: roughness, default is 1.0
    :param transmission_weight: transmission weight, default is 0.0
    :param ior: index of refraction, default is 1.5
    :param material_name: material name, default is "Full_Principled_BSDF_Material"
    :return: full principled BSDF material
    """

    material = bpy.data.materials.new(name=material_name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]

    if IS_BLENDER_4:
        # Keys have been remapped, ref: https://wiki.blender.org/wiki/Reference/Release_Notes/4.0/Python_API
        bsdf.inputs['Base Color'].default_value = (base_color[0], base_color[1], base_color[2], 1)
        bsdf.inputs['Subsurface Weight'].default_value = 0
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Specular IOR Level'].default_value = 1
        bsdf.inputs['Specular Tint'].default_value = (1, 1, 1, 1)
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Anisotropic'].default_value = 0
        bsdf.inputs['Anisotropic Rotation'].default_value = 0.5
        bsdf.inputs['Sheen Weight'].default_value = 0
        bsdf.inputs['Sheen Tint'].default_value = (0, 0, 0, 1)
        bsdf.inputs['Coat Weight'].default_value = 0
        bsdf.inputs['Coat Roughness'].default_value = 0
        bsdf.inputs['Transmission Weight'].default_value = transmission_weight
        bsdf.inputs['Emission Color'].default_value = (0, 0, 0, 1)
        bsdf.inputs['Alpha'].default_value = 1
        bsdf.inputs['IOR'].default_value = ior
    else:
        bsdf.inputs['Base Color'].default_value = (base_color[0], base_color[1], base_color[2], 1)
        bsdf.inputs['Subsurface'].default_value = 0
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Specular'].default_value = 1
        bsdf.inputs['Specular Tint'].default_value = 1
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Anisotropic'].default_value = 0
        bsdf.inputs['Anisotropic Rotation'].default_value = 0.5
        bsdf.inputs['Sheen'].default_value = 0
        bsdf.inputs['Sheen Tint'].default_value = 0
        bsdf.inputs['Clearcoat'].default_value = 0
        bsdf.inputs['Clearcoat Roughness'].default_value = 0
        bsdf.inputs['IOR'].default_value = ior
        bsdf.inputs['Transmission'].default_value = transmission_weight
        bsdf.inputs['Transmission Roughness'].default_value = 0
        bsdf.inputs['Emission'].default_value = (0, 0, 0, 1)
        bsdf.inputs['Alpha'].default_value = 1

    return material
