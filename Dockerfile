FROM python:3.10

WORKDIR /app

COPY req.txt req.txt
RUN pip3 install -r req.txt

COPY mongoreq.txt mongoreq.txt
RUN pip3 install -r mongoreq.txt

COPY . .

EXPOSE 8000
CMD ["python3", "main.py"]s