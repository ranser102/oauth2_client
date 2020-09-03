FROM python:3.8-slim-buster
ENV LC_ALL=en_US.utf-8
ENV LANG=en_US.utf-8

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt \
    && apt-get update -y \
    && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

USER 1000
EXPOSE 5001 
ENTRYPOINT [ "python" ] 
CMD [ "adminapi.py" ] 
