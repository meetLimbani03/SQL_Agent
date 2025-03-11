# SQL Agent for Supabase

This project implements an intelligent SQL agent that can query a Supabase database using natural language. The agent is designed to efficiently retrieve database schema information on-demand, preventing context overload by only fetching schema details relevant to the current query.

## Features

- Natural language interface to your Supabase database
- On-demand schema inspection (tables, columns, foreign keys)
- Intelligent query generation and execution
- Streamlit web interface for easy interaction

## Architecture

The application consists of three main components:

1. **Database Connector** (`db_connector.py`): Handles connections to Supabase and provides methods for schema inspection and query execution.
2. **SQL Agent** (`sql_agent.py`): Implements the LangChain-based agent with tools for database interaction.
3. **Streamlit App** (`app.py`): Provides a user-friendly web interface for interacting with the agent.

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Make sure your `.env` file contains the necessary credentials:
   ```
   OPENAI_API_KEY=your_openai_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_API_KEY=your_supabase_api_key
   ```

## Usage

1. Start the Streamlit app:
   ```
   streamlit run app.py
   ```
2. Open your web browser and navigate to the URL provided by Streamlit (typically http://localhost:8501)
3. Enter your database queries in natural language

## Example Queries

- "What tables are available in the public schema?"
- "Show me the schema of the users table"
- "How many users do we have in the database?"
- "What are the top 5 products by sales?"

## Requirements

- Python 3.8+
- LangChain
- OpenAI API key
- Supabase account and API key
- Streamlit
