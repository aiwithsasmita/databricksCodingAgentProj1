# NextGen Provider Intelligence Dashboard v2 — Offline US Map Solution

## Problem Statement

The NextGen Provider Intelligence Dashboard uses a WebGL-based map to visualize provider behavior across the United States. In the original implementation (v1), the map relied on **MapLibre GL** (via `react-map-gl/maplibre`) to render the US basemap. At runtime, MapLibre fetches basemap tiles from an external CDN:

```
https://basemaps.cartocdn.com/gl/positron-gl-style/style.json
```

This style JSON in turn loads **vector tile images** from Carto's servers on every page load.

### Why It Broke on the Server

On the Linux deployment server, **outbound requests to Carto/Mapbox CDNs are blocked** by the network firewall/proxy. As a result:

- The basemap rendered as a **blank canvas**
- Data layers (scatter bubbles, heatmap, hexagons) had **no map underneath**
- The application was functionally unusable for geographic analysis

### Packages Causing External Dependency

| Package | Role | Problem |
|---------|------|---------|
| `maplibre-gl` | Tile renderer | Fetches vector tiles from Carto CDN at runtime |
| `react-map-gl` | React wrapper | Hosts the MapLibre GL instance |
| `@deck.gl/mapbox` | Integration bridge | Bridges deck.gl layers with MapLibre basemap |

---

## Solution: Self-Contained US Map with Bundled GeoJSON

Replaced the external tile-based basemap with a **fully self-contained US map** that is bundled directly into the JavaScript at build time. **Zero network requests** are made at runtime for map data.

### What Was Done

#### 1. Bundled US State Boundaries Locally

Downloaded `us-states-topo.json` (US Census Bureau state boundaries via the [us-atlas](https://github.com/topojson/us-atlas) project, ~115KB) into `src/data/`. This file becomes part of the source code and gets bundled by Next.js during `npm run build`.

The TopoJSON file contains two geometry objects:
- **`states`** — boundaries for all 50 US states + DC
- **`nation`** — the outer national boundary

#### 2. Added TopoJSON Conversion Library

Added `topojson-client` (~15KB) as a runtime dependency. This converts the compact TopoJSON format into GeoJSON that deck.gl can render. The conversion happens once at module load time:

```typescript
import { feature } from "topojson-client";
import usTopology from "@/data/us-states-topo.json";

const usStatesGeoJson = feature(usTopology, usTopology.objects.states);
const usNationGeoJson = feature(usTopology, usTopology.objects.nation);
```

#### 3. Rewrote MapView.tsx

Removed the MapLibre `<Map>` component and replaced it with two deck.gl `GeoJsonLayer`s:

| Layer | Purpose | Visual |
|-------|---------|--------|
| `us-nation-fill` | Fills the land mass | Light gray `[243, 244, 246]` |
| `us-states-borders` | Draws state boundary lines | Gray `[189, 195, 207]`, 1-2px |

The container div background is set to `#dce4ed` (blue-gray), which acts as the ocean color.

**Before (v1):**
```tsx
<DeckGL viewState={...} layers={dataLayers} ...>
  <Map mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json" />
</DeckGL>
```

**After (v2):**
```tsx
<DeckGL viewState={...} layers={[geoJsonBaseLayers, ...dataLayers]} .../>
```

No child `<Map>` component. No external URL. No CDN dependency.

#### 4. Removed External Map Dependencies

```diff
  "dependencies": {
-   "@deck.gl/mapbox": "^9.2.11",
-   "maplibre-gl": "^5.22.0",
-   "react-map-gl": "^8.1.1",
+   "topojson-client": "^3.1.0"
  }
```

#### 5. Cleaned Up CSS

Removed `.maplibregl-canvas`, `.maplibregl-ctrl-logo`, and `.maplibregl-ctrl-attrib` CSS rules from `globals.css` that were specific to the removed MapLibre library.

---

### What Stayed the Same

All existing functionality is preserved identically:

- **Scatter mode** — colored/sized bubbles by org type and selected metric
- **Heatmap mode** — density visualization weighted by payment or bed count
- **3D Hexagon mode** — extruded hexbins with lighting effects
- **Hover tooltips** — provider name, type, billing pattern, efficiency, claims, payment
- **Pan/zoom** — clamped to US bounds (lat 18–72, lng -170 to -60, zoom 2.5–12)
- **NPI Search** — highlighted provider with similar provider matching
- **Filter bar** — specialty, billing pattern, state, org type filters
- **Data table** — paginated provider list with sorting

---

## Why This Is Guaranteed to Work

| Aspect | Before (v1) | After (v2) |
|--------|-------------|------------|
| Basemap source | Carto CDN (runtime fetch) | Bundled in JS (build time) |
| Runtime network for map | Required | Not needed |
| Map data size | ~MB of tiles per session | 115KB one-time in bundle |
| External packages | maplibre-gl, react-map-gl, @deck.gl/mapbox | topojson-client (15KB) |
| Server requirement | Outbound HTTPS to cartocdn.com | None after `npm run build` |

The **only network access** needed is during `npm install` (to download packages from the npm registry — which the server already does for React, Next.js, deck.gl, etc.). After `npm run build`, the entire application is **completely self-contained**.

---

## File Structure (v2)

```
NextGen_Provider_Intelligence_Dashboard_v2/
├── src/
│   ├── app/
│   │   ├── globals.css          # Cleaned up (no maplibre styles)
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── MapView.tsx          # Rewritten - GeoJsonLayer basemap
│   │   ├── FilterBar.tsx
│   │   ├── HospitalTable.tsx
│   │   ├── NpiSearch.tsx        # Fixed type compatibility
│   │   └── ProviderUniverse.tsx # Fixed Plotly type errors
│   ├── data/
│   │   └── us-states-topo.json  # Bundled US state boundaries
│   └── lib/
│       ├── colors.ts
│       ├── dummy-data.ts
│       ├── filters.ts
│       ├── similarity.ts
│       └── types.ts
├── public/
├── package.json                 # Updated dependencies
├── tsconfig.json
├── next.config.ts
└── SKILLED.md                   # This file
```

---

## Deployment Instructions

```bash
# Install dependencies (requires npm registry access — one time)
npm install

# Build the production bundle (map data baked into JS)
npm run build

# Start the server (zero external requests for map)
npm start
```

No environment variables, API keys, or CDN access required for the map to render.
