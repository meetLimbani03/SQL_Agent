"""
SQL Agent for interacting with Supabase database
"""
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from pg_connector import PostgresConnector
from connection_manager import ConnectionManager

# Load environment variables
load_dotenv()

class SQLAgent:
    """
    Agent for interacting with SQL databases
    """
    def __init__(self):
        """
        Initialize the SQL agent with tools
        """
        self.db = PostgresConnector()
        
        # Initialize connection manager with 10 minute timeout
        self.connection_manager = ConnectionManager(self.db, idle_timeout=600)
        
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create tools
        self.tools = self._create_tools()
        
        # Initialize conversation history
        self.conversation_history = []
        
        # Create agent
        self.agent_executor = self._create_agent()
        
    def _create_tools(self) -> List[Tool]:
        """
        Create tools for the agent
        """
        tools = [
            Tool(
                name="execute_query",
                func=self.db.execute_query,
                description="Executes a SQL query. Input should be a valid SQL query string."
            )
        ]
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """
        Create the agent with tools
        """
        system_message = """
        You are a helpful SQL assistant that can help users interact with a PostgreSQL database.
        You have access to tools that can inspect the database schema and execute SQL queries.
        
        When a user asks a question about data, follow these steps:
        1. First, explore the database schema to understand available tables using: 
           SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
        
        2. For each relevant table, examine its structure using:
           SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '<table_name>';
        
        3. Discover relationships between tables using:
           SELECT tc.table_schema, tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_schema AS foreign_table_schema, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name FROM information_schema.table_constraints tc JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name WHERE constraint_type = 'FOREIGN KEY';
        
        4. CRITICAL: ALWAYS explore the actual data values before using them in queries. This is mandatory, not optional:
           - When asked about countries, FIRST run: SELECT country_id, country_name FROM countries;
           - When asked about departments, FIRST run: SELECT department_id, department_name FROM departments;
           
           When a user mentions a country name like "US" or "United States", NEVER assume the database format.
           ALWAYS check both the country_id and country_name values in the database first.
        
        5. Formulate appropriate SQL queries, using JOINs when data spans multiple tables.
        
        Important notes:
        - When users mention entities like countries, departments, or job titles in natural language, IMMEDIATELY check how they are stored in the database
        - User queries like "employees from US" require checking if "US" is stored as country_id or country_name
        - Try both exact matches and LIKE '%value%' if initial queries return no results
        - Format SQL query results as markdown tables when possible
        - Do not generate SQL queries that edit the database in any way
        - Explain your reasoning and the SQL queries you're executing
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create the agent
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create the agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )
        
        return agent_executor
    
    def run(self, query: str) -> Dict[str, Any]:
        """
        Run the agent with a user query
        """
        try:
            # Update connection activity timestamp
            self.connection_manager.update_activity()
            
            # Include conversation history in the agent invocation
            response = self.agent_executor.invoke({
                "input": query,
                "chat_history": self.conversation_history
            })
            
            # Add the current interaction to the conversation history
            self.conversation_history.append(("human", query))
            self.conversation_history.append(("ai", response["output"]))
            
            # Keep conversation history to a reasonable size (last 10 interactions)
            if len(self.conversation_history) > 20:  # 10 interactions (human + ai)
                self.conversation_history = self.conversation_history[-20:]
                
            return {"success": True, "response": response["output"]}
        except Exception as e:
            import traceback
            print(f"Error in agent execution: {str(e)}")
            print(traceback.format_exc())
            return {"success": False, "error": str(e)}
