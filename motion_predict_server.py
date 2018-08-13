import asyncio
import struct
import time
import zmq
import cbor2
import csv
from abc import *
from zmq.asyncio import Context, Poller

class MotionData:
    @classmethod
    def from_bytes(cls, bytes):
        def float_list_from_bytes(bytes, count, pos):
            return list(struct.unpack_from('>{}f'.format(count), bytes, pos)), pos + 4 * count
        
        pos = 0

        header, sample_number = struct.unpack_from('BB', bytes, pos)
        assert((header & 0xFF) == 0xA0)
        pos += 2

        biosignal, pos = float_list_from_bytes(bytes, 8, pos)
        acceleration, pos = float_list_from_bytes(bytes, 3, pos)
        angular_velocities, pos = float_list_from_bytes(bytes, 3, pos)
        magnetic_field, pos = float_list_from_bytes(bytes, 3, pos)
        orientation, pos = float_list_from_bytes(bytes, 4, pos)

        timestamp = struct.unpack_from('>q', bytes, pos)[0]
        pos += 8

        footer = struct.unpack_from('B', bytes, pos)[0]
        assert((footer & 0xF8) == 0xC0)

        return cls(sample_number, biosignal, acceleration, angular_velocities, magnetic_field, orientation, timestamp)
    
    def __init__(self, sample_number, biosignal, acceleration, angular_velocities,
                 magnetic_field, orientation, timestamp):
        self.sample_number = sample_number
        self.biosignal = biosignal
        self.acceleration = acceleration
        self.angular_velocities = angular_velocities
        self.magnetic_field = magnetic_field
        self.orientation = orientation
        self.timestamp = timestamp

    def __str__(self):
        return ("sample {0}, biosignal {1}, acceleration {2}, angular velocities {3}, "
                "magnetic field {4}, orientation {5}, timestamp {6}").format(
                    self.sample_number, self.biosignal, self.acceleration, self.angular_velocities,
                    self.magnetic_field, self.orientation, self.timestamp
                    )

class PredictedData:
    def __init__(self, timestamp, prediction_time, orientation):
        self.timestamp = timestamp
        self.prediction_time = prediction_time
        self.orientation = orientation

    def pack(self):
        return struct.pack('>q5f',
                           self.timestamp,
                           self.prediction_time,
                           self.orientation[0],
                           self.orientation[1],
                           self.orientation[2],
                           self.orientation[3])

class PredictModule(metaclass=ABCMeta):
    @abstractmethod
    def predict(self, motion_data):
        pass

