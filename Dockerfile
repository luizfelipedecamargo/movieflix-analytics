FROM python:3.11-alpine

WORKDIR /app

COPY app/requirements.txt .
RUN pip install -r requirements.txt

COPY app/ .

CMD ["sh", "-c",
"python collect_and_generate.py && \
python load_to_postgres.py && \
python run_analytics.py"]
