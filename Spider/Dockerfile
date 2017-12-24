FROM python:3.5

MAINTAINER Red Red.Guan@gmail.com

COPY . /wls/app/Spider

WORKDIR	/wls/app/Spider

RUN pip install -r requirement.txt

VOLUMN /home/worker/

CMD ["python", "main.py"]