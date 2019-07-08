FROM python:3.6
MAINTAINER Oles Izovita 'oizovita@yahoo.com'
RUN apt-get update
RUN mkdir /app
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
ENTRYPOINT ["python3", "main.py"]