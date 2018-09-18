FROM pivotaldata/ubuntu-gpdb-dev:16.04_gcc_6_3

RUN apt-get update
# required for `make mkpgbouncer`
RUN apt-get install -y libldap2-dev libtool automake pkg-config

RUN mkdir /root/gpdb/
COPY . /root/gpdb/

WORKDIR /root/gpdb/depends
RUN ./configure
RUN make

RUN git submodule update --init --recursive

RUN mkdir -p /root/gpdb/gpAux/docs/release

ENV BLD_ARCH=ubuntu16_x86_64

WORKDIR /root/gpdb/gpAux
RUN make sync_tools
RUN make dist
