# GitHub Repository Explorer Template

A modern, responsive React application template built with TypeScript, featuring beautiful animations and a clean UI. This template demonstrates how to build a GitHub repository explorer with real-time data fetching, smooth animations, and a beautiful user interface.

## 🌟 Features

- **Modern Tech Stack**:
  - React with TypeScript
  - Vite for fast development
  - TanStack Query for data fetching
  - Framer Motion for animations
  - DaisyUI & Tailwind CSS for styling
  - GitHub API integration
  - usehooks-ts for custom hooks

- **Beautiful UI Components**:
  - Responsive navigation with mobile menu
  - Animated cards and transitions
  - Persistent Dark/Light theme switcher with smooth transitions
  - Loading animations
  - Search functionality
  - Statistics dashboard

- **Developer Experience**:
  - TypeScript for type safety
  - Modern project structure
  - Reusable components
  - Custom hooks
  - API service layer

## 🚀 Getting Started

### Prerequisites

- Node.js (v14 or higher)
- Yarn or npm

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd <your-repo-name>
```

2. Install dependencies:
```bash
yarn install
# or
npm install
```

3. Start the development server:
```bash
yarn dev
# or
npm run dev
```

## 📁 Project Structure

```
src/
├── components/         # Reusable UI components
│   ├── LoadingSpinner.tsx
│   └── WebsiteCard.tsx
├── pages/             # Page components
│   ├── Dashboard.tsx
│   ├── WebsiteList.tsx
│   └── AddWebsite.tsx
├── services/          # API and service layer
│   └── api.ts
├── hooks/             # Custom React hooks
│   ├── useWebsites.ts
│   └── useTheme.ts    # Theme management hook
├── types/             # TypeScript type definitions
│   └── website.ts
└── App.tsx           # Main application component
```

## 🎨 Styling and Theming

The project uses a combination of Tailwind CSS and DaisyUI for styling:

- **Tailwind CSS**: Utility-first CSS framework
- **DaisyUI**: Component library with theme support
- **Custom theme configuration** in `tailwind.config.js`
- **Persistent theme storage** using `usehooks-ts`

### Theme System

The theme system includes:
- Light and dark mode support
- Smooth transitions between themes
- Persistent theme selection
- Animated theme toggle button

Example of theme usage:

```typescript
import { useTheme } from './hooks/useTheme';

function Component() {
  const { theme, toggleTheme } = useTheme();
  
  return (
    <button onClick={toggleTheme}>
      Current theme: {theme}
    </button>
  );
}
```

### Theme Customization

You can customize both light and dark themes in `tailwind.config.js`:

```javascript
daisyui: {
  themes: [
    {
      light: {
        primary: "#1976d2",
        "base-100": "#ffffff",
        // Add more customizations
      },
      dark: {
        primary: "#42a5f5",
        "base-100": "#1a1b1e",
        // Add more customizations
      },
    },
  ],
}
```

## 🎬 Animations

The project uses Framer Motion for animations:

- Page transitions
- Card hover effects
- Loading animations
- Staggered list animations
- Theme toggle animations

Example of animation usage:

```typescript
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3 }}
  whileHover={{ scale: 1.02 }}
>
  {/* Your content */}
</motion.div>
```

## 🔄 Data Fetching

Data fetching is handled using TanStack Query (React Query) with custom hooks:

- Automatic caching
- Loading states
- Error handling
- Real-time updates

Example usage:

```typescript
const { websites, isLoading, error } = useWebsites();
```

## 📱 Responsive Design

The template is fully responsive with breakpoints:
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

## 🛠 Customization

### API Integration

To change the API integration, modify `services/api.ts`. Currently configured for GitHub API, but can be adapted for any REST API.

### Adding New Pages

1. Create a new page component in `src/pages/`
2. Add the route in `App.tsx`
3. Update the navigation in `App.tsx`

### Adding New Components

1. Create component in `src/components/`
2. Use Framer Motion for animations
3. Style with Tailwind CSS and DaisyUI classes

## 🔧 Available Scripts

- `yarn dev`: Start development server
- `yarn build`: Build for production
- `yarn preview`: Preview production build
- `yarn lint`: Run ESLint

## 📚 Key Dependencies

- `react`: ^18.3.1
- `react-router-dom`: ^7.1.1
- `@tanstack/react-query`: ^5.64.0
- `framer-motion`: ^11.17.0
- `daisyui`: ^4.12.23
- `tailwindcss`: ^3.4.17
- `@octokit/rest`: ^21.1.0
- `usehooks-ts`: ^3.1.0

## 🤝 Contributing

Feel free to contribute to this template by:
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- React Team
- Framer Motion
- DaisyUI
- TanStack Query
- GitHub API
- usehooks-ts
