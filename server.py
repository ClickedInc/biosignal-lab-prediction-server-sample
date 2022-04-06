from math import radians
import sys
import getopt

from numpy import deg2rad
from predict_server import PredictModule, MotionPredictServer
from predict_server.simulator import MotionPredictSimulator
import predict_server.utils
# from predict_server import BufferedNoPrediction


class App(PredictModule):
    def __init__(self):
        # self.prediction = BufferedNoPrediction(20, 100)
        self.sum_overall_latency = 0
        self.count_overall_latency = 0
        pass

    def parse_command_args(self):
        port = 5555
        feedback = 5554
        input_file = output = metric_output = game_event_output = None
        accept_client_buttons = False
        
        try:
            opts, _args = getopt.getopt(sys.argv[1:], "p:f:m:o:i:g:", ["accept-client-buttons"])
        except getopt.GetoptError as err:
            print(err)
            sys.exit(1)

        for opt, arg in opts:
            if opt == "-p":
                port = int(arg)
            elif opt == "-f":
                feedback = int(arg)
            elif opt == "-i":
                input_file = arg
            elif opt == "-o":
                output = arg
            elif opt == "-m":
                metric_output = arg
            elif opt == "-g":
                game_event_output = arg
            elif opt == "--accept-client-buttons":
                accept_client_buttons = True
            else:
                assert False, "unhandled option"
                
        return port, feedback, input_file, output, metric_output, game_event_output, accept_client_buttons

    def run(self):
        port_input, port_feedback, input_file, output, metric_output, game_event_output, accept_client_buttons = \
            self.parse_command_args()
        if input_file is None:
            assert(port_input is not None and port_feedback is not None)
            
            server = MotionPredictServer(
                self, port_input, port_feedback, output, metric_output, game_event_output, accept_client_buttons
            )

            server.run()
                
        else:
            assert(output is not None)

            simulator = MotionPredictSimulator(self, input_file, output)

            try:                
                simulator.run()
            except KeyboardInterrupt:
                pass
    
    # implements PredictModule
    def predict(self, motion_data):
        # self.prediction.put_motion_data(motion_data)
        # return self.prediction.get_predicted_result()

        # no prediction
        prediction_time = 150.0  # ms
        predicted_left_eye_pos = motion_data.left_eye_position
        predicted_right_eye_pos = motion_data.right_eye_position
        predicted_head_orientation = motion_data.head_orientation

        # overfilling delta in radian (left, top, right, bottom)
        overfilling = [radians(10), radians(10), radians(10), radians(10)]

        left_eye_projection = motion_data.camera_projection
        predicted_left_camera_projection = predict_server.utils.make_camera_projection(left_eye_projection, overfilling)

        right_eye_projection = predict_server.utils.make_other_eye_projection(left_eye_projection)
        predicted_right_camera_projection = predict_server.utils.make_camera_projection(right_eye_projection, overfilling)

        predicted_right_hand_pos = motion_data.right_hand_position
        predicted_right_hand_ori = motion_data.right_hand_orientation

        foveation_inner_radius = 1.06
        foveation_middle_radius = 1.42

        return prediction_time, \
               predicted_left_eye_pos, \
               predicted_right_eye_pos, \
               predicted_head_orientation, \
               predicted_left_camera_projection, \
               predicted_right_camera_projection, \
               foveation_inner_radius, \
               foveation_middle_radius, \
               predicted_right_hand_pos, \
               predicted_right_hand_ori

    def feedback_received(self, feedback):
        # see PrefMetricWriter.write_metric() to understand feedback values
        # (motion_prediction_server.py:320)
        
        # example : calculate overall latency
        #
        self.sum_overall_latency += feedback['endClientRender'] - feedback['gatherInput']
        self.count_overall_latency += 1

        if self.count_overall_latency >= 72:
            print("avg. overall latency: " + str(self.sum_overall_latency / self.count_overall_latency), flush=True)
            self.sum_overall_latency = 0
            self.count_overall_latency = 0

        pass

    def external_input_received(self, input_data):
        #print(input_data, flush=True)
        pass
    
    def game_event_received(self, event):
        print(event, flush=True)
        pass
    
def main():
    app = App()
    app.run()

    
if __name__ == "__main__":
    main()
