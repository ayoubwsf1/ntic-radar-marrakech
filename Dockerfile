FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV RADAR_DB=/data/stages.db
EXPOSE 8501
CMD streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0
