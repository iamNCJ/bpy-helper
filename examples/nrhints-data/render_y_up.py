import json
import math
import os

import bpy
from tqdm import tqdm

from bpy_helper.camera import look_at_to_c2w, create_camera
from bpy_helper.geometry import set_smooth_shading
from bpy_helper.light import create_point_light
from bpy_helper.random import gen_random_pts_around_origin
from bpy_helper.scene import import_3d_model
from bpy_helper.utils import stdout_redirected


def render_blender_scene_random_pl(
        blend_path, out_path,
        w, h,
        N_train, N_val, N_test,
        fov_in_degree, zn, zf,
        view_dist_range, view_theta_range,
        pl_dist_range, pl_theta_range,
        pl_energy,
        seed_view=0, seed_pl=1,
        N_samples=128,
        rescale_scene=1.0,
        fix_light=False,
        hard_shadow=False,
        use_hdr=False):
    import_3d_model(blend_path)

    # Always assume the scene named as 'Scene'
    bpy.context.window.scene = bpy.data.scenes['Scene']
    os.makedirs(out_path, exist_ok=True)

    # Force smooth shading
    set_smooth_shading()

    # Set film
    if use_hdr:
        bpy.context.scene.render.image_settings.file_format = 'OPEN_EXR'
    else:
        bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.resolution_x = w
    bpy.context.scene.render.resolution_y = h
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = N_samples

    # do rendering
    eyes = gen_random_pts_around_origin(seed_view, N_train + N_val + N_test, view_dist_range[0], view_dist_range[1],
                                        view_theta_range[0], view_theta_range[1], z_up=False)
    pls = gen_random_pts_around_origin(seed_pl, N_train + N_val + N_test, pl_dist_range[0], pl_dist_range[1],
                                       pl_theta_range[0], pl_theta_range[1], z_up=False)

    js = [dict(), dict(), dict()]
    datasets = ['train', 'val', 'test']
    Ns = [N_train, N_val, N_test]
    offset = 0
    for d in range(len(datasets)):
        js[d]['camera_angle_x'] = fov_in_degree * math.pi / 180.0
        js[d]['camera_far'] = zf * rescale_scene
        js[d]['camera_near'] = zn * rescale_scene
        js[d]['frames'] = list()

        for i in tqdm(range(Ns[d])):
            # camera 
            m = look_at_to_c2w(eyes[i + offset], (0, 0, 0), (0, 1, 0))
            cam = create_camera(m, fov_in_degree)
            bpy.context.scene.camera = cam

            if not fix_light:
                pl = create_point_light(pls[i + offset], power=pl_energy, hard_shadow=hard_shadow)

            # render
            if use_hdr:
                bpy.context.scene.render.filepath = os.path.join(out_path, datasets[d], f'r_{i}.exr')
            else:
                bpy.context.scene.render.filepath = os.path.join(out_path, datasets[d], f'r_{i}.png')
            with stdout_redirected():
                bpy.ops.render.render(animation=False, write_still=True)

            # write json
            frame = dict()
            if use_hdr:
                frame['file_ext'] = '.exr'
            else:
                frame['file_ext'] = '.png'
            frame['file_path'] = f'./{datasets[d]}/r_{i}'
            if not fix_light:
                energy = pl_energy * (rescale_scene * rescale_scene)
                frame['pl_intensity'] = [energy, energy, energy]
                pl_pos = pls[i + offset]
                frame['pl_pos'] = [pl_pos[0] * rescale_scene, pl_pos[1] * rescale_scene, pl_pos[2] * rescale_scene]
            else:
                frame['pl_intensity'] = [0.0, 0.0, 0.0]
                pl_pos = pls[i + offset]
                frame['pl_pos'] = [0.0, 0.0, 0.0]
            frame['transform_matrix'] = [
                [m[0][0], m[0][1], m[0][2], m[0][3] * rescale_scene],
                [m[1][0], m[1][1], m[1][2], m[1][3] * rescale_scene],
                [m[2][0], m[2][1], m[2][2], m[2][3] * rescale_scene],
                [m[3][0], m[3][1], m[3][2], m[3][3]]]
            js[d]['frames'].append(frame)

        out_file = open(os.path.join(out_path, f"transforms_{datasets[d]}.json"), "w")
        json.dump(js[d], out_file, indent=4)
        offset += Ns[d]


if __name__ == '__main__':
    material_names = [r'Metal_Aniso', r'Metal']
    for m in material_names:
        render_blender_scene_random_pl(
            f'./Cup_Plane_{m}_4Lights.blend',
            f'./Cup_Plane_{m}_PL_500',
            512, 512, 500, 100, 100,
            30.0, 2.0, 7.0,
            (4.0, 5.0), (10.0, 90.0),
            (4.0, 5.0), (0.0, 60.0),
            pl_energy=5000,
            seed_view=0, seed_pl=1,
            N_samples=256,  # 256
            rescale_scene=1.0,
            fix_light=False, hard_shadow=True)

    material_names = [r'SSS']
    for m in material_names:
        render_blender_scene_random_pl(
            f'./Cup_Plane_{m}_4Lights.blend',
            f'./Cup_Plane_{m}_PL_500',
            512, 512, 500, 100, 100,
            30.0, 2.0, 7.0,
            (4.0, 5.0), (10.0, 90.0),
            (4.0, 5.0), (0.0, 60.0),
            pl_energy=5000,
            seed_view=0, seed_pl=1,
            N_samples=1024,  # 256
            rescale_scene=1.0,
            fix_light=False, hard_shadow=True)

    render_blender_scene_random_pl(
        f'./Basket_4Lights.blend',
        f'./Basket_PL_500',
        512, 512, 500, 100, 100,
        30.0, 2.0, 7.0,
        (4.0, 5.0), (10.0, 90.0),
        (4.0, 5.0), (0.0, 60.0),
        pl_energy=2000,
        seed_view=0, seed_pl=1,
        N_samples=256,
        rescale_scene=1.0,
        fix_light=False,
        hard_shadow=True)

    render_blender_scene_random_pl(
        r'./FurBall_Plane_5AreaLights.blend',
        r'./FurBall_Plane_PL_500',
        512, 512, 500, 100, 100,
        30.0, 20.0, 50.0,
        (30.0, 35.0), (10.0, 90.0),
        (30.0, 35.0), (0.0, 60.0),
        pl_energy=100000,
        seed_view=0, seed_pl=1,
        N_samples=1024,
        rescale_scene=0.15,
        fix_light=False)
