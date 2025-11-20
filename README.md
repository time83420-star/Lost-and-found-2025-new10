# AI-Powered Lost & Found System - Frontend

Complete React + TypeScript frontend for NIT Kurukshetra's Lost & Found System.

## Tech Stack

- React 18 + TypeScript
- Vite
- Tailwind CSS
- React Router v6
- Axios
- Context API
- Lucide Icons

## Features

### Authentication
- Register with NIT email validation (@nitkkr.ac.in)
- Login/Logout with JWT token persistence
- Protected routes
- Auth context management

### Core Pages
- **Home**: Landing page with hero section and feature overview
- **Browse Items**: Grid view with filters (category, location, type)
- **Search**: Semantic search functionality for AI-powered matching
- **Item Details**: Full item information with contact owner button
- **Upload Item**: Report lost/found items with image upload
- **Dashboard**: Manage uploaded items, update status
- **Messages**: Real-time chat interface for communication
- **Admin Panel**: Manage all items and reports

### Components Structure

```
src/
├── components/
│   ├── Auth/
│   │   └── ProtectedRoute.tsx
│   ├── Items/
│   │   └── ItemCard.tsx
│   ├── Search/
│   │   └── FilterPanel.tsx
│   ├── Messaging/
│   │   ├── ChatList.tsx
│   │   └── ChatWindow.tsx
│   └── Layout/
│       ├── Layout.tsx
│       ├── Navbar.tsx
│       └── Toast.tsx
├── pages/
│   ├── Home.tsx
│   ├── Login.tsx
│   ├── Register.tsx
│   ├── BrowseItems.tsx
│   ├── ItemDetails.tsx
│   ├── UploadItem.tsx
│   ├── Dashboard.tsx
│   ├── Messages.tsx
│   └── AdminPanel.tsx
├── context/
│   ├── AuthContext.tsx
│   └── ToastContext.tsx
├── utils/
│   └── api.ts
├── App.tsx
└── main.tsx
```

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
VITE_API_URL=http://localhost:5000/api
```

### 3. Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### 4. Build for Production

```bash
npm run build
```

### 5. Preview Production Build

```bash
npm run preview
```

## API Integration

The frontend expects the following backend endpoints:

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user

### Items
- `GET /items` - Get all items (with filters)
- `GET /items/:id` - Get item details
- `POST /items` - Create new item
- `PATCH /items/:id/status` - Update item status
- `DELETE /items/:id` - Delete item
- `POST /items/search` - Semantic search
- `GET /items/my-items` - Get user's items

### Messages
- `GET /messages/conversations` - Get all conversations
- `GET /messages/conversation/:id` - Get messages
- `POST /messages/conversation/:id` - Send message
- `POST /messages` - Start new conversation

### Admin
- `GET /admin/items` - Get all items
- `DELETE /admin/items/:id` - Delete any item

### Upload
- `POST /upload` - Upload image (multipart/form-data)

## Key Features

### JWT Authentication
- Token stored in localStorage
- Axios interceptor adds token to all requests
- Auto-redirect on 401 errors

### Protected Routes
- User authentication required
- Admin-only routes
- Loading states

### Toast Notifications
- Success/Error/Info messages
- Auto-dismiss after 3 seconds
- Smooth animations

### Responsive Design
- Mobile-first approach
- Breakpoints: sm, md, lg
- Touch-friendly interfaces

### Image Upload
- Preview before upload
- File size validation
- Cloudinary integration ready

### Real-time Messaging
- Conversation list
- Chat window with message history
- Unread message badges

## Folder Organization

All components follow single responsibility principle:
- Reusable components in `components/`
- Page-level components in `pages/`
- Shared state in `context/`
- API utilities in `utils/`

## Styling

- Tailwind CSS utility classes
- Custom animations in `index.css`
- Consistent color scheme (blue primary)
- Professional, clean design

## Development Notes

- TypeScript strict mode enabled
- ESLint configured
- Hot module replacement
- Optimized bundle size

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

MIT
