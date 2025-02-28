# OSINT Comments Frontend

A Vue.js frontend for the OSINT Comments project.

## Project Setup

```bash
# Install dependencies
npm install

# Serve with hot-reload for development
npm run serve

# Build for production
npm run build
```

## Features

- Dashboard with statistics
- Crawler interface for fetching articles
- Comments interface for gathering comments
- Analysis interface for analyzing comments

## Architecture

The frontend is built with Vue.js and communicates with the FastAPI backend. It uses:

- Vue Router for navigation
- Axios for API requests
- Bootstrap for styling

## Development

The frontend is designed to work with the FastAPI backend running on `http://localhost:8000`. Make sure the backend is running before starting the frontend.

## Folder Structure

```
frontend/
  ├── public/              # Static files
  │   └── index.html       # HTML template
  ├── src/                 # Source files
  │   ├── components/      # Vue components
  │   ├── views/           # Vue views (pages)
  │   ├── router/          # Vue Router configuration
  │   ├── App.vue          # Main app component
  │   └── main.js          # Entry point
  ├── package.json         # Dependencies and scripts
  └── README.md            # This file
