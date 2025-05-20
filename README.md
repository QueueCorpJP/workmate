# Chatbot Application - Local Setup Guide with Supabase

This guide will help you set up and run both the backend and frontend components of the chatbot application locally, using Supabase for the database.

## Prerequisites

- Python 3.8 or higher
- Node.js and npm
- A Supabase account (free tier is sufficient)

## Setup Instructions

### 1. Set up Supabase

Run the Supabase setup guide:

```
setup_supabase.bat
```

This will guide you through:
1. Creating a Supabase account (if you don't have one)
2. Creating a new Supabase project
3. Getting your Supabase project URL and API key
4. Updating your .env file with the correct Supabase credentials

### 2. Set up the Backend

Run the setup script:

```
setup_backend.bat
```

This script will:
- Create a Python virtual environment
- Install all required dependencies including the Supabase client
- Install Playwright
- Create a `.env` file with default configuration (you'll need to update this with your Supabase details)

Note: You'll need to replace the dummy Google API key in the `.env` file with a real one if you want to use the Gemini AI features.

### 3. Set up the Frontend

Run the setup script:

```
setup_frontend.bat
```

This script will install all the required npm packages.

## Running the Application

### 1. Start the Backend

Run the backend server:

```
run_backend.bat
```

This will:
- Set up the database schema in your Supabase project
- Start the backend server on http://localhost:8083

### 2. Start the Frontend

Run the frontend development server:

```
run_frontend.bat
```

The frontend will start on http://localhost:3025

### 3. Run Everything at Once

Alternatively, you can run both the backend and frontend with a single command:

```
run_all.bat
```

## Accessing the Application

Once both the backend and frontend are running, you can access the application by opening http://localhost:3025 in your web browser.

## Default Login Credentials

The application comes with a default admin user:

- Email: queue@queuefood.co.jp
- Password: QueueMainPass0401

## Troubleshooting

- If you encounter database connection issues, make sure your Supabase credentials in the `.env` file are correct.
- If the frontend can't connect to the backend, check that the backend server is running on port 8083.
- If you get database schema errors, check the Supabase SQL Editor to see if the tables were created correctly.

## Supabase Database Management

You can manage your database directly through the Supabase dashboard:

1. Go to https://supabase.com and log in
2. Select your project
3. Use the "Table Editor" to view and edit your data
4. Use the "SQL Editor" to run custom SQL queries

This gives you a convenient way to manage your database without needing to install any additional tools.