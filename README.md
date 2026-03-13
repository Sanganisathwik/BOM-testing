# Network SOM Testing

This project consists of a Django-based backend and a React (Vite) frontend.

## Project Structure

- `backend/`: Django API server.
- `frontend/`: React + TypeScript frontend application.

## Prerequisites

- Python 3.x
- Node.js & npm

## Setup Instructions

### Backend
1. Navigate to the `backend` directory.
2. Create and activate a virtual environment (`python -m venv venv`).
3. Install dependencies: `pip install -r requirements.txt`.
4. Configure environment variables in a `.env` file.
5. Run the server: `python manage.py runserver`.

### Frontend
1. Navigate to the `frontend` directory.
2. Install dependencies: `npm install`.
3. Start the development server: `npm run dev`.

## Environmental Variables
The project uses `.env` files for configuration. Ensure you create these locally based on the project requirements. Sensitive files are ignored by git.
