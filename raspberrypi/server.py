import time
from concurrent import futures

import grpc

import lock_pb2
import lock_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class GlockServer(lock_pb2_grpc.GLOCKServicer):
    def Unlock(self, request, context):
        return lock_pb2.GlockResponse(message='got unlock rpc')


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lock_pb2_grpc.add_GLOCKServicer_to_server(GlockServer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()