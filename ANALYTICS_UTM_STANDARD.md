# Analytics UTM Standard

This website uses batch-level campaign attribution only. UTM parameters must never identify a specific professor, email recipient, or individual contact.

## Canonical Example

```text
https://olivia-wr-research.github.io/?utm_source=outreach&utm_medium=email&utm_campaign=phd_2027&utm_content=overseas_scienceofscience_v1
```

## Allowed Values

### `utm_source`

- `outreach`
- `application`
- `organic`
- `github`
- `other`

### `utm_medium`

- `email`
- `cv`
- `application_system`
- `referral`

### `utm_campaign`

- `phd_2027`
- `ra_2026`
- `research_collaboration`

### `utm_content` examples

- `overseas_scienceofscience_v1`
- `overseas_management_v1`
- `overseas_economics_v1`
- `domestic_management_v1`
- `domestic_data_v1`
- `domestic_economics_v1`

## Prohibited Values

Do not use:

- professor names
- professor email addresses
- university-contact-specific tokens
- individual recipient identifiers
- hidden tracking pixels
- one-link-per-professor identifiers

## Interpretation

UTM attribution supports comparison across outreach batches, such as domestic versus overseas, PhD versus RA, or field-specific batches. It cannot show that a particular professor viewed the site.
