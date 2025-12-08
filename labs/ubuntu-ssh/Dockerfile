FROM ubuntu:22.04

RUN apt update && \
    apt install -y openssh-server sudo && \
    mkdir /var/run/sshd

RUN useradd -m student && echo "student:student123" | chpasswd
RUN echo "student ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
