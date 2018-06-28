import asyncio
import signal
import struct
import sys
import time
import zmq
from zmq.asyncio import Context, Poller

class MotionData:
    def __init__(self, bytes):
        def float_list_from_bytes(bytes, count, pos):
            return list(struct.unpack_from('>{}f'.format(count), bytes, pos)), pos + 4 * count
        
        pos = 0

        header, self.sample_number = struct.unpack_from('BB', bytes, pos)
        assert((header & 0xFF) == 0xA0)
        pos += 2

        self.biosignal, pos = float_list_from_bytes(bytes, 8, pos)
        self.acceleration, pos = float_list_from_bytes(bytes, 3, pos)
        self.angular_velocities, pos = float_list_from_bytes(bytes, 3, pos)
        self.magnetic_field, pos = float_list_from_bytes(bytes, 3, pos)
        self.orientation, pos = float_list_from_bytes(bytes, 4, pos)

        self.timestamp = struct.unpack_from('>d', bytes, pos)[0]
        pos += 8

        footer = struct.unpack_from('B', bytes, pos)[0]
        assert((footer & 0xF8) == 0xC0)

    def __str__(self):
        return ("sample {0}, biosignal {1}, acceleration {2}, angular velocities {3}, "
                "magnetic field {4}, orientation {5}, timestamp {6}").format(
                    self.sample_number, self.biosignal, self.acceleration, self.angular_velocities,
                    self.magnetic_field, self.orientation, self.timestamp
                    )

class PredictedData:
    def __init__(self, timestamp, orientation, predictionTime):
        self.timestamp = timestamp
        self.orientation = orientation
        self.predictionTime = predictionTime

class PredictionServerData:
    def __init__(self, predictedData , originalOrientation):
        self.data = struct.pack('>d9f', predictedData.timestamp,
                                predictedData.orientation[0],predictedData.orientation[1],predictedData.orientation[2],predictedData.orientation[3], predictedData.predictionTime,
                                originalOrientation[0] , originalOrientation[1] , originalOrientation[2], originalOrientation[3])

def trivial_prediction(motion_data):
    # no prediction
    predictionTime = 100.0 #sample
    return PredictedData(motion_data.timestamp, motion_data.orientation, predictionTime)

async def server_loop(context, port, predict):
    motion_raw_input = context.socket(zmq.PULL)
    motion_raw_input.bind("tcp://*:" + str(port))

    stats_input = context.socket(zmq.PULL)
    stats_input.bind("tcp://*:" + str(port + 1))

    motion_predicted_output = context.socket(zmq.PUSH)
    motion_predicted_output.bind("tcp://*:" + str(port + 2))

    poller = Poller()
    poller.register(motion_raw_input, zmq.POLLIN)
    poller.register(stats_input, zmq.POLLIN)

    while True:
        events = await poller.poll(100)
        if motion_raw_input in dict(events):
            frame = await motion_raw_input.recv(0, False)
            motion_data = MotionData(frame.bytes)

            predicted_data = predict(motion_data)

            packet = PredictionServerData(predicted_data, motion_data.orientation)
            
            motion_predicted_output.send(packet.data)
        if stats_input in dict(events):
            stats = await stats_input.recv_json()
            print(stats)

def main():
    port = int(sys.argv[1])
    context = Context.instance()

    try:
        event_loop = asyncio.get_event_loop()

        # choose a prediction method
        predict = trivial_prediction
        
        event_loop.run_until_complete(server_loop(context, port, predict))
    except KeyboardInterrupt:
        pass
    finally:
        event_loop.close()

if __name__ == "__main__":
    main()
