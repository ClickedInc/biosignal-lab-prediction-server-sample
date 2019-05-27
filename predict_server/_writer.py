from abc import abstractmethod, ABCMeta


class CsvWriter(metaclass=ABCMeta):
    def __init__(self, output):
        self.output = open(output, 'w')
        self.write_line(self.make_header_items())

    def write_line(self, items):
        self.output.write(','.join(items) + '\n')

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
            'biosignal_0',
            'biosignal_1',
            'biosignal_2',
            'biosignal_3',
            'biosignal_4',
            'biosignal_5',
            'biosignal_6',
            'biosignal_7',
            'acceleration_x',
            'acceleration_y',
            'acceleration_z',
            'angular_vec_x',
            'angular_vec_y',
            'angular_vec_z',
            'magnetic_x',
            'magnetic_y',
            'magnetic_z',
            'input_orientation_x',
            'input_orientation_y',
            'input_orientation_z',
            'input_orientation_w',
            'prediction_time',
            'predicted_orientation_x',
            'predicted_orientation_y',
            'predicted_orientation_z',
            'predicted_orientation_w',
            'fov',
            'overfilling_left',
            'overfilling_top',
            'overfilling_right',
            'overfilling_bottom'
        ]

    def write(self, motion_data, predicted_data):
        self.write_line([
            str(motion_data.timestamp),
            str(motion_data.biosignal[0]),
            str(motion_data.biosignal[1]),
            str(motion_data.biosignal[2]),
            str(motion_data.biosignal[3]),
            str(motion_data.biosignal[4]),
            str(motion_data.biosignal[5]),
            str(motion_data.biosignal[6]),
            str(motion_data.biosignal[7]),
            str(motion_data.acceleration[0]),
            str(motion_data.acceleration[1]),
            str(motion_data.acceleration[2]),
            str(motion_data.angular_velocities[0]),
            str(motion_data.angular_velocities[1]),
            str(motion_data.angular_velocities[2]),
            str(motion_data.magnetic_field[0]),
            str(motion_data.magnetic_field[1]),
            str(motion_data.magnetic_field[2]),
            str(motion_data.orientation[0]),
            str(motion_data.orientation[1]),
            str(motion_data.orientation[2]),
            str(motion_data.orientation[3]),
            str(predicted_data.prediction_time),
            str(predicted_data.orientation[0]),
            str(predicted_data.orientation[1]),
            str(predicted_data.orientation[2]),
            str(predicted_data.orientation[3]),
            str(motion_data.fov),
            str(predicted_data.overfilling[0]),
            str(predicted_data.overfilling[1]),
            str(predicted_data.overfilling[2]),
            str(predicted_data.overfilling[3])
        ])

        
class PerfMetricWriter(CsvWriter):
    def __init__(self, output):
        super().__init__(output)

    def make_header_items(self):
        return [
            'timestamp',
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
            'frame_size'
        ]

    def write_metric(self, feedback):
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

        self.write_line([
            str(feedback['session'] / 705600000.0),
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
            str("{:.0f}".format(feedback['frameSize']))
        ])
