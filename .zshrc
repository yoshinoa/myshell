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
alias magnet='function _magnet() { transmission-remote https://XXXXXX.feralhosting.com:443/USERNAME/transmission/rpc --auth :FERALHOSTINGPW -a "$(xclip -o -selection clipboard)" && track-magnet "$(xclip -o -selection clipboard)" & }; _magnet'
alias torrent='tordl'
alias anime='ani-cli'

# extra stuff
timer() {
    termdown "$@" && (for i in {1..5}; do play -n synth 0.3 sine 440 gain 5 2>/dev/null; sleep 0.3; done)
}

# Plugins
plugins=(
  git
  zsh-autosuggestions
  zsh-syntax-highlighting
  autojump
)