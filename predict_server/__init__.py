import math
import asyncio
import time
import zmq
import cbor2
from abc import abstractmethod, ABCMeta
from zmq.asyncio import Context, Poller

from ._types import MotionData, PredictedData
from ._writer import PredictionOutputWriter, PerfMetricWriter


class PredictModule(metaclass=ABCMeta):
    @abstractmethod
    def predict(self, motion_data):
        pass

    @abstractmethod
    def feedback_received(self, feedback):
        pass

    def make_camera_projection(self, motion_data, overfilling):
        return [
            math.tan(math.atan(motion_data.camera_projection[0]) - overfilling[0]),
            math.tan(math.atan(motion_data.camera_projection[1]) + overfilling[1]),
            math.tan(math.atan(motion_data.camera_projection[2]) + overfilling[2]),
            math.tan(math.atan(motion_data.camera_projection[3]) - overfilling[3])
        ]        


class MotionPredictServer:
    def __init__(self, module, port_input, port_feedback,
                 prediction_output, metric_output):
        self.module = module
        self.port_input = port_input
        self.port_feedback = port_feedback
        self.feedbacks = {}

        self.prediction_output = PredictionOutputWriter(
            prediction_output
        ) if prediction_output is not None else None
        
        self.metric_writer = PerfMetricWriter(
            metric_output
        ) if metric_output is not None else None

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

                prediction_time, orientation, projection, \
                    left_eye_position, right_eye_position, \
                    right_hand_position, right_hand_orientation = \
                    self.module.predict(motion_data)
                
                predicted_data = PredictedData(motion_data.timestamp,
                                               prediction_time,
                                               orientation,
                                               projection,
                                               left_eye_position,
                                               right_eye_position,
                                               right_hand_position,
                                               right_hand_orientation)
                
                self.end_prediction(motion_data.timestamp)
            
                motion_predicted_output.send(predicted_data.pack())

                if self.prediction_output is not None:
                    self.prediction_output.write(motion_data, predicted_data)
                
            if feedback_recv in dict(events):
                feedback = await feedback_recv.recv()
                self.merge_feedback(cbor2.loads(feedback))

    # process feedbacks
    def start_prediction(self, session):
        assert(session not in self.feedbacks)
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
        self.feedbacks[session] = {**entry, **feedback}

        if entry['srcmask'] == 0b11:
            if self.metric_writer is not None:
                self.metric_writer.write_metric(self.feedbacks[session])

            self.module.feedback_received(self.feedbacks[session])
                
            self.feedbacks = {
                s: self.feedbacks[s] for s in self.feedbacks if s > session
            }
