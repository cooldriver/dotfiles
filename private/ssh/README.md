# Encrypted SSH configuration

This directory is not a Stow package. Only `config.private.age` (age ciphertext) and `recipients.txt` (public age recipients) belong here, besides this guide. Neither file is created until the owner initializes the real configuration. See [the SSH workflow](../../docs/ssh.md).

Never store a decrypted SSH configuration, SSH public-key inventory, age private identity, or SSH private key here. The public repository still reveals the existence, size, and update history of the encrypted file.
