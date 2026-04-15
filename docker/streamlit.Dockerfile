FROM python:3.14-rc-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app/src
CMD ["streamlit", "run", "src/streamlit/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
