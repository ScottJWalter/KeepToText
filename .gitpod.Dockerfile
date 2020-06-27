FROM gitpod/workspace-mongodb

# Install custom tools, runtimes, etc.
# For example "bastet", a command-line tetris clone:
# RUN brew install bastet
#
# More information: https://www.gitpod.io/docs/config-docker/

RUN sudo apt-get update \
 && sudo apt-get full-upgrade -y \
 && sudo apt-get install -y \
    python3-lxml \
 && sudo rm -rf /var/lib/apt/lists/*
