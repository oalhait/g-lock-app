import grpc

import lock_pb2
import lock_pb2_grpc


def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = lock_pb2_grpc.GLOCKStub(channel)
    response = stub.Unlock(lock_pb2.GlockRequest())
    print('Client received: {}'.format(response.message))


if __name__ == '__main__':
    run()