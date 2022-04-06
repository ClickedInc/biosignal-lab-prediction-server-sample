import math
from . import utils

from abc import abstractmethod, ABCMeta

def quat_to_euler(x, y, z, w):
    siny_cosp = 2 * (w * y - z * x)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    sinp = 2 * (w * z + x * y)
    if abs(sinp) >= 1:
        roll = math.copysign(math.pi / 2, sinp)
    else:
        roll = math.asin(sinp)

    sinx_cosp = 2 * (w * x - y * z)
    cosx_cosp = 1 - 2 * (z * z + x * x)
    pitch = math.atan2(sinx_cosp, cosx_cosp)

    return [yaw, pitch, roll]    


class CsvWriter(metaclass=ABCMeta):
    def __init__(self, output):
        self.output = open(output, 'w')
        self.write_line(self.make_header_items())

    def write_line(self, items):
        self.output.write(','.join(items) + '\n')
        self.output.flush()

    def close(self):
        self.output.close()

    @abstractmethod
    def make_header_items(self):
        pass

    
class PredictionOutputWriter(CsvWriter):
    def __init__(self, output):
        super().__init__(output)

    def make_header_items(self):
        return [
            'timestamp',
            'input_left_eye_position_x',
            'input_left_eye_position_y',
            'input_left_eye_position_z',
            'input_right_eye_position_x',
            'input_right_eye_position_y',
            'input_right_eye_position_z',
            'input_head_orientation_x',
            'input_head_orientation_y',
            'input_head_orientation_z',
            'input_head_orientation_w',
            'input_head_orientation_yaw',
            'input_head_orientation_pitch',
            'input_head_orientation_roll',
            'input_head_acceleration_x',
            'input_head_acceleration_y',
            'input_head_acceleration_z',
            'input_head_angular_vec_x',
            'input_head_angular_vec_y',
            'input_head_angular_vec_z',
            'input_camera_projection_left',
            'input_camera_projection_top',
            'input_camera_projection_right',
            'input_camera_projection_bottom',
            'input_right_hand_position_x',
            'input_right_hand_position_y',
            'input_right_hand_position_z',
            'input_right_hand_orientation_x',
            'input_right_hand_orientation_y',
            'input_right_hand_orientation_z',
            'input_right_hand_orientation_w',
            'input_right_hand_orientation_yaw',
            'input_right_hand_orientation_pitch',
            'input_right_hand_orientation_roll',
            'input_right_hand_acceleration_x',
            'input_right_hand_acceleration_y',
            'input_right_hand_acceleration_z',
            'input_right_hand_angular_vec_x',
            'input_right_hand_angular_vec_y',
            'input_right_hand_angular_vec_z',
            'prediction_time',
            'predicted_left_eye_position_x',
            'predicted_left_eye_position_y',
            'predicted_left_eye_position_z',
            'predicted_right_eye_position_x',
            'predicted_right_eye_position_y',
            'predicted_right_eye_position_z',
            'predicted_head_orientation_x',
            'predicted_head_orientation_y',
            'predicted_head_orientation_z',
            'predicted_head_orientation_w',
            'predicted_head_orientation_yaw',
            'predicted_head_orientation_pitch',
            'predicted_head_orientation_roll',
            'predicted_left_camera_projection_left',
            'predicted_left_camera_projection_top',
            'predicted_left_camera_projection_right',
            'predicted_left_camera_projection_bottom',
            'predicted_right_camera_projection_left',
            'predicted_right_camera_projection_top',
            'predicted_right_camera_projection_right',
            'predicted_right_camera_projection_bottom',
            'predicted_foveation_inner_radius',
            'predicted_foveation_middle_radius',
            'predicted_right_hand_position_x',
            'predicted_right_hand_position_y',
            'predicted_right_hand_position_z',
            'predicted_right_hand_orientation_x',
            'predicted_right_hand_orientation_y',
            'predicted_right_hand_orientation_z',
            'predicted_right_hand_orientation_w',
            'predicted_right_hand_orientation_yaw',
            'predicted_right_hand_orientation_pitch',
            'predicted_right_hand_orientation_roll'
        ]

    def write(self, motion_data, predicted_data):
        input_head_orientation_euler = quat_to_euler(
            motion_data.head_orientation[0],
            motion_data.head_orientation[1],
            motion_data.head_orientation[2],
            motion_data.head_orientation[3] 
        )
        predicted_head_orientation_euler = quat_to_euler(
            predicted_data.predicted_head_orientation[0],
            predicted_data.predicted_head_orientation[1],
            predicted_data.predicted_head_orientation[2],
            predicted_data.predicted_head_orientation[3]
        )
        input_right_hand_orientation_euler = quat_to_euler(
            motion_data.right_hand_orientation[0],
            motion_data.right_hand_orientation[1],
            motion_data.right_hand_orientation[2],
            motion_data.right_hand_orientation[3]
        )
        predicted_right_hand_orientation_euler = quat_to_euler(
            predicted_data.predicted_right_hand_orientation[0],
            predicted_data.predicted_right_hand_orientation[1],
            predicted_data.predicted_right_hand_orientation[2],
            predicted_data.predicted_right_hand_orientation[3]
        )
        
        self.write_line([
            str(motion_data.timestamp),
            str(motion_data.left_eye_position[0]),
            str(motion_data.left_eye_position[1]),
            str(motion_data.left_eye_position[2]),
            str(motion_data.right_eye_position[0]),
            str(motion_data.right_eye_position[1]),
            str(motion_data.right_eye_position[2]),
            str(motion_data.head_orientation[0]),
            str(motion_data.head_orientation[1]),
            str(motion_data.head_orientation[2]),
            str(motion_data.head_orientation[3]),
            str(input_head_orientation_euler[0]),
            str(input_head_orientation_euler[1]),
            str(input_head_orientation_euler[2]),
            str(motion_data.head_acceleration[0]),
            str(motion_data.head_acceleration[1]),
            str(motion_data.head_acceleration[2]),
            str(motion_data.head_angular_velocity[0]),
            str(motion_data.head_angular_velocity[1]),
            str(motion_data.head_angular_velocity[2]),
            str(motion_data.camera_projection[0]),
            str(motion_data.camera_projection[1]),
            str(motion_data.camera_projection[2]),
            str(motion_data.camera_projection[3]),
            str(motion_data.right_hand_position[0]),
            str(motion_data.right_hand_position[1]),
            str(motion_data.right_hand_position[2]),
            str(input_right_hand_orientation_euler[0]),
            str(input_right_hand_orientation_euler[1]),
            str(input_right_hand_orientation_euler[2]),
            str(motion_data.right_hand_orientation[0]),
            str(motion_data.right_hand_orientation[1]),
            str(motion_data.right_hand_orientation[2]),
            str(motion_data.right_hand_orientation[3]),
            str(motion_data.right_hand_acceleration[0]),
            str(motion_data.right_hand_acceleration[1]),
            str(motion_data.right_hand_acceleration[2]),
            str(motion_data.right_hand_angular_velocity[0]),
            str(motion_data.right_hand_angular_velocity[1]),
            str(motion_data.right_hand_angular_velocity[2]),
            str(predicted_data.prediction_time),
            str(predicted_data.predicted_left_eye_position[0]),
            str(predicted_data.predicted_left_eye_position[1]),
            str(predicted_data.predicted_left_eye_position[2]),
            str(predicted_data.predicted_right_eye_position[0]),
            str(predicted_data.predicted_right_eye_position[1]),
            str(predicted_data.predicted_right_eye_position[2]),
            str(predicted_data.predicted_head_orientation[0]),
            str(predicted_data.predicted_head_orientation[1]),
            str(predicted_data.predicted_head_orientation[2]),
            str(predicted_data.predicted_head_orientation[3]),
            str(predicted_head_orientation_euler[0]),
            str(predicted_head_orientation_euler[1]),
            str(predicted_head_orientation_euler[2]),
            str(predicted_data.predicted_left_camera_projection[0]),
            str(predicted_data.predicted_left_camera_projection[1]),
            str(predicted_data.predicted_left_camera_projection[2]),
            str(predicted_data.predicted_left_camera_projection[3]),
            str(predicted_data.predicted_right_camera_projection[0]),
            str(predicted_data.predicted_right_camera_projection[1]),
            str(predicted_data.predicted_right_camera_projection[2]),
            str(predicted_data.predicted_right_camera_projection[3]),
            str(predicted_data.predicted_foveation_inner_radius),
            str(predicted_data.predicted_foveation_middle_radius),
            str(predicted_data.predicted_right_hand_position[0]),
            str(predicted_data.predicted_right_hand_position[1]),
            str(predicted_data.predicted_right_hand_position[2]),
            str(predicted_data.predicted_right_hand_orientation[0]),
            str(predicted_data.predicted_right_hand_orientation[1]),
            str(predicted_data.predicted_right_hand_orientation[2]),
            str(predicted_data.predicted_right_hand_orientation[3]),
            str(predicted_right_hand_orientation_euler[0]),
            str(predicted_right_hand_orientation_euler[1]),
            str(predicted_right_hand_orientation_euler[2])
        ])

        
