# Privacy and report security

Search sends a public topic and year filters to OpenAlex. Do not use unpublished research questions or personal identifiers. API credentials are read from the environment and sent only as an authorization header. Errors do not include raw request objects, credentials or provider response bodies.

Reports embed retrieved public metadata, including public author names and publication affiliations. They do not contain the project owner's profile, email, private research or papers. Researcher identity and employment are not verified. Runtime reports and review notes may be confidential for their users and should remain local unless separately reviewed.

Reports load no external scripts, fonts, analytics or images. Provider text is HTML-escaped and embedded JSON escapes angle brackets. Outgoing links permit HTTPS only and use `noopener noreferrer`. CSV formula prefixes are escaped. Imported review decisions must match the report snapshot hash.

Before publishing changes, inspect the staged diff, repository history and newly added examples. Do not upload `runs/`, browser state, API credentials or original private workspaces. Report security concerns privately to the repository owner without posting secrets in a public issue.
