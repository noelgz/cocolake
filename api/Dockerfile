FROM python:3.12-slim

WORKDIR /app

COPY api/requirements.txt ./api_requirements.txt
RUN pip install --no-cache-dir -r api_requirements.txt

COPY pipeline/requirements.txt ./pipeline_requirements.txt
RUN pip install --no-cache-dir -r pipeline_requirements.txt

COPY common/ ./common/

COPY pipeline/ ./pipeline/

# Copy the API code
COPY api/ ./api/

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
