FROM python:3-alpine

ENV S3_BUCKET=
ENV AWS_ACCESS_KEY_ID=
ENV AWS_SECRET_ACCESS_KEY=

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000 

ENTRYPOINT ["python"]

CMD ["app.py"]