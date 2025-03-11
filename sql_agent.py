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
from db_connector import SupabaseConnector

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
        self.db = SupabaseConnector()
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
                name="list_schemas",
                func=lambda _: self.db.get_schemas(),
                description="Lists all available schemas in the database. Use this to get an overview of the database structure."
            ),
            Tool(
                name="list_tables",
                func=lambda schema: self.db.get_tables_in_schema(schema),
                description="Lists all tables in a specific schema. Input should be a schema name."
            ),
            Tool(
                name="get_table_schema",
                func=lambda x: self.db.get_table_schema(*x.split('.')) if isinstance(x, str) and '.' in x else None,
                description="Gets the schema of a specific table. Input should be a string in the format 'schema_name.table_name'."
            ),
            Tool(
                name="get_foreign_keys",
                func=lambda x: self.db.get_foreign_keys(*x.split('.')) if isinstance(x, str) and '.' in x else None,
                description="Gets the foreign keys of a specific table. Input should be a string in the format 'schema_name.table_name'."
            ),
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
        You are a helpful SQL assistant that can help users interact with a database.
        You have access to tools that can inspect the database schema and execute SQL queries.
        
        When a user asks a question about data, follow these steps:
        1. First, determine which tables and schemas might be relevant to the query.
        2. Use the appropriate tools to inspect the schema of those tables.
        3. Formulate a SQL query based on the user's question and the schema information.
        4. Execute the query and return the results.
        
        Important: Only request schema information for tables that are relevant to the user's query.
        Do not try to load the entire database schema at once to prevent overloading.
        
        When using the get_table_schema or get_foreign_keys tools, provide the input as a string in the format 'schema_name.table_name'.
        For example: 'public.users'
        
        Always explain your reasoning and the SQL queries you're executing.
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
