FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install essential tools and ttyd
RUN apt update && apt install -y \
    sudo \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    net-tools \
    iputils-ping \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install ttyd (web-based terminal)
RUN curl -L https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64 \
    -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd

# Create labuser with sudo privileges
RUN useradd -m -s /bin/bash labuser && \
    echo "labuser:labpassword123" | chpasswd && \
    echo "labuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set up labuser home directory
RUN mkdir -p /home/labuser/{projects,downloads} && \
    chown -R labuser:labuser /home/labuser

# Create welcome message
RUN echo '#!/bin/bash' > /home/labuser/.bashrc && \
    echo 'echo "╔════════════════════════════════════════════════════════════╗"' >> /home/labuser/.bashrc && \
    echo 'echo "║        Welcome to Selfmade Labs - Ubuntu Environment      ║"' >> /home/labuser/.bashrc && \
    echo 'echo "╚════════════════════════════════════════════════════════════╝"' >> /home/labuser/.bashrc && \
    echo 'echo ""' >> /home/labuser/.bashrc && \
    echo 'echo "👤 User: $USER (Email: ${USER_EMAIL:-Not Set})"' >> /home/labuser/.bashrc && \
    echo 'echo "📁 Your files are in: /home/labuser"' >> /home/labuser/.bashrc && \
    echo 'echo "🔧 Installed tools: git, python3, node, vim, nano, htop"' >> /home/labuser/.bashrc && \
    echo 'echo "💾 All files persist across lab sessions!"' >> /home/labuser/.bashrc && \
    echo 'echo ""' >> /home/labuser/.bashrc && \
    echo 'PS1="\[\033[01;32m\]\u@selfmade-ubuntu\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "' >> /home/labuser/.bashrc && \
    chown labuser:labuser /home/labuser/.bashrc

# Set working directory
WORKDIR /home/labuser

# Switch to labuser
USER labuser

# Expose ttyd port
EXPOSE 7681

# Start ttyd with bash terminal
# -W flag enables writable mode (allows terminal input)
# -p 7681 sets the port
# bash starts the bash shell
CMD ["ttyd", "-p", "7681", "-W", "bash"]
