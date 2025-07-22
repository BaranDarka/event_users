FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY . .

# Tell Streamlit to listen on $PORT (Cloud Run default) and all interfaces
CMD ["streamlit", "run", "main.py", "--server.port=8080", "--server.address=0.0.0.0"]
