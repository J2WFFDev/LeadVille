SSH setup for LeadVille Pi

Purpose
- Provide a short, non-secret runbook for contributors to configure a local SSH alias named `leadville-pi` for consistent access to the Raspberry Pi running the LeadVille bridge. Do NOT commit private keys or passphrases.

Add a local SSH config entry (do not commit)
1. Open `~/.ssh/config` in your editor (create it if it doesn't exist).
2. Add the following block, replacing `HostName` and `User` with your Pi's address and username:

    Host leadville-pi
        HostName 192.168.1.124    # replace with your Pi IP or DNS name
        User pi                  # replace with your Pi username
        IdentityFile ~/.ssh/id_rsa_leadville
        IdentitiesOnly yes

3. Save the file and ensure it has proper permissions:

    chmod 600 ~/.ssh/config

Test connectivity

- Test SSH connection using the alias:

```pwsh
ssh leadville-pi
```

- If you prefer to use the IP directly, substitute `pi@192.168.1.124`.

Copying files to the Pi (example)

- From Windows PowerShell (use your alias or `user@ip`):

```pwsh
scp "C:\path\to\local\file.md" leadville-pi:/home/jrwest/projects/LeadVille/docs/file.md
```

- Or using IP:

```pwsh
scp "C:\path\to\local\file.md" pi@192.168.1.124:/home/jrwest/projects/LeadVille/docs/file.md
```

Verify checksum after copy

- Local SHA256 (PowerShell):

```pwsh
Get-FileHash -Algorithm SHA256 "C:\sandbox\TargetSensor\LeadVille\docs\pi_full_project_inventory.md"
```

- Remote SHA256 via SSH (Linux):

```pwsh
ssh leadville-pi "sha256sum /home/jrwest/projects/LeadVille/docs/pi_full_project_inventory.md"
```

- Compare the two hashes; they should match exactly.

Service and runtime checks (example)

- Restart the bridge service and view recent logs:

```pwsh
ssh leadville-pi "sudo systemctl restart leadville-bridge && sudo journalctl -u leadville-bridge -n 200 --no-pager"
```

- Query the capture DB (shot_log view):

```pwsh
ssh leadville-pi "sqlite3 /home/jrwest/projects/LeadVille/logs/bt50_samples.db 'SELECT * FROM shot_log ORDER BY ts_ns DESC LIMIT 10;'"
```

Security notes

- Never store private keys or passphrases in the repository.
- Use `ssh-agent` or a secure key file with `IdentityFile` and restrictive permissions.
- For CI-based automation, create a machine-specific deploy key and keep it in the CI vault.

If you want, I can add a small `scripts/` helper that prints the local sha256 and copies the file using an alias if present; let me know and I'll implement it.
