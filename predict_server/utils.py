import math
import numpy as np
import quaternion

def make_other_eye_projection(projection):
    return [
        -projection[2],
        projection[1],
        -projection[0],
        projection[3]
    ]


def make_camera_projection(eye_projection, overfilling):
    return [
        math.tan(math.atan(eye_projection[0]) - overfilling[0]),
        math.tan(math.atan(eye_projection[1]) + overfilling[1]),
        math.tan(math.atan(eye_projection[2]) + overfilling[2]),
        math.tan(math.atan(eye_projection[3]) - overfilling[3])
    ]


def calc_optimal_projection(hmd_orientation, frame_orientation, eye_projection):
    q_hmd = np.quaternion(
        hmd_orientation[0],
        hmd_orientation[1],
        hmd_orientation[2],
        hmd_orientation[3]
    )
    q_frame = np.quaternion(
        frame_orientation[0],
        frame_orientation[1],
        frame_orientation[2],
        frame_orientation[3]
    )

    q_d = np.matmul(
        np.linalg.inv(quaternion.as_rotation_matrix(q_hmd)),
        quaternion.as_rotation_matrix(q_frame)
    )

    lt = np.matmul(q_d, [eye_projection[0], eye_projection[1], 1])
    p_lt = np.dot(lt, 1 / lt[2])
    
    rt = np.matmul(q_d, [eye_projection[2], eye_projection[1], 1])
    p_rt = np.dot(rt, 1 / rt[2])

    rb = np.matmul(q_d, [eye_projection[2], eye_projection[3], 1])
    p_rb = np.dot(rb, 1 / rb[2])

    lb = np.matmul(q_d, [eye_projection[0], eye_projection[3], 1])
    p_lb = np.dot(lb, 1 / lb[2])

    p_l = min(p_lt[0], p_rt[0], p_rb[0], p_lb[0])
    p_t = max(p_lt[1], p_rt[1], p_rb[1], p_lb[1])
    p_r = max(p_lt[0], p_rt[0], p_rb[0], p_lb[0])
    p_b = min(p_lt[1], p_rt[1], p_rb[1], p_lb[1])

    return [
        min(p_l, eye_projection[0]),
        max(p_t, eye_projection[1]),
        max(p_r, eye_projection[2]),
        min(p_b, eye_projection[3])
    ]


def calc_overhead(eye_projection, frame_projection):
    a_eye = (eye_projection[2] - eye_projection[0]) * (eye_projection[1] - eye_projection[3])
    a_frame = (frame_projection[2] - frame_projection[0]) * (frame_projection[1] - frame_projection[3])

    return a_frame / a_eye - 1