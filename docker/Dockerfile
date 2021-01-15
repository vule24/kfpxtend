# ARG IMAGE_TYPE="gpu"
# FROM gcr.io/kubeflow-images-public/tensorflow-2.1.0-notebook-${IMAGE_TYPE}:v-base-1caade5-1228430207824695301
FROM python:3.8

ARG NB_USER=jovyan

# TODO: User should be refactored instead of hard coded jovyan

USER root

RUN apt-get update
RUN apt-get install -y  \
        sudo \
        zsh openssh-server htop \
        ca-certificates tar less \
        tree tmux vim nano


RUN bash -c "curl -fsSL https://code-server.dev/install.sh | sh"

# Install base python3 packages
RUN pip3 uninstall -y enum34
RUN pip3 install --upgrade pip && \
    pip3 install -U \
        jupyterlab==2.2.9 \
        kfp \
        ipywidgets \
        jupyterlab-git \
        jupyter-server-proxy jupyter-vscode-proxy pylint


RUN curl -sL https://deb.nodesource.com/setup_15.x | bash -
RUN apt-get install -y nodejs
# Install Jupyter Lab Extensions
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager --no-build && \
    jupyter labextension install @jupyterlab/toc --no-build && \
    jupyter labextension install @aquirdturtle/collapsible_headings --no-build && \
    jupyter labextension install @jupyterlab/server-proxy --no-build && \
    jupyter lab build && \
    jupyter lab clean && \
    jlpm cache clean && \
    npm cache clean --force && \
    rm -rf $HOME/.node-gyp && \
    rm -rf $HOME/.local 

RUN useradd -rm -d /home/jovyan -s /bin/bash -g root -G sudo -u 1001 jovyan
RUN echo "jovyan ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers.d/jovyan

COPY zshrc /zshrc
COPY tmux.conf /tmux.conf
COPY setup.sh /setup.sh
RUN chown -R ${NB_USER}:users ${HOME}
USER ${NB_USER}
ENV HOME=/home/jovyan
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" --skip-chsh --unattended \
  && git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions \
  && git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting

RUN sudo mv ${HOME}/.oh-my-zsh /
# Configure container startup
WORKDIR ${HOME}
SHELL ["/bin/zsh", "-c"]
ENV SHELL=/bin/zsh
RUN sudo apt-get install tini
ENTRYPOINT ["tini", "--"]
CMD ["zsh","-c", "/setup.sh; \  
    jupyter lab --notebook-dir=${HOME} --ip=0.0.0.0 --no-browser \
        --allow-root --port=8888 --LabApp.token='' --LabApp.password='' \
        --LabApp.allow_origin='*' --LabApp.base_url=${NB_PREFIX}"]
