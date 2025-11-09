## Description

## Project Structure

```
src/
├── app/
│   ├── layout/        # Layout
│   ├── pages/         # Page components and routing
│   ├── styles/        # Global styles and theme
│   ├── App.tsx        # Root component
│   ├── index.tsx      # Entry point
│   └── router.tsx     # Router configuration
├── assets/            # Static assets (images, fonts, etc.)
│   ├── fonts/         # Config fonts for project
│   └── images/        # Config images for project
├── services/          # API services and external integrations
└── shared/            # Shared modules and utilities
    ├── components/    # Reusable UI components
    ├── constants/     # Application constants
    ├── contexts/      # Global context for project (ex: themeContext, langueContext,loadingContext..)
    ├── services/      # Common service for project (ex: StorageService, Config Interceptor for request and response)
    ├── hooks/         # Common hooks for project (ex: useDarkMode, useLoading,...)
    ├── types/         # TypeScript type definitions
    └── utils/         # Utility functions
```

## Prerequisites

- Node.js (Version 18 or higher)
- npm or yarn

### HTTP Client

- Axios 1.7.9

## Installation

1. Clone the repository

```bash
git clone [repository-url]
```

2. Install dependencies

```bash
npm install
# or
yarn install
```

3. Start development server

```bash
npm run dev
# or
yarn dev
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run prod` - Start production server
- `npm run build` - Build for development

## Technology Stack

### Core

- React 18.3.1
- TypeScript 5.6.2
- Vite 6.0.5

### State Management & Routing

- React Router DOM 7.1.5

### UI components

- antd 5.24.2

### Styling

- TailwindCSS 3.4.17
- PostCSS 8.5.1
- Autoprefixer 10.4.20

### Form Handling & Validation

- React Hook Form 7.55.0

### Development Tools

- ESLint 9.17.0
- Prettier 3.4.2
- TypeScript ESLint 8.18.2
- Various ESLint plugins and configurations

## Architecture Overview

This project follows a modular architecture with clear separation of concerns:

- **app/**: Contains application-specific code and configuration
- **shared/**: Houses reusable modules and utilities
- **components/**: Reusable UI components following atomic design principles
- **services/**: API integrations and external service handlers
- **hooks/**: Custom React hooks for shared logic
- **utils/**: Helper functions and utilities
