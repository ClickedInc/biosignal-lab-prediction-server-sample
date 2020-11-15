import zmq

from ._types import MotionData, PredictedData, ExternalInputData

class MotionDataTransport:
    def __init__(self, owner):
        self.owner = owner
        self.accept_client_buttons = False

    def configure(self, context, poller, port_recv, port_send, accept_client_buttons):
        self.socket_recv = context.socket(zmq.PULL)
        self.socket_recv.bind("tcp://*:" + str(port_recv))

        self.socket_send = context.socket(zmq.PUSH)
        self.socket_send.bind("tcp://*:" + str(port_send))

        poller.register(self.socket_recv, zmq.POLLIN)

        self.accept_client_buttons = accept_client_buttons
        print("accept_client_buttons: " + str(accept_client_buttons))

    async def process_events(self, events, external_input):
        if self.socket_recv not in dict(events):
            return

        frame = await self.socket_recv.recv(0, False)
        motion_data = MotionData.from_bytes(frame.bytes)

        self.owner.pre_predict_motion(motion_data.timestamp)

        prediction_time, left_eye_position, right_eye_position, \
            head_orientation, camera_projection, \
            right_hand_position, right_hand_orientation = \
            self.owner.predict_motion(motion_data)

        if self.accept_client_buttons:
            external_input.set_input(ExternalInputData(
                motion_data.timestamp,
                0,
                motion_data.right_hand_primary_button_press,
                motion_data.right_hand_primary_button_press
            ))

        # TODO: add all inputs to predicted data
        input_data = external_input.get_input(0)

        predicted_data = PredictedData(motion_data.timestamp,
                                        prediction_time,
                                        left_eye_position,
                                        right_eye_position,
                                        head_orientation,
                                        camera_projection,
                                        right_hand_position,
                                        right_hand_orientation,
                                        input_data.id,
                                        input_data.actual_press,
                                        input_data.predicted_press)

        self.owner.post_predict_motion(motion_data.timestamp)

        self.socket_send.send(predicted_data.pack())

        self.owner.write_prediction_output(motion_data, predicted_data)
