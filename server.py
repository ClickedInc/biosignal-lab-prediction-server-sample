import signal
import sys
import getopt
from motion_predict_server import PredictModule, MotionPredictServer, MotionPredictSimulator

class App(PredictModule):
    def parse_command_args(self):
        port = feedback = input_file = output = metric_output = None
        
        try:
            opts, args = getopt.getopt(sys.argv[1:], "p:f:m:o:i:")
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
            else:
                assert False, "unhandled option"
                
        return port, feedback, input_file, output, metric_output

    def run(self):
        port_input, port_feedback, input_file, output, metric_output = self.parse_command_args()
        if input_file == None:
            assert(port_input != None and port_feedback != None)
            
            server = MotionPredictServer(self, port_input, port_feedback, output, metric_output)

            try:
                server.run()
            except KeyboardInterrupt:
                pass
            finally:                
                server.shutdown()
                
        else:
            assert(output != None)

            simulator = MotionPredictSimulator(self, input_file, output)

            try:                
                simulator.run()
            except KeyboardInterrupt:
                pass
    
    # implements PredictModule
    def predict(self, motion_data):
        # no prediction
        predicted_orientation = motion_data.orientation
        prediction_time = 100.0  #sample

        return predicted_orientation, prediction_time

def main():
    app = App()
    app.run()

if __name__ == "__main__":
    main()
