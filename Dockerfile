FROM python:3.12.9-bookworm

RUN apt-get update && \
    apt-get install -y supervisor nano procps && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm /var/lib/apt/lists/* rm -rf /var/cache/apt/* 

COPY requirements.txt /opt/requirements.txt
RUN pip3 install -r /opt/requirements.txt
#RUN pip3 install supabase && pip3 install langchain_community
RUN mkdir /opt/supervisor
RUN touch /opt/supervisor/supervisor.sock
RUN touch /opt/supervisor/supervisor.pid


COPY supervisord.conf /etc/supervisor/supervisord.conf
#COPY gunicorn_logging.conf /opt/Tegus/gunicorn_logging.conf
RUN mkdir -p /opt/tegus /opt/logs /opt/tegus/db
COPY app /opt/tegus/app
COPY run.py /opt/tegus/run.py
COPY tegus/chroma/ /opt/tegus/db/chroma/
#COPY tegus/calculation_db/ /opt/tegus/db/calculation_db/
#COPY tegus/truefalse_db/ /opt/tegus/db/truefalse_db/
#COPY tegus/multiple_choise_db/ /opt/tegus/db/multiple_choise_db/



WORKDIR /opt/tegus

CMD ["/usr/bin/supervisord"]
