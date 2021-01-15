#!/bin/bash
if [[ -f ${HOME}/.zshrc ]] ; then
    echo '.zshrc exists'
else
    sudo mv /zshrc ${HOME}/.zshrc 
    sudo chown ${NB_USER}:users ${HOME}/.zshrc 
    echo 'Moved .zshrc' 
fi

if [[ -f ${HOME}/.tmux.conf ]] ; then 
    echo '.tmux.conf exists'
else 
    sudo mv /tmux.conf ${HOME}/.tmux.conf 
    sudo chown ${NB_USER}:users ${HOME}/.tmux.conf 
    echo 'Moved .tmux.conf'
fi
if [[ -d ${HOME}/.oh-my-zsh ]] ; then 
    echo '.oh-my-zsh exists'
else 
    sudo mv /.oh-my-zsh ${HOME}/ 
    sudo chown -R ${NB_USER}:users ${HOME}/.oh-my-zsh 
    echo 'Moved .oh-my-zsh'
fi