import grpc
from concurrent import futures
from unittest.mock import MagicMock

# Importy Protobufów
import user_auth_pb2
import user_auth_pb2_grpc

# Mockowany serwis gRPC
class MockAuthService(user_auth_pb2_grpc.AuthUserServiceServicer):
    def RegisterUser(self, request, context):
        if request.username == "existing_user":
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(f"User with username: {request.username} already exists")
            return user_auth_pb2.RegisterResponse()
        return user_auth_pb2.RegisterResponse(user_id="test_user_id")

    def GetUserByNickname(self, request, context):
        if request.username == "valid_user":
            return user_auth_pb2.UserResponse(
                username="valid_user",
                password="hashed_password",
                password_reset_code="hashed_reset_code",
                salt="salt",
                permission_level=1,
            )
        elif request.username == "nonexistent_user":
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"User with username: {request.username} doesn't exist")
            return user_auth_pb2.UserResponse()
        context.set_code(grpc.StatusCode.INTERNAL)
        context.set_details("Internal server error")
        return user_auth_pb2.UserResponse()

    def ResetPassword(self, request, context):
        if request.username == "valid_user":
            return user_auth_pb2.ResetPasswordResponse()
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details(f"User with username: {request.username} doesn't exist")
        return user_auth_pb2.ResetPasswordResponse()

# Funkcja do uruchamiania serwera gRPC
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    user_auth_pb2_grpc.add_AuthUserServiceServicer_to_server(MockAuthService(), server)
    server.add_insecure_port("[::]:50051")
    return server

if __name__ == "__main__":
    server = serve()
    print("gRPC server is running on port 50051...")
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Shutting down gRPC server...")
        server.stop(0)