class MotionPredictSimulator:
    def __init__(self, module, input_motion_data, prediction_output):
        self.module = module
        self.input_motion_data = input_motion_data
        self.prediction_output = PredictionOutputWriter(prediction_output) if prediction_output is not None else None

    def run(self):
        with open(self.input_motion_data, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                motion_data = MotionData(
                    0,
                    [ float(row["biosignal_0"]), float(row["biosignal_1"]),
                      float(row["biosignal_2"]), float(row["biosignal_3"]),
                      float(row["biosignal_4"]), float(row["biosignal_5"]),
                      float(row["biosignal_6"]), float(row["biosignal_7"]) ],
                    [ float(row["acceleration_x"]),
                      float(row["acceleration_y"]),
                      float(row["acceleration_z"]) ],
                    [ float(row["angular_vec_x"]),
                      float(row["angular_vec_y"]),
                      float(row["angular_vec_z"]) ],
                    [ float(row["magnetic_x"]),
                      float(row["magnetic_y"]),
                      float(row["magnetic_z"]) ],
                    [ float(row["input_orientation_x"]),
                      float(row["input_orientation_y"]),
                      float(row["input_orientation_z"]),
                      float(row["input_orientation_w"]) ],
                    float(row["timestamp"])
                )

                predicted_orientation, prediction_time = self.module.predict(motion_data)
                predicted_data = PredictedData(motion_data.timestamp,
                                               prediction_time,
                                               predicted_orientation)

                if self.prediction_output is not None:
                    self.prediction_output.write(motion_data, predicted_data)

class MotionPredictServer:
    def __init__(self, module, port_input, port_feedback, prediction_output, metric_output):
        self.module = module
        self.port_input = port_input
        self.port_feedback = port_feedback
        self.feedbacks = {}

        self.prediction_output = PredictionOutputWriter(prediction_output) if prediction_output is not None else None
        self.metric_writer = PerfMetricWriter(metric_output) if metric_output is not None else None

    def run(self):
        context = Context.instance()
        self.event_loop = asyncio.get_event_loop()

        self.event_loop.run_until_complete(self.loop(context))

    def shutdown(self):
        self.event_loop.close()

        if self.prediction_output is not None:
            self.prediction_output.close()

        if self.metric_writer is not None:
            self.metric_writer.close()

    async def loop(self, context):
        motion_raw_input = context.socket(zmq.PULL)
        motion_raw_input.bind("tcp://*:" + str(self.port_input))

        motion_predicted_output = context.socket(zmq.PUSH)
        motion_predicted_output.bind("tcp://*:" + str(self.port_input + 1))

        feedback_recv = context.socket(zmq.PULL)
        feedback_recv.bind("tcp://*:" + str(self.port_feedback))

        poller = Poller()
        poller.register(motion_raw_input, zmq.POLLIN)
        poller.register(feedback_recv, zmq.POLLIN)

        while True:
            events = await poller.poll(100)
            if motion_raw_input in dict(events):
                frame = await motion_raw_input.recv(0, False)
                motion_data = MotionData.from_bytes(frame.bytes)

                self.start_prediction(motion_data.timestamp)

                predicted_orientation, prediction_time = self.module.predict(motion_data)
                predicted_data = PredictedData(motion_data.timestamp,
                                               prediction_time,
                                               predicted_orientation)
                
                self.end_prediction(motion_data.timestamp)
            
                motion_predicted_output.send(predicted_data.pack())

                if self.prediction_output is not None:
                    self.prediction_output.write(motion_data, predicted_data)
                
            if feedback_recv in dict(events):
                feedback = await feedback_recv.recv()
                self.merge_feedback(cbor2.loads(feedback))

    # process feedbacks
    def start_prediction(self, session):
        assert(not session in self.feedbacks)
        self.feedbacks[session] = {
            'srcmask': 0,
            'startPrediction': time.clock()
        }

    def end_prediction(self, session):
        self.feedbacks[session]['stopPrediction'] = time.clock()

    def merge_feedback(self, feedback):
        if not all(key in feedback for key in ('session', 'source')):
            return

        if not feedback['session'] in self.feedbacks:
            return
        
        session = feedback['session']
        entry = self.feedbacks[session]
        
        if feedback['source'] == 'acli':
            entry['srcmask'] |= 0b01
        elif feedback['source'] == 'asrv':
            entry['srcmask'] |= 0b10
        else:
            return

        del feedback['source']
        self.feedbacks[session] = { **entry, **feedback }

        if entry['srcmask'] == 0b11:
            if self.metric_writer is not None:
                self.metric_writer.write_metric(self.feedbacks[session])
                
            self.feedbacks = { s:self.feedbacks[s] for s in self.feedbacks if s > session }

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
            'predicted_orientation_x',
            'predicted_orientation_y',
            'predicted_orientation_z',
            'predicted_orientation_w',
            'prediction_time'
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
            str(predicted_data.orientation[0]),
            str(predicted_data.orientation[1]),
            str(predicted_data.orientation[2]),
            str(predicted_data.orientation[3]),
            str(predicted_data.prediction_time)
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
        
        start_prediction_send_predicted = feedback['stopPrediction'] - feedback['startPrediction']
        send_predicted_start_server_render = feedback['startServerRender'] - feedback['startSimulation']
        start_server_render_start_encode = feedback['startEncode'] - feedback['startServerRender']
        start_encode_send_video = feedback['sendVideo'] - feedback['startEncode']
        start_recv_video_start_decode = feedback['startDecode'] - feedback['firstFrameReceived']
        start_decode_start_client_render = feedback['startClientRender'] - feedback['startDecode']
        start_client_render_end_client_render = feedback['endClientRender'] - feedback['startClientRender']
        
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
