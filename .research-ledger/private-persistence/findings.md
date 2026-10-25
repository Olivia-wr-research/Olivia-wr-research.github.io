# Findings — 2026-10-25 Asia/Shanghai

- PR #9 open/draft, head 82311772328ab380636fdeb7719fc41291ba8176; PR #10 open/draft, head 446421e863fb946dda552af3cdb27f048ca595f0. GitHub connector reads verified these heads.
- Run 40120830584 downloaded predecessor checkpoint but decryption failed; run 40142890984 stopped at explicit owner authorization. Neither executed source checks.
- Artifact 12557829387: terrafar-full-census-40088463064-1, 311886 bytes, not expired, expires 2027-01-22T11:05:05Z. This is metadata, not proof of successful decryption. Current reviewed migration binds its ciphertext and certificate hashes.
- Current source authority uses 90-day Actions artifacts; review authority uses an encrypted public terrafar-review branch not yet created. Public artifacts are repository-readable, not owner-only.
- STATUS.md says the separate historical 160-record reconstruction requires rechecks and has no user sampling approval. It cannot substitute for the latest encrypted ledger.
- Existing CMS encryption is RSA recipient wrapping + AES-256-CBC. It supplies confidentiality, not a sender signature. Integrity/authenticity depend on version-pinned trusted storage and IAM; owner/admin rollback remains outside the code threat model.
- New transport keeps unchanged evidence object references and checks registry equality, candidate histories, journal monotonicity and historical files. Limits fail closed; workload/size testing remains a production gate.

Primary documentation is linked in maintenance/terrafar-source-audit/private-storage/README.md. No keys or detailed live records were read or uploaded.
