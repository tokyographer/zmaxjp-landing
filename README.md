# Z-MAX Landing — Quote Request

A self-contained, single-file landing page for **Z-MAX** custom thermoelectric (Peltier) coolers, with a quote-request call to action. The entire page — markup, styles, and scripts — ships in one `quote-request.html` file, so it can be opened directly in a browser or dropped onto any static host.

## Contents

- `quote-request.html` — the complete landing page (no build step, no dependencies)

## Usage

Open the file locally:

```bash
open quote-request.html
```

Or serve it with any static server:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000/quote-request.html
```

## Deployment

Being a single static HTML file, it deploys anywhere that serves static assets — Vercel, Netlify, GitHub Pages, or an S3/CDN bucket. No environment variables or backend are required.

For GitHub Pages, rename or copy the file to `index.html` (or configure your host to serve `quote-request.html` as the entry point).

## License

See [LICENSE](LICENSE).
