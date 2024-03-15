import math

import bpy
import mathutils
import numpy as np


def create_camera_look_at_object(location, target_object, fov=30):
    # remove other cameras
    bpy.ops.object.select_all(action='DESELECT')
    obj = bpy.data.objects.get("Camera")
    if obj is not None:
        obj.select_set(True)
        bpy.ops.object.delete()

    camera_data = bpy.data.cameras.new("Camera")
    camera_data.angle = fov * (math.pi / 180)  # Convert degrees to radians
    camera_obj = bpy.data.objects.new("Camera", camera_data)
    bpy.context.collection.objects.link(camera_obj)
    camera_obj.location = location

    # Make the camera look at the target object
    direction = target_object.location - camera_obj.location
    camera_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    return camera_obj


def create_camera_look_at_origin(location, fov=30):
    # remove other cameras
    bpy.ops.object.select_all(action='DESELECT')
    obj = bpy.data.objects.get("Camera")
    if obj is not None:
        obj.select_set(True)
        bpy.ops.object.delete()

    camera_data = bpy.data.cameras.new("Camera")
    camera_data.angle = fov * (math.pi / 180)  # Convert degrees to radians
    camera_obj = bpy.data.objects.new("Camera", camera_data)
    bpy.context.collection.objects.link(camera_obj)
    camera_obj.location = location

    # Make the camera look at the target object
    direction = mathutils.Vector([0, 0, 0]) - camera_obj.location
    camera_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    return camera_obj


def create_camera(transform_matrix, fov=30):
    # remove other cameras
    bpy.ops.object.select_all(action='DESELECT')
    obj = bpy.data.objects.get("Camera")
    if obj is not None:
        obj.select_set(True)
        bpy.ops.object.delete()

    camera_data = bpy.data.cameras.new("Camera")
    camera_data.angle = fov * (math.pi / 180.)  # Convert degrees to radians
    camera_obj = bpy.data.objects.new("Camera", camera_data)
    bpy.context.collection.objects.link(camera_obj)

    m = mathutils.Matrix(transform_matrix)
    camera_obj.location = mathutils.Vector([transform_matrix[0][3], transform_matrix[1][3], transform_matrix[2][3]])
    camera_obj.rotation_mode = "QUATERNION"
    camera_obj.rotation_quaternion = m.to_3x3().to_quaternion()

    return camera_obj


def look_at_to_c2w(camera_position, target_position=[0.0, 0.0, 0.0], up_dir=[0.0, 0.0, 1.0]):
    """
    Look at transform matrix
    :param camera_position: camera position
    :param target_position: target position, default is origin
    :param up_dir: up vector, default is z-axis up
    :return: camera to world matrix
    """
    camera_direction = np.array(camera_position) - np.array(target_position)
    camera_direction = camera_direction / np.linalg.norm(camera_direction)
    camera_right = np.cross(np.array(up_dir), camera_direction)
    camera_right = camera_right / np.linalg.norm(camera_right)
    camera_up = np.cross(camera_direction, camera_right)
    camera_up = camera_up / np.linalg.norm(camera_up)
    rotation_transform = np.zeros((4, 4))
    rotation_transform[0, :3] = camera_right
    rotation_transform[1, :3] = camera_up
    rotation_transform[2, :3] = camera_direction
    rotation_transform[-1, -1] = 1.0
    translation_transform = np.eye(4)
    translation_transform[:3, -1] = -np.array(camera_position)
    look_at_transform = np.matmul(rotation_transform, translation_transform)
    return np.linalg.inv(look_at_transform)
