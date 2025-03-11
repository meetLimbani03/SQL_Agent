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

# Title and description
st.title("SQL Database Agent")
st.markdown("""
This agent can help you query your PostgreSQL database using natural language.
It will intelligently fetch only the schema information it needs to answer your question.
""")

# Main chat interface
st.header("Chat with your Database")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and "data" in message:
            st.write(message["content"])
            
            # Display data as table if available
            if isinstance(message["data"], list) and len(message["data"]) > 0:
                try:
                    df = pd.DataFrame(message["data"])
                    st.dataframe(df)
                except Exception:
                    st.json(message["data"])
        else:
            st.write(message["content"])

# Chat input
user_query = st.chat_input("Ask a question about your database...")

if user_query:
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    
    # Display user message
    with st.chat_message("user"):
        st.write(user_query)
    
    # Update last activity timestamp
    import time
    st.session_state.last_activity = time.time()
    
    # Get response from agent
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # The agent now maintains its own conversation history internally
            response = st.session_state.agent.run(user_query)
            
            if response["success"]:
                # Extract any table data if present
                data = None
                content = response["response"]
                
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
                    "data": data
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
