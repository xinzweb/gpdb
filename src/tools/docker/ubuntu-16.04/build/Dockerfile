FROM pivotaldata/ubuntu-gpdb-dev:16.04_gcc_6_3

RUN mkdir /root/gpdb/
COPY . /root/gpdb/

ENV BLD_ARCH=ubuntu16_x86_64

WORKDIR /root/gpdb/gpAux
RUN make sync_tools
RUN make dist