class PerfMetricWriter(CsvWriter):
    def __init__(self, output):
        super().__init__(output)

    def make_header_items(self):
        return [
            'timestamp',
            'input_orientation_x',
            'input_orientation_y',
            'input_orientation_z',
            'input_orientation_w',
            'input_orientation_yaw',
            'input_orientation_pitch',
            'input_orientation_roll',
            'input_projection_left',
            'input_projection_top',
            'input_projection_right',
            'input_projection_bottom',
            'predicted_orientation_x',
            'predicted_orientation_y',
            'predicted_orientation_z',
            'predicted_orientation_w',
            'predicted_orientation_yaw',
            'predicted_orientation_pitch',
            'predicted_orientation_roll',
            'predicted_projection_left',
            'predicted_projection_top',
            'predicted_projection_right',
            'predicted_projection_bottom',
            'overall_latency',
            'gather_input_start_prediction',
            'start_prediction_send_predicted',
            'send_predicted_start_server_render',
            'start_server_render_start_encode',
            'start_encode_send_video',
            'send_video_start_recv_video',
            'start_recv_video_start_decode',
            'start_decode_start_client_render',
            'start_client_render_end_client_render',
            'frame_type',
            'frame_size',
            'optimal_overhead',
            'actual_overhead'
        ]

    def write_metric(self, feedback):
        # latency
        overall_latency = feedback['endClientRender'] - feedback['gatherInput']
        
        start_prediction_send_predicted = \
            feedback['stopPrediction'] - feedback['startPrediction']
        send_predicted_start_server_render = \
            feedback['startServerRender'] - feedback['startSimulation']
        start_server_render_start_encode = \
            feedback['startEncode'] - feedback['startServerRender']
        start_encode_send_video = \
            feedback['sendVideo'] - feedback['startEncode']
        start_recv_video_start_decode = \
            feedback['startDecode'] - feedback['firstFrameReceived']
        start_decode_start_client_render = \
            feedback['startClientRender'] - feedback['startDecode']
        start_client_render_end_client_render = \
            feedback['endClientRender'] - feedback['startClientRender']
        
        rtt = overall_latency - (
            start_prediction_send_predicted +
            send_predicted_start_server_render +
            start_server_render_start_encode +
            start_encode_send_video +
            start_recv_video_start_decode +
            start_decode_start_client_render +
            start_client_render_end_client_render
        )

        gather_input_start_prediction = send_video_start_recv_video = rtt / 2

        # overhead
        hmd_orientation = [
            feedback['hmdOrientationW'],
            -feedback['hmdOrientationX'],
            -feedback['hmdOrientationY'],
            feedback['hmdOrientationZ'],
        ]
        left_eye_projection = [
            feedback['hmdProjectionL'],
            feedback['hmdProjectionT'],
            feedback['hmdProjectionR'],
            feedback['hmdProjectionB']
        ]
        frame_orientation = [
            feedback['frameOrientationW'],
            -feedback['frameOrientationX'],
            -feedback['frameOrientationY'],
            feedback['frameOrientationZ']
        ]
        left_frame_projection = [
            feedback['frameProjectionLL'],
            feedback['frameProjectionLT'],
            feedback['frameProjectionLR'],
            feedback['frameProjectionLB']
        ]
        right_frame_projection = [
            feedback['frameProjectionRL'],
            feedback['frameProjectionRT'],
            feedback['frameProjectionRR'],
            feedback['frameProjectionRB']
        ]

        left_optimal_overhead = utils.calc_overhead(
            left_eye_projection,
            utils.calc_optimal_projection(hmd_orientation, frame_orientation, left_eye_projection)
        )
        left_actual_overhead = utils.calc_overhead(left_eye_projection, left_frame_projection)
        
        right_eye_projection = utils.make_other_eye_projection(left_eye_projection)
        right_optimal_overhead = utils.calc_overhead(
            right_eye_projection,
            utils.calc_optimal_projection(hmd_orientation, frame_orientation, right_eye_projection)
        )
        right_actual_overhead = utils.calc_overhead(right_eye_projection, right_frame_projection)

        hmd_orientation_euler = quat_to_euler(
            hmd_orientation.x,
            hmd_orientation.y,
            hmd_orientation.z,
            hmd_orientation.w
        )
        frame_orientation_euler = quat_to_euler(
            frame_orientation.x,
            frame_orientation.y,
            frame_orientation.z,
            frame_orientation.w
        )

        self.write_line([
            str(feedback['session']),
            str(-feedback['hmdOrientationX']),
            str(-feedback['hmdOrientationY']),
            str(feedback['hmdOrientationZ']),
            str(feedback['hmdOrientationW']),
            str(hmd_orientation_euler[0]),
            str(hmd_orientation_euler[1]),
            str(hmd_orientation_euler[2]),
            str(feedback['hmdProjectionL']),
            str(feedback['hmdProjectionT']),
            str(feedback['hmdProjectionR']),
            str(feedback['hmdProjectionB']),
            str(-feedback['frameOrientationX']),
            str(-feedback['frameOrientationY']),
            str(feedback['frameOrientationZ']),
            str(feedback['frameOrientationW']),
            str(frame_orientation_euler[0]),
            str(frame_orientation_euler[1]),
            str(frame_orientation_euler[2]),
            str(feedback['frameProjectionLL']),
            str(feedback['frameProjectionLT']),
            str(feedback['frameProjectionLR']),
            str(feedback['frameProjectionLB']),
            str(feedback['frameProjectionRL']),
            str(feedback['frameProjectionRT']),
            str(feedback['frameProjectionRR']),
            str(feedback['frameProjectionRB']),
            str(overall_latency),
            str(gather_input_start_prediction),
            str(start_prediction_send_predicted),
            str(send_predicted_start_server_render),
            str(start_server_render_start_encode),
            str(start_encode_send_video),
            str(send_video_start_recv_video),
            str(start_recv_video_start_decode),
            str(start_decode_start_client_render),
            str(start_client_render_end_client_render),
            str("{:.0f}".format(feedback['frameType'])),
            str("{:.0f}".format(feedback['frameSize'])),
            str((left_optimal_overhead + right_optimal_overhead) / 2),
            str((left_actual_overhead + right_actual_overhead) / 2)
        ])


class GameEventWriter(CsvWriter):
    def __init__(self, output):
        super().__init__(output)

    def make_header_items(self):
        return [
            'timestamp',
            'type',
            'id',
            'event'
        ]

    def write(self, event):
        self.write_line([
            str(event['timestamp']),
            str(event['type']),
            str(event['id']),
            str(event['event'])
        ])
    