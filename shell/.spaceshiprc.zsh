# Show the time on the right.
SPACESHIP_TIME_SHOW=true
spaceship remove time
SPACESHIP_RPROMPT_ORDER=(time)

# Keep user and host together, then show the current directory.
spaceship remove dir
spaceship add --after host dir

# Show user and host on every machine; report failed commands.
SPACESHIP_USER_SHOW=always
SPACESHIP_HOST_SHOW=always
SPACESHIP_EXIT_CODE_SHOW=true
