FROM kalilinux/kali-rolling

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update package lists and install essential tools
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
    # Kali-specific pentesting tools
    kali-tools-top10 \
    nmap \
    metasploit-framework \
    sqlmap \
    john \
    hashcat \
    hydra \
    aircrack-ng \
    wireshark \
    burpsuite \
    nikto \
    gobuster \
    dirb \
    && rm -rf /var/lib/apt/lists/*

# Install ttyd (web-based terminal)
RUN curl -L https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64 \
    -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd

# Create student user with sudo privileges
RUN useradd -m -s /bin/bash student && \
    echo "student:student123" | chpasswd && \
    echo "student ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set up student home directory
RUN mkdir -p /home/student/{projects,downloads,tools,wordlists} && \
    chown -R student:student /home/student

# Create welcome message with Kali tools info
RUN echo '#!/bin/bash' > /home/student/.bashrc && \
    echo 'echo "╔════════════════════════════════════════════════════════════╗"' >> /home/student/.bashrc && \
    echo 'echo "║      Welcome to Selfmade Labs - Kali Linux Environment    ║"' >> /home/student/.bashrc && \
    echo 'echo "╚════════════════════════════════════════════════════════════╝"' >> /home/student/.bashrc && \
    echo 'echo ""' >> /home/student/.bashrc && \
    echo 'echo "📁 Your files are in: /home/student"' >> /home/student/.bashrc && \
    echo 'echo "🔧 Pentesting tools: nmap, metasploit, sqlmap, john, hashcat"' >> /home/student/.bashrc && \
    echo 'echo "🌐 Network tools: hydra, aircrack-ng, wireshark, burpsuite"' >> /home/student/.bashrc && \
    echo 'echo "💾 All files persist across lab sessions!"' >> /home/student/.bashrc && \
    echo 'echo ""' >> /home/student/.bashrc && \
    echo 'echo "💡 Quick start: nmap -sV <target>, msfconsole, sqlmap -u <url>"' >> /home/student/.bashrc && \
    echo 'echo ""' >> /home/student/.bashrc && \
    echo 'PS1="\[\033[01;31m\]\u@kali-linux\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "' >> /home/student/.bashrc && \
    chown student:student /home/student/.bashrc

# Set working directory
WORKDIR /home/student

# Switch to student user
USER student

# Expose ttyd port
EXPOSE 7681

# Start ttyd with bash terminal
CMD ["ttyd", "-p", "7681", "-W", "bash"]
