# Step 3: Frontend — React Dashboard

## Context
This is step 3 of **Financial Monitor**.
- Step 0: CDK infrastructure
- Step 1: Backend shared + bond-spreads services
- Step 2: Lambda handlers

We now build the React frontend. The app is a platform shell with feature modules. The first feature is the **Bond Spreads Dashboard**.

## Task

Build the complete React frontend matching the design in `financial_monitor_design.html` (attached). Match it precisely — typography, colors, spacing, animations, responsive breakpoints.

## Tech Stack
- React 18+ with TypeScript, Vite, TanStack React Query v5
- React Context for theme + UI state
- Plain CSS with CSS variables
- No component library — all custom
- Vitest + React Testing Library

## File Structure

```
frontend/
├── src/
│   ├── shared/                             # Platform-wide shared code
│   │   ├── components/
│   │   │   ├── Header.tsx                  # Platform header (logo, theme toggle, nav)
│   │   │   ├── Footer.tsx                  # Platform footer
│   │   │   ├── ThemeToggle.tsx             # Dark/light switch
│   │   │   ├── LoadingState.tsx            # Skeleton/shimmer loading
│   │   │   └── ErrorState.tsx              # Error with retry button
│   │   ├── context/
│   │   │   └── ThemeContext.tsx             # Dark/light theme provider
│   │   ├── hooks/
│   │   │   └── useMediaQuery.ts            # Responsive breakpoint hook
│   │   ├── styles/
│   │   │   ├── variables.css               # CSS variables (dark + light themes)
│   │   │   ├── global.css                  # Reset, typography, base styles
│   │   │   └── animations.css              # Shared animations (fadeIn, pulse)
│   │   └── utils/
│   │       └── formatting.ts               # Generic formatters (dates, numbers)
│   │
│   ├── features/
│   │   └── bond-spreads/                   # BOND SPREADS feature
│   │       ├── components/
│   │       │   ├── BondSpreadsDashboard.tsx # Feature root — composes all sub-components
│   │       │   ├── StatsRow.tsx             # 4 hero stat cards
│   │       │   ├── FilterBar.tsx            # Search + region tags
│   │       │   ├── SortControls.tsx         # Sort buttons
│   │       │   ├── SpreadTable.tsx          # Desktop table (hidden on mobile)
│   │       │   ├── SpreadCard.tsx           # Single mobile card
│   │       │   ├── SpreadCardList.tsx       # Mobile card list (hidden on desktop)
│   │       │   ├── SpreadBar.tsx            # Zero-centered bar visualization
│   │       │   ├── Sparkline.tsx            # Mini 6-month bar chart
│   │       │   ├── DeltaBadge.tsx           # Change indicator badge
│   │       │   ├── HistoryChart.tsx         # SVG multi-line chart
│   │       │   ├── ChartLegend.tsx          # Chart color legend
│   │       │   ├── InversionAlerts.tsx      # Sidebar: red alert cards
│   │       │   ├── TopMovers.tsx            # Sidebar: ranked movers
│   │       │   └── GlobalSummary.tsx        # Sidebar: key stats
│   │       ├── hooks/
│   │       │   ├── useSpreadData.ts         # /data/bond-spreads/spreads-latest.json
│   │       │   ├── useHistoryData.ts        # /data/bond-spreads/spreads-history.json
│   │       │   └── useSummaryData.ts        # /data/bond-spreads/spreads-summary.json
│   │       ├── context/
│   │       │   └── BondSpreadsUIContext.tsx  # Sort, filter, time period state
│   │       ├── utils/
│   │       │   ├── sorting.ts               # Bond-spread sorting logic
│   │       │   └── filtering.ts             # Region/search filtering
│   │       ├── types/
│   │       │   └── index.ts                 # Bond-spread TypeScript interfaces
│   │       └── styles/
│   │           └── bond-spreads.css         # Feature-specific styles
│   │
│   ├── App.tsx                              # Platform shell + feature routing
│   ├── App.css                              # App-level layout
│   └── main.tsx                             # Entry with providers
│
├── tests/
│   ├── shared/
│   │   └── formatting.test.ts
│   └── features/
│       └── bond-spreads/
│           ├── sorting.test.ts
│           ├── filtering.test.ts
│           ├── SpreadBar.test.tsx
│           ├── DeltaBadge.test.tsx
│           ├── StatsRow.test.tsx
│           └── ThemeContext.test.tsx
├── public/
│   ├── robots.txt
│   └── sitemap.xml
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

## App Architecture

```typescript
// main.tsx
<QueryClientProvider>
  <ThemeProvider>
    <App />
  </ThemeProvider>
</QueryClientProvider>

// App.tsx — for now just renders the bond spreads feature
// Future: add React Router, navigation between features
<div className="app">
  <Header />
  <main>
    <BondSpreadsDashboard />   {/* First feature */}
  </main>
  <Footer />
</div>
```

The `<Header>` is platform-level (shared logo "Financial Monitor", theme toggle). The `<BondSpreadsDashboard>` is the feature root that composes everything inside.

## Shared Components

### Header.tsx
- Logo: "Financial **Monitor**" (Playfair Display, gold accent on "Monitor")
- Logo mark: "F" in gold-bordered square
- Theme toggle (sun/moon icon + track switch)
- Live indicator (green pulsing dot)
- Updated timestamp + date
- On mobile: stacks vertically, hides meta text

### ThemeContext
- `theme: 'dark' | 'light'`, `toggleTheme()`
- Sets `data-theme` on `<html>`, persists to localStorage
- Default: `'dark'`

### CSS Variables (`shared/styles/variables.css`)
Extract ALL CSS variables from the design HTML. Both `:root` (dark) and `[data-theme="light"]` blocks. This is the single source of truth for theming across all features.

## Bond Spreads Feature

### Data Fetching

```typescript
// Note: paths include the feature namespace
const useSpreadData = () => useQuery({
  queryKey: ['bond-spreads', 'latest'],
  queryFn: () => fetch('/data/bond-spreads/spreads-latest.json').then(r => r.json()),
  staleTime: 1000 * 60 * 60,
  gcTime: 1000 * 60 * 60 * 24,
  retry: 3,
});
```

### BondSpreadsUIContext
Feature-local state:
- `sortBy`, `sortDirection`, `regionFilter`, `searchQuery`, `timePeriod`, `selectedCountries`
- Only used within the bond-spreads feature tree

### BondSpreadsDashboard.tsx
The feature root. Wraps everything in `<BondSpreadsUIProvider>` and composes:
```
<BondSpreadsUIProvider>
  <FilterBar />
  <StatsRow />
  <SortControls />
  <SpreadTable />        {/* Desktop */}
  <SpreadCardList />     {/* Mobile */}
  <div className="bottom-grid">
    <HistoryChart />
    <aside>
      <InversionAlerts />
      <TopMovers />
      <GlobalSummary />
    </aside>
  </div>
</BondSpreadsUIProvider>
```

### TypeScript Interfaces (`features/bond-spreads/types/`)
Same as before — `SpreadCountry`, `SpreadLatestResponse`, `HistoryPoint`, `CountryHistory`, `SpreadHistoryResponse`, `InversionEntry`, `MoverEntry`, `SpreadSummaryResponse`, `SortField`, `SortDirection`, `RegionFilter`, `TimePeriod`.

### Component Specs
All same as original spec — SpreadTable, SpreadCard, SpreadBar, Sparkline, HistoryChart, FilterBar, InversionAlerts, TopMovers, GlobalSummary. Refer to the design HTML for exact styling.

### Loading & Error States
- `<LoadingState>` (shared): skeleton shimmer on stat cards and table rows
- `<ErrorState>` (shared): "Data temporarily unavailable" with retry button
- Both are platform components, reused by any feature

## SEO (`index.html`)

```html
<title>Financial Monitor — Government Bond Yield Curve Spreads</title>
<meta name="description" content="Financial data platform. Track government bond yield curve spreads, monitor inversions, and analyze economic signals across major world economies." />
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Financial Monitor",
  "description": "Financial data platform for tracking economic indicators",
  "applicationCategory": "FinanceApplication"
}
</script>
```

## Responsive Design

Extract all `@media` queries from the design HTML:
- **≤1024px**: tablet — 2-col stats, stacked bottom grid
- **≤768px**: mobile — card layout, horizontal scroll tags, stacked everything
- **≤420px**: compact — tighter padding, hide currency codes

## Unit Tests

### Shared
- `formatting.test.ts`: formatDate, formatNumber, formatPercentage

### Bond Spreads Feature
- `sorting.test.ts`: sort by spread/change/name, asc/desc, null handling
- `filtering.test.ts`: G7/G20/Emerging/BRICS/All, search by name/currency
- `SpreadBar.test.tsx`: green right / red left / zero
- `DeltaBadge.test.tsx`: positive green / negative red / null
- `StatsRow.test.tsx`: renders summary values
- `ThemeContext.test.tsx`: toggle, localStorage, data-theme attribute

Run: `cd frontend && npx vitest run`

## Key Design Principle

**Feature isolation**: everything under `features/bond-spreads/` is self-contained. To add a new feature (e.g., currency rates), create `features/currency-rates/` with its own components, hooks, context, types, styles. Shared components and theme stay in `shared/`. No feature imports from another feature.
