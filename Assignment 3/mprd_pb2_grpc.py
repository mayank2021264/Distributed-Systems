# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import mprd_pb2 as mprd__pb2


class MapperStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Mapper = channel.unary_unary(
                '/Mapper/Mapper',
                request_serializer=mprd__pb2.DataRequest.SerializeToString,
                response_deserializer=mprd__pb2.DataResponse.FromString,
                )
        self.get_data = channel.unary_unary(
                '/Mapper/get_data',
                request_serializer=mprd__pb2.data.SerializeToString,
                response_deserializer=mprd__pb2.alldata.FromString,
                )


class MapperServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Mapper(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def get_data(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_MapperServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Mapper': grpc.unary_unary_rpc_method_handler(
                    servicer.Mapper,
                    request_deserializer=mprd__pb2.DataRequest.FromString,
                    response_serializer=mprd__pb2.DataResponse.SerializeToString,
            ),
            'get_data': grpc.unary_unary_rpc_method_handler(
                    servicer.get_data,
                    request_deserializer=mprd__pb2.data.FromString,
                    response_serializer=mprd__pb2.alldata.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Mapper', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Mapper(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Mapper(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Mapper/Mapper',
            mprd__pb2.DataRequest.SerializeToString,
            mprd__pb2.DataResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def get_data(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Mapper/get_data',
            mprd__pb2.data.SerializeToString,
            mprd__pb2.alldata.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class ReducerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Reducer = channel.unary_unary(
                '/Reducer/Reducer',
                request_serializer=mprd__pb2.red_req.SerializeToString,
                response_deserializer=mprd__pb2.DataResponse.FromString,
                )


class ReducerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Reducer(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ReducerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Reducer': grpc.unary_unary_rpc_method_handler(
                    servicer.Reducer,
                    request_deserializer=mprd__pb2.red_req.FromString,
                    response_serializer=mprd__pb2.DataResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Reducer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Reducer(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Reducer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Reducer/Reducer',
            mprd__pb2.red_req.SerializeToString,
            mprd__pb2.DataResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
