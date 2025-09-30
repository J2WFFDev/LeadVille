Use this file to provide workspace-specific custom instructions to Copilot for the LeadVille project.

Checklist
- [x] Verify that the `copilot-instructions.md` file exists in `.github/`.
- [x] Clarify project requirements (LeadVille Impact Bridge - BLE-based impact detection bridge).
- [x] Scaffold and document the project structure and common tasks.
- [x] Keep this file focused: minimal instructions for contributors and CI.

Important notes for contributors
- Pi is the single source of authority for deployed runtime and logs: treat the Pi host as the authoritative system when investigating issues, running background services, or performing database inspections.
- Do not hardcode credentials or secrets. Use SSH keys and the Pi's local user accounts.

Connecting to the Pi
- Prefer using SSH with an entry in your `~/.ssh/config` or a workspace SSH config (example below). Use the username and host that match your environment (do not publish credentials).

Example `~/.ssh/config` entry:

    Host leadville-pi
        HostName pitts
        User Rpi
        IdentityFile ~/.ssh/id_rsa_leadville

Then connect with: `ssh rpi` or use VS Code Remote-SSH `rpi` host.

If you must connect with a raw command: `ssh <user>@<pi-host-or-ip>` (replace `<user>` and `<pi-host-or-ip>` appropriately).

Preferred SSH alias (recommended)
--
To make it easier for contributors and automated agents, we recommend adding a local SSH config entry on your machine using the alias `leadville-pi`. This alias standardizes how people and agents connect to the Pi without committing secrets into the repo.

Example `~/.ssh/config` entry to add locally (do NOT commit this file):

    Host leadville-pi
        HostName pitts     # <replace-with-your-pi-hostname-or-ip>
        User rpi                   # <replace-with-your-pi-user>
        IdentityFile ~/.ssh/id_rsa_leadville
        IdentitiesOnly yes

After you add this, connect with: `ssh leadville-pi`

Notes on usage by contributors and agents
- Do NOT commit private keys, passphrases, or the `~/.ssh/config` file to the repository. The alias is for local convenience only.
- Agents and automation that run in CI or from trusted workstations can use the `leadville-pi` alias; if your environment uses a different alias or user, tell the agent which alias to use.
- If an agent tries `ssh leadville-pi` and the host is unresolved, it's because your local `~/.ssh/config` doesn't contain the entry shown above. Add it locally or provide `user@ip` when asked.

Where to document your Pi address for the team
- If you want a non-secret, team-visible place to record the preferred alias and the placeholder HostName (without credentials), add it to `docs/ssh_setup.md` or to your private ops vault. The repo intentionally shouldn't contain private keys.

Housekeeping guidance (do not add noisy scripts to project root)
- Keep the repository root small: move ad-hoc scripts and one-off experiments into `misc/` or `archive/` with accompanying README entries.
- Avoid committing local or temporary debugging files. Use `.gitignore` for runtime-generated files.

When using Copilot within this workspace
- Prefer suggestions that reference existing modules under `src/`.
- Avoid introducing large new dependencies without adding them to `pyproject.toml` / `requirements.txt` and tests.

Maintenance checklist (short)
- Keep `README.md` up to date with quick start and deployment steps.
- Keep `docs/` or `archive/` for one-off analysis, and document why a file was archived in `archive/ARCHIVE_LIST.md`.

If you need to update these instructions, keep changes minimal and focused on developer ergonomics.