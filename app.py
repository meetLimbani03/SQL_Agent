"""
Streamlit app for SQL Agent
"""
import streamlit as st
import pandas as pd
from sql_agent import SQLAgent

# Set page configuration
st.set_page_config(
    page_title="SQL Agent",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = SQLAgent()

# We'll use the app's chat_history for display purposes
# and the agent's internal conversation_history for context
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
# Track last activity time for connection management
if "last_activity" not in st.session_state:
    st.session_state.last_activity = 0
    
# Store SQL queries per user message
if "user_queries" not in st.session_state:
    st.session_state.user_queries = {}

# Title and description
st.title("SQL Database Agent")
st.markdown("""
This agent can help you query your PostgreSQL database using natural language.
It will intelligently fetch only the schema information it needs to answer your question.
""")

# Main chat interface
st.header("Chat with your Database")

# Add a dedicated section for the last executed SQL query
if "last_executed_query" in st.session_state and st.session_state.last_executed_query:
    st.sidebar.markdown("### Last SQL Query")
    st.sidebar.code(st.session_state.last_executed_query, language="sql")

# Display chat history with SQL queries
for i, message in enumerate(st.session_state.chat_history):
    # Display the actual message
    with st.chat_message(message["role"]):
        # For user messages, show the SQL query above if available
        if message["role"] == "user":
            # Check if this user message has an associated SQL query in our mapping
            if "id" in message and message["id"] in st.session_state.user_queries:
                sql_query = st.session_state.user_queries[message["id"]]
                st.markdown("**SQL Query:**")
                st.code(sql_query, language="sql")
            st.write(message["content"])
        # For assistant messages
        else:
            st.write(message["content"])
            
            # Display data as table if available
            if "data" in message and isinstance(message["data"], list) and len(message["data"]) > 0:
                try:
                    df = pd.DataFrame(message["data"])
                    st.dataframe(df)
                except Exception:
                    st.json(message["data"])

# Chat input
user_query = st.chat_input("Ask a question about your database...")

if user_query:
    # Generate a unique ID for this message
    import time
    import uuid
    message_id = str(uuid.uuid4())
    
    # Add user message to chat history with ID
    st.session_state.chat_history.append({"role": "user", "content": user_query, "id": message_id})
    
    # Display user message
    with st.chat_message("user"):
        st.write(user_query)
    
    # Update last activity timestamp
    import time
    st.session_state.last_activity = time.time()
    
    # Get response from agent
    with st.chat_message("assistant"):
        with st.spinner("Thinking & executing queries..."):
            # The agent now maintains its own conversation history internally
            response = st.session_state.agent.run(user_query)
            
            if response["success"]:
                # Extract any table data if present
                data = None
                content = response["response"]

                # Store and display the SQL query prominently
                if "last_query" in response and response["last_query"]:
                    # Store in session state for persistent display
                    st.session_state.last_executed_query = response["last_query"]
                    
                    # Store the SQL query for the current user message
                    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user" and "id" in st.session_state.chat_history[-1]:
                        user_message_id = st.session_state.chat_history[-1]["id"]
                        st.session_state.user_queries[user_message_id] = response["last_query"]
                    
                    # Display prominently in the main chat area
                    st.code(response["last_query"], language="sql")
                    st.markdown("---")
                
                
                # Check if the response contains SQL results
                if "```json" in content:
                    try:
                        import re
                        import json
                        
                        # Extract JSON data from markdown code blocks
                        json_match = re.search(r"```json\n([\s\S]*?)\n```", content)
                        if json_match:
                            json_str = json_match.group(1)
                            data = json.loads(json_str)
                            
                            # Remove the JSON block from the content
                            content = content.replace(json_match.group(0), "")
                    except Exception:
                        pass
                
                st.write(content)
                
                # Display data as table if available
                if data:
                    try:
                        df = pd.DataFrame(data)
                        st.dataframe(df)
                    except Exception:
                        st.json(data)
                
                # Add assistant message to chat history
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": content,
                    "data": data,
                    "last_query": response.get("last_query")
                })
                
                # Update last activity timestamp
                import time
                st.session_state.last_activity = time.time()
            else:
                error_message = f"Error: {response['error']}"
                st.error(error_message)
                
                # Add error message to chat history
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": error_message
                })
                
                # Update last activity timestamp
                import time
                st.session_state.last_activity = time.time()
