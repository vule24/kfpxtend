ARG IMAGE_TYPE="gpu"
FROM gcr.io/kubeflow-images-public/tensorflow-2.1.0-notebook-${IMAGE_TYPE}:v-base-1caade5-1228430207824695301

ARG NB_USER=jovyan

# TODO: User should be refactored instead of hard coded jovyan

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        zsh openssh-server htop \
        ca-certificates tar less \
        python-pip python-setuptools build-essential python-dev \
        python3-pip python3-wheel && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install code-server
RUN bash -c "curl -fsSL https://code-server.dev/install.sh | sh"

# Install base python3 packages
RUN pip3 install --upgrade pip && \
    pip3 install --upgrade jupyterlab && \
    pip3 install https://storage.googleapis.com/ml-pipeline/release/latest/kfp.tar.gz --upgrade && \
    pip3 install -U \
        easykubeflow \
        ipywidgets \
        jupyter-server-proxy jupyter-vscode-proxy pylint\
        kafka-python confluent-kafka \
        elasticsearch \
        
RUN pip3 uninstall -y enum34
RUN pip3 install --upgrade elyra

# Install Jupyter Lab Extensions
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager --no-build && \
    jupyter labextension install @aquirdturtle/collapsible_headings --no-build && \
    jupyter labextension install @jupyterlab/server-proxy --no-build && \
    jupyter lab build && \
        jupyter lab clean && \
        jlpm cache clean && \
        npm cache clean --force && \
        rm -rf $HOME/.node-gyp && \
        rm -rf $HOME/.local 

RUN echo "jovyan ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers.d/jovyan

COPY zshrc /zshrc
COPY tmux.conf /tmux.conf
RUN chown -R ${NB_USER}:users ${HOME}
USER ${NB_USER}
RUN sudo apt-get update && sudo apt-get install -y tmux
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" --skip-chsh --unattended \
  && git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions \
  && git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting

RUN sudo mv ${HOME}/.oh-my-zsh /
# Configure container startup
WORKDIR ${HOME}
SHELL ["/bin/zsh", "-c"]
ENV SHELL=/bin/zsh
ENTRYPOINT ["tini", "--"]
CMD ["zsh","-c", "sudo rm .zshrc .tmux.conf && \
        sudo rm -rf .oh-my-zsh && \
        sudo mv /zshrc ${HOME}/.zshrc && sudo mv /tmux.conf ${HOME}/.tmux.conf && \
        sudo mv /.oh-my-zsh ${HOME}/ && \
        sudo chown ${NB_USER}:users ${HOME}/.zshrc && sudo chown ${NB_USER}:users ${HOME}/.tmux.conf && \
        jupyter lab --notebook-dir=${HOME} --ip=0.0.0.0 --no-browser \
            --allow-root --port=8888 --LabApp.token='' --LabApp.password='' \
            --LabApp.allow_origin='*' --LabApp.base_url=${NB_PREFIX}"]
