# Static Dashboard

This folder contains a framework-free static dashboard prototype for the Taiwan VTuber Infographics project.

It reads only:

- `data/derived/public-index.json`
- aggregate CSV files under `data/derived/`
- SVG exports under `charts/exports/`

It does not read raw upstream data, names, IDs, URLs as rows, or individual timelines.

Current modules:

- aggregate summary cards
- safe metric switcher
- platform coverage chart
- public status chart
- quarterly ecosystem coverage chart
- source coverage chart
- public output table

Run locally from the repo root:

```bash
python -m http.server 8080
```

Then open:

```text
http://localhost:8080/site/
```

When GitHub Pages is enabled through the included workflow, the public dashboard path is:

```text
https://chiveswang.github.io/taiwan-vtuber-infographics/site/
```
