# Client compatibility and public-edition scope

Checked against official documentation on 2026-10-15:

- [Repo-local skills](https://learn.chatgpt.com/docs/build-skills): repository skills are discovered under `.agents/skills` from the current working directory toward the repository root.
- [Custom subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): project agent TOML files use `name`, `description` and `developer_instructions`. Permissions are inherited from the parent; role-level `sandbox_mode` does not override them.
- [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference): parent/user settings control concurrency and other runtime choices.

Open the **workbench subfolder**, not just the parent portfolio repository, in a compatible client. Keep the full toolkit together: its skills refer to shared root-level `references/`, `scripts/` and templates. Each SKILL.md now makes that path scope explicit. Do not install a single nested skill folder without its shared resources.

The public edition removes misleading role-level sandbox settings and leaves model, approval and concurrency settings inherited. It adds safe project creation, stricter CSV checks and isolated offline regression tests. It does not install anything into a user's global skill directory, connect providers, run live literature searches or make paid model calls.

The local tests validate files, script behavior and synthetic negative cases. They do not establish end-to-end custom-agent discovery or model behavior in every client version. No live scientific review or model-based quality benchmark was performed for this release.
