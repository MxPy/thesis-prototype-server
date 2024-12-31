FROM python:3.10

WORKDIR /app

COPY req.txt req.txt
RUN pip3 install -r req.txt

COPY mongoreq.txt mongoreq.txt
RUN pip3 install -r mongoreq.txt

COPY . .
RUN python -m grpc_tools.protoc -I ./protobuf --python_out=. --grpc_python_out=. auth.proto
RUN python -m grpc_tools.protoc -I ./protobuf --python_out=. --grpc_python_out=. user_auth.proto
EXPOSE 8000
CMD ["python3", "main.py"]