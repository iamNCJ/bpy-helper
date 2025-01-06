from typing import Literal
import bpy
from bpy_helper.scene import reset_scene, import_3d_model, normalize_scene, scene_meshes


def uv_unwarp(
    input_mesh_file: str,
    output_mesh_file: str,
    method: Literal['unwarp', 'smart_project', 'cube_project', 'cylinder_project', 'sphere_project'] = 'unwarp',
    **kwargs
) -> bool:
    """
    Unwarps the UVs of the given mesh file.

    Args:
        input_mesh_file (str): The path to the input mesh file.
        output_mesh_file (str): The path to the output mesh file.
        method (Literal['unwarp', 'smart_project', 'cube_project', 'cylinder_project', 'sphere_project'], optional): The method to use for unwrapping. Defaults to 'unwarp'.
        kwargs: Additional keyword arguments.

    Returns:
        bool: True if the unwrapping was successful, False otherwise.
    """

    # clean the scene
    reset_scene()

    import_3d_model(input_mesh_file)
    # turn to Z-up Y-forward
    for obj in scene_meshes():
        obj.rotation_mode = 'XYZ'
        obj.rotation_euler = (0.0, 0.0, 0.0)

    # normalize the scene
    scale, offset = normalize_scene(use_bounding_sphere=True)
    print(f"scale: {scale}, offset: {offset}")

    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    if method == 'unwarp':
        _kwargs = {
            'method': 'ANGLE_BASED',
            'margin': 0.001
        }
        _kwargs.update(kwargs)
        bpy.ops.uv.unwrap(**_kwargs)
    elif method == 'smart_project':
        _kwargs = {
        }
        _kwargs.update(kwargs)
        bpy.ops.uv.smart_project(**_kwargs)
    elif method == 'cube_project':
        _kwargs = {
        }
        _kwargs.update(kwargs)
        bpy.ops.uv.cube_project(**_kwargs)
    elif method == 'cylinder_project':
        _kwargs = {
        }
        _kwargs.update(kwargs)
        bpy.ops.uv.cylinder_project(**_kwargs)
    elif method == 'sphere_project':
        _kwargs = {
        }
        _kwargs.update(kwargs)
        bpy.ops.uv.sphere_project(**_kwargs)
    else:
        raise ValueError(f"Unsupported method: {method}")

    bpy.ops.object.mode_set(mode='OBJECT')

    # export to same coordinates
    bpy.ops.wm.obj_export(
        filepath=output_mesh_file,
        export_uv=True,
        export_normals=False,
        export_colors=False,
        export_materials=False,
        export_triangulated_mesh=True,
        up_axis='Z',
        forward_axis='Y'
    )

    return True
