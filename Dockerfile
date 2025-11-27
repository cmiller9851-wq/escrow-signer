FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY escrow_signer.py .

RUN adduser --disabled-password appuser && chown -R appuser /app
USER appuser

CMD ["python", "escrow_signer.py"]
