FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend
COPY langgraph_layer /app/langgraph_layer

EXPOSE 8002

CMD ["uvicorn", "langgraph_layer.app:app", "--host", "0.0.0.0", "--port", "8002"]
