# NextGen Provider Intelligence Dashboard - Installation

## Prerequisites

- Node.js >= 18.x (recommended: 20.x or later)
- npm >= 9.x

## Quick Install

```bash
cd dashboard
npm install
```

This installs all packages from `package.json` automatically.

## Run Development Server

```bash
npm run dev
```

Open http://localhost:3000

## Build for Production

```bash
npm run build
npm start
```

## All Dependencies

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| next | 16.2.3 | React framework (App Router) |
| react | 19.2.4 | UI library |
| react-dom | 19.2.4 | React DOM renderer |
| deck.gl | ^9.2.11 | WebGL map visualization |
| @deck.gl/core | ^9.2.11 | deck.gl core engine |
| @deck.gl/layers | ^9.2.11 | ScatterplotLayer, ArcLayer |
| @deck.gl/aggregation-layers | ^9.2.11 | HeatmapLayer, HexagonLayer |
| @deck.gl/react | ^9.2.11 | React bindings for deck.gl |
| @deck.gl/mapbox | ^9.2.11 | Mapbox/MapLibre integration |
| maplibre-gl | ^5.22.0 | Open-source map renderer |
| react-map-gl | ^8.1.1 | React wrapper for MapLibre |
| plotly.js-dist-min | ^3.5.0 | Charting library (minified) |
| react-plotly.js | ^2.6.0 | React wrapper for Plotly |

### Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| typescript | ^5 | TypeScript compiler |
| tailwindcss | ^4 | Utility-first CSS framework |
| @tailwindcss/postcss | ^4 | Tailwind PostCSS plugin |
| eslint | ^9 | Linter |
| eslint-config-next | 16.2.3 | Next.js ESLint rules |
| @types/node | ^20 | Node.js type definitions |
| @types/react | ^19 | React type definitions |
| @types/react-dom | ^19 | React DOM type definitions |
| @types/react-plotly.js | ^2.6.4 | Plotly React type definitions |

## Manual Install (if needed)

```bash
npm install next@16.2.3 react@19.2.4 react-dom@19.2.4
npm install deck.gl @deck.gl/core @deck.gl/layers @deck.gl/aggregation-layers @deck.gl/react @deck.gl/mapbox
npm install maplibre-gl react-map-gl
npm install plotly.js-dist-min react-plotly.js
npm install -D typescript tailwindcss @tailwindcss/postcss eslint eslint-config-next
npm install -D @types/node @types/react @types/react-dom @types/react-plotly.js
```
