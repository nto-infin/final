FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY main.py /app

CMD ["streamlit", "run", "main.py", "--server.port=80", "--server.address=0.0.0.0"]
