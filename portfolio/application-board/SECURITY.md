# Privacy / deployment boundary

- Local storage and exported files are unencrypted. Do not enter passwords, identity documents, referee details or confidential manuscripts.
- Browser profile/origin is the only storage boundary. Shared profiles share data. There is no user authentication, tenant separation or recovery service.
- The Python launcher binds only to loopback, serves an explicit file allowlist and accepts no data writes. Host/cross-site guards and CSP reduce incidental web risks; they are not a hardened security boundary or a security review.
- Imported records are schema/size checked; user text is rendered through DOM text APIs. CSV formula prefixes are escaped. A backup is still untrusted data, not evidence that a vacancy or applicant fact is correct.
- Back up regularly. Malformed stored data disables writes instead of silently replacing it. The app does not provide an in-product repair/reset path in this release; recovery may require technical help and a previously exported backup.
- Do not expose the launcher publicly or represent it as a multi-user server. Cloud hosting, accounts, tenant-isolated storage, secrets, deletion/export rights, abuse controls and security review require a separate design and implementation.

## Local CV processing (0.4)

DOCX/TXT/Markdown are processed in memory, not posted to the launcher or a model. Only reviewed fixed-vocabulary tags are persisted after explicit confirmation. Raw text is cleared after extraction and close. No PDF/OCR fallback upload exists. DOCX XML extraction has size, compression and entity-declaration checks, but is not a complete document parser or a security audit. Avoid confidential content; browser extensions and same-origin scripts remain trusted.
