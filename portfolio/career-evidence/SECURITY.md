# Privacy and safe operation

This edition has no network client, telemetry, model provider or HTTP server. It reads user-selected local files and writes new local output directories. No credentials are needed.

Run outputs contain extracted source text and potentially sensitive biographies. Keep them private. The bundled example is invented, not a real person's CV. `.gitignore` is a convenience, not a privacy guarantee.

Only parse trusted files on a trusted local machine. The 20 MiB input limit is not a sandbox or protection against malicious PDFs, ZIP expansion, XML attacks or parser vulnerabilities. Do not host the CLI as a public upload service. Review optional parser dependencies before installation.

The hash manifest detects file inconsistencies, not malicious modification of both files and manifest. It is not signed. A consistent digest does not prove a person's identity, source authenticity, career facts, consent or the correctness of review decisions.

No automatic gold promotion or downstream scientific inference is supported. Do not publish real-person outputs merely because the source documents were publicly accessible.
