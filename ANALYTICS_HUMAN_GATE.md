# Analytics Human Gate

GA4 Measurement ID is not present in the repository or local environment. Do not invent it.

## Create the GA4 Web Data Stream

1. Go to https://analytics.google.com.
2. Create or select the Google Analytics 4 property for Ran Wang's academic website.
3. Create a Web data stream.
4. Use this Website URL exactly:
   `https://olivia-wr-research.github.io`
5. Copy the Measurement ID. It must look like:
   `G-XXXXXXXXXX`

## Where Codex Should Add the ID

After the real Measurement ID is provided, add Quarto native Google Analytics configuration in both site configs:

```yaml
website:
  site-url: "https://olivia-wr-research.github.io"
  google-analytics: "G-XXXXXXXXXX"
```

For the Chinese site, add the same real ID in `zh/_quarto.yml` under `website:` while preserving:

```yaml
site-url: "https://olivia-wr-research.github.io/zh/"
```

Quarto's native `google-analytics` option injects the appropriate Google tag during render. The custom event layer in `assets/js/analytics-events.js` is already prepared and safely no-ops until `gtag` exists.

## Human Gate Status

- GA4 ID found locally: No
- GA4 ID invented: No
- Static event integration prepared: Yes
- Live analytics verification: Pending real GA4 ID and deployed/visited site
