# Aliases
alias vim="nvim"
alias nr="npm run"
alias nrd="npm run dev"
alias dcdn='docker-compose down'
alias dcup='docker-compose up'
alias docker-compose='docker compose'
alias eep='systemctl suspend'
alias zshrc='code ~/.zshrc'
alias windows='sudo grub-reboot 2 && sudo reboot'
alias magnet='transmission-remote TRANSMISSION_REMOTE_URL --auth :FERALHOSTINGPW -a'

# timer
timer() {
    termdown "$@" && (for i in {1..5}; do play -n synth 0.3 sine 440 gain 5; sleep 0.3; done)
}

# Plugins
plugins=(
  git
  zsh-autosuggestions
  zsh-syntax-highlighting
  autojump
)