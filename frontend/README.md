# OnSide Frontend Application

Modern React + TypeScript frontend for the OnSide Competitive Intelligence Platform.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Environment Setup

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Configure your environment variables:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Project Structure

```
src/
├── components/          # React components
│   └── ProgressTracker/ # Progress tracking UI
├── hooks/              # Custom React hooks
│   └── useProgressTracking.ts
├── api/                # API client (future)
├── utils/              # Utility functions (future)
└── types/              # TypeScript types (future)
```

## Available Components

### ReportProgressTracker

Real-time WebSocket-based progress tracking for report generation.

```tsx
import { ReportProgressTracker } from '@components/ProgressTracker';

<ReportProgressTracker
  reportId={123}
  userId={1}
  onComplete={() => console.log('Done!')}
  onError={(error) => console.error(error)}
  showStages={true}
  showTimeEstimate={true}
  allowCancel={true}
/>
```

### useProgressTracking Hook

Custom hook for WebSocket progress tracking.

```tsx
import { useProgressTracking } from '@hooks/useProgressTracking';

const {
  progressData,
  isConnected,
  connect,
  disconnect,
  cancelReport
} = useProgressTracking({
  reportId: 123,
  userId: 1,
  onComplete: handleComplete,
  onError: handleError
});
```

## Development

### Code Quality

```bash
# Run linter
npm run lint

# Format code
npm run format

# Type check
npm run type-check
```

### Technology Stack

- **React 18.2** - UI framework
- **TypeScript 5.3** - Type safety
- **Vite 5.0** - Build tool
- **React Router 6** - Routing
- **React Query** - Server state
- **Zustand** - Client state
- **Recharts** - Data visualization

## Features

### Implemented ✅

- WebSocket progress tracking
- Real-time updates
- Multi-stage process visualization
- Progress bars and indicators
- Responsive design
- Accessibility (WCAG 2.1 AA)
- Dark mode support
- TypeScript strict mode

### Coming Soon 🚧

- Authentication UI
- Dashboard layout
- Competitor management
- SEO analytics dashboard
- Reports visualization
- Settings pages

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- WebSocket support required

## Contributing

1. Follow TypeScript strict mode
2. Write accessible components (ARIA labels, semantic HTML)
3. Include CSS for responsive design
4. Add JSDoc comments for public APIs
5. Test on multiple browsers

## License

Private - OnSide Platform
