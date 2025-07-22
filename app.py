import streamlit as st
import pandas as pd
import openai
from openai import OpenAI
from datetime import datetime
import os
import json
import numpy as np
from io import BytesIO
import sqlite3
import re

# Set page config
st.set_page_config(
    page_title="KRISPR Business Intelligence Chatbot",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .admin-header {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .chat-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .user-message {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #2196f3;
    }
    
    .ai-message {
        background: #f3e5f5;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 3px solid #9c27b0;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #155724;
    }
    
    .info-box {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #0c5460;
    }
    
    .sql-box {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-family: monospace;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

class KrisprChatbot:
    def __init__(self):
        self.client = None
        # Use data directory for persistent storage
        self.data_dir = "data"
        self.db_path = os.path.join(self.data_dir, "krispr_data.db")
        self.data_summary = None
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
    def initialize_openai(self, api_key):
        """Initialize OpenAI client"""
        try:
            self.client = OpenAI(api_key=api_key)
            return True
        except Exception as e:
            st.error(f"Error initializing OpenAI: {str(e)}")
            return False
    
    def check_database_exists_and_ready(self):
        """Check if database exists and has data"""
        try:
            if not os.path.exists(self.db_path):
                return False, "Database file not found"
            
            conn = sqlite3.connect(self.db_path)
            
            # Check if any tables exist
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                conn.close()
                return False, "Database exists but has no tables"
            
            # Check if tables have data
            total_rows = 0
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                total_rows += row_count
            
            conn.close()
            
            if total_rows == 0:
                return False, "Database exists but has no data"
            
            return True, f"Database ready with {len(tables)} tables and {total_rows:,} total records"
            
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def clean_column_name(self, col_name):
        """Clean column names for SQL compatibility"""
        # Remove special characters and replace with underscores
        clean_name = re.sub(r'[^\w\s]', '_', str(col_name))
        # Replace spaces with underscores
        clean_name = re.sub(r'\s+', '_', clean_name)
        # Remove multiple underscores
        clean_name = re.sub(r'_+', '_', clean_name)
        # Remove leading/trailing underscores
        clean_name = clean_name.strip('_')
        # Ensure it starts with a letter
        if clean_name and not clean_name[0].isalpha():
            clean_name = 'col_' + clean_name
        return clean_name or 'unnamed_column'
    
    def create_database_from_excel(self, uploaded_file):
        """Convert Excel file to SQLite database"""
        try:
            # Remove existing database
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            
            # Create new database connection
            conn = sqlite3.connect(self.db_path)
            
            # Read all sheets from Excel
            xl_file = pd.ExcelFile(uploaded_file)
            sheet_info = {}
            
            for sheet_name in xl_file.sheet_names:
                # Read sheet
                df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                
                # Clean data
                df = df.dropna(how='all').dropna(axis=1, how='all')
                
                # Clean column names for SQL
                original_columns = df.columns.tolist()
                clean_columns = [self.clean_column_name(col) for col in original_columns]
                df.columns = clean_columns
                
                # Create table name (clean sheet name)
                table_name = self.clean_column_name(sheet_name)
                
                # Store the data in SQLite
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                
                # Store metadata
                sheet_info[sheet_name] = {
                    'table_name': table_name,
                    'original_columns': original_columns,
                    'clean_columns': clean_columns,
                    'row_count': len(df),
                    'column_count': len(df.columns)
                }
                
                st.success(f"✅ Sheet '{sheet_name}' → Dataset '{table_name}' ({len(df):,} records)")
            
            conn.close()
            
            # Generate database summary
            self.generate_database_summary(sheet_info)
            
            st.success(f"🎉 Data processed successfully with {len(xl_file.sheet_names)} datasets!")
            st.info(f"📊 Database saved to: {self.db_path}")
            st.warning("⚠️ **IMPORTANT**: Commit the `data/` folder to GitHub to make this persistent!")
            
            return True
            
        except Exception as e:
            st.error(f"Error creating database: {str(e)}")
            return False
    
    def generate_database_summary(self, sheet_info):
        """Generate database schema summary"""
        conn = sqlite3.connect(self.db_path)
        
        summary = {
            "database_path": self.db_path,
            "total_tables": len(sheet_info),
            "tables": {}
        }
        
        for sheet_name, info in sheet_info.items():
            table_name = info['table_name']
            
            # Get table schema
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            schema = cursor.fetchall()
            
            # Get sample data
            cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT 10")
            sample_data = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            # Get all unique values for potential product columns
            product_columns = []
            for col in info['clean_columns']:
                if any(keyword in col.lower() for keyword in ['product', 'name', 'item', 'sku']):
                    cursor = conn.execute(f"SELECT DISTINCT {col} FROM {table_name} WHERE {col} IS NOT NULL LIMIT 50")
                    unique_values = [row[0] for row in cursor.fetchall()]
                    product_columns.append({
                        'column': col,
                        'original_name': info['original_columns'][info['clean_columns'].index(col)],
                        'unique_values': unique_values
                    })
            
            summary["tables"][sheet_name] = {
                "table_name": table_name,
                "schema": schema,
                "sample_data": sample_data,
                "sample_columns": columns,
                "row_count": info['row_count'],
                "column_mapping": dict(zip(info['original_columns'], info['clean_columns'])),
                "product_columns": product_columns
            }
        
        conn.close()
        self.data_summary = summary
    
    def load_existing_database_summary(self):
        """Load database summary from existing database"""
        try:
            if not os.path.exists(self.db_path):
                return False
            
            conn = sqlite3.connect(self.db_path)
            
            # Get all tables
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                conn.close()
                return False
            
            # Generate summary for existing database
            summary = {
                "database_path": self.db_path,
                "total_tables": len(tables),
                "tables": {}
            }
            
            for table_name in tables:
                # Get table schema
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                schema = cursor.fetchall()
                
                # Get sample data
                cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT 10")
                sample_data = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                # Get row count
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                # Create column mapping (simplified for existing DB)
                column_mapping = {col: col for col in columns}
                
                # Get product columns
                product_columns = []
                for col in columns:
                    if any(keyword in col.lower() for keyword in ['product', 'name', 'item', 'sku']):
                        cursor = conn.execute(f"SELECT DISTINCT {col} FROM {table_name} WHERE {col} IS NOT NULL LIMIT 50")
                        unique_values = [row[0] for row in cursor.fetchall()]
                        product_columns.append({
                            'column': col,
                            'original_name': col,
                            'unique_values': unique_values
                        })
                
                summary["tables"][table_name] = {
                    "table_name": table_name,
                    "schema": schema,
                    "sample_data": sample_data,
                    "sample_columns": columns,
                    "row_count": row_count,
                    "column_mapping": column_mapping,
                    "product_columns": product_columns
                }
            
            conn.close()
            self.data_summary = summary
            return True
            
        except Exception as e:
            st.error(f"Error loading existing database: {str(e)}")
            return False
    
    def get_database_info(self):
        """Get database tables and columns for debugging"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get all tables
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get columns for each table
            table_info = {}
            for table in tables:
                cursor = conn.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                table_info[table] = columns
            
            conn.close()
            return table_info
        except Exception as e:
            return f"Error getting database info: {str(e)}"
    
    def execute_sql_query(self, query):
        """Execute SQL query and return results"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Clean the query one more time
            clean_query = query.strip()
            if clean_query.endswith(';;'):
                clean_query = clean_query[:-1]  # Remove double semicolon
            
            cursor = conn.execute(clean_query)
            results = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            conn.close()
            
            return {
                "success": True,
                "columns": columns,
                "data": results,
                "row_count": len(results),
                "query_executed": clean_query
            }
        except Exception as e:
            # Get database info for debugging
            db_info = self.get_database_info()
            return {
                "success": False,
                "error": str(e),
                "query_attempted": query,
                "database_info": db_info
            }
    
    def get_ai_response(self, user_question):
        """Get AI response using SQL database"""
        if not self.client:
            return "Please contact admin to configure the system first."
        
        # Check database status
        db_ready, db_message = self.check_database_exists_and_ready()
        if not db_ready:
            return f"Database not ready: {db_message}. Please contact admin to upload data."
        
        # Load database summary if not already loaded
        if not self.data_summary:
            if not self.load_existing_database_summary():
                return "Error loading database information. Please contact admin."
        
        try:
            # Handle simple greetings only (not data questions)
            question_lower = user_question.lower().strip()
            simple_greetings = ['hi', 'hello', 'hey']
            
            # Only respond with greeting if it's JUST a greeting, not a data question
            if question_lower in simple_greetings:
                return "Hi there! 👋 I'm KRISPR Business Intelligence Assistant. I'm here to help you analyze your business data and provide insights. How can I assist you today?"
            
            if question_lower in ['who are you', 'what are you', 'introduce yourself']:
                return "I'm KRISPR Business Intelligence Assistant, your expert data analyst. I can help you understand your business data, find specific metrics, analyze trends, and provide actionable insights. What would you like to know about your data?"
            
            # For ALL OTHER questions (including data questions), process with SQL
            # Prepare database context
            context = f"""
            You are KRISPR Business Intelligence Assistant, an expert data analyst. You have access to business data from multiple sources.
            
            DATABASE INFORMATION:
            - Total Data Sources: {self.data_summary['total_tables']}
            
            AVAILABLE DATA SOURCES AND SCHEMA:
            """
            
            # Add detailed table information
            for sheet_name, table_info in self.data_summary['tables'].items():
                context += f"""
                
            DATA SOURCE: {table_info['table_name']} (from "{sheet_name}")
            - Records: {table_info['row_count']:,}
            - Columns: {', '.join(table_info['sample_columns'])}
            
            Column Mapping (Original → System):
            {json.dumps(table_info['column_mapping'], indent=2)}
            
            Sample Data from {table_info['table_name']}:
            Columns: {table_info['sample_columns']}
            """
                for i, row in enumerate(table_info['sample_data'][:5]):
                    context += f"\nRow {i+1}: {row}"
                
                # Add product information if available
                if table_info['product_columns']:
                    context += f"""
            
            Product Columns in {table_info['table_name']}:
            """
                    for prod_col in table_info['product_columns']:
                        context += f"""
            - {prod_col['column']} (original: {prod_col['original_name']})
              Sample products: {prod_col['unique_values'][:10]}
            """
            
            context += f"""
            
            INSTRUCTIONS:
            1. You are a business intelligence assistant with access to comprehensive business data
            2. When users ask questions, generate and execute queries to find precise answers
            3. Use SELECT statements to query the data
            4. For vendor/supplier questions, look for columns like 'vendor', 'supplier', 'source', etc.
            5. For sales questions, look for columns like 'units', 'sales', 'quantity', 'amount', etc.
            6. For week questions, look for columns containing 'week' or numeric week values
            7. Always provide the exact query you would use
            8. Based on the schema above, construct accurate queries
            9. Use the clean column names (system-compatible) in your queries
            10. When searching for week 26, use WHERE week = 26 or WHERE week_number = 26
            11. Group results by vendor/supplier to show breakdown
            12. NEVER mention "SQLite", "database", or technical terms - just provide business insights
            
            IMPORTANT: Format your query EXACTLY like this (no markdown, no code blocks):
            SQL_QUERY: SELECT column FROM table WHERE condition;
            EXPLANATION: [your explanation here]
            
            DO NOT use ```sql or ``` formatting. Just provide the plain query after "SQL_QUERY:"
            
            USER QUESTION: {user_question}
            
            Provide your response in this exact format:
            SQL_QUERY: [clean query statement here]
            EXPLANATION: [explanation of what you're looking for]
            """
            
            # Get AI response with SQL query
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_question}
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            # Extract SQL query from response - handle multiple formats
            sql_query = None
            
            # Look for SQL_QUERY: format
            if "SQL_QUERY:" in ai_response:
                sql_start = ai_response.find("SQL_QUERY:") + len("SQL_QUERY:")
                sql_end = ai_response.find("EXPLANATION:", sql_start)
                if sql_end == -1:
                    sql_end = len(ai_response)
                sql_query = ai_response[sql_start:sql_end].strip()
            
            # Clean up the SQL query - remove markdown formatting
            if sql_query:
                # Remove ```sql and ``` markers
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
                # Remove any remaining markdown or HTML
                sql_query = sql_query.replace("<code>", "").replace("</code>", "").strip()
                # Remove any newlines and extra spaces
                sql_query = " ".join(sql_query.split())
                # Ensure it ends with semicolon
                if sql_query and not sql_query.endswith(';'):
                    sql_query += ';'
            
            # Execute the SQL query if found
            if sql_query:
                query_result = self.execute_sql_query(sql_query)
                
                if query_result["success"]:
                    # Format the results
                    if query_result["data"]:
                        # Get final answer from AI
                        final_context = f"""
                        The query was executed successfully. Here are the results:
                        
                        Query: {sql_query}
                        Results: {query_result['data']}
                        Columns: {query_result['columns']}
                        
                        Based on these results, provide a natural, conversational answer to the user's question: {user_question}
                        
                        IMPORTANT RESPONSE GUIDELINES:
                        - Write in a conversational, friendly tone like you're talking to a colleague
                        - Give the direct answer first, then supporting details
                        - Use natural language, not formal structure or numbered lists
                        - Don't use "**Summary Answer**" or "**Breakdown**" formatting
                        - Don't use numbered or bulleted lists unless absolutely necessary
                        - Include specific numbers and vendor names naturally in sentences
                        - Be helpful and insightful but keep it conversational
                        - If multiple vendors, mention them naturally: "Vendor A had 500 units while Vendor B had 300 units"
                        
                        Example of good response style:
                        "Based on your data, Talabat Mart in Dubai Silicon Oasis performed the best with 464 units sold. This is significantly higher than other vendors, showing they have a strong customer base in that area."
                        
                        DO NOT USE:
                        - Numbered lists (1. 2. 3.)
                        - Bullet points with asterisks (* * *)
                        - Bold formatting for sections (**Summary**, **Breakdown**)
                        - Formal business report structure
                        
                        Just answer naturally like a helpful business analyst would in conversation.
                        """
                        
                        final_response = self.client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": final_context},
                                {"role": "user", "content": "Provide the final answer based on the results."}
                            ],
                            max_tokens=1000,
                            temperature=0.1
                        )
                        
                        return final_response.choices[0].message.content
                    else:
                        return "I couldn't find relevant data for that question. I specialize in product sales, weekly trends, and media or organic performance. Try asking: 'Which products had the highest sales last week?' or 'What's the media performance for week 26?'"
                else:
                    return "I couldn't find relevant data for that question. I specialize in product sales, weekly trends, and media or organic performance. Try asking: 'Which products had the highest sales last week?' or 'What's the media performance for week 26?'"
            else:
                # If no SQL query found, check if it's a general question
                if any(word in user_question.lower() for word in ['weather', 'news', 'time', 'date', 'recipe', 'movie', 'music', 'sports', 'politics']):
                    return "I couldn't find relevant data for that question. I specialize in product sales, weekly trends, and media or organic performance. Try asking: 'Which products had the highest sales last week?' or 'What's the media performance for week 26?'"
                else:
                    return ai_response
            
        except Exception as e:
            return "I couldn't find relevant data for that question. I specialize in product sales, weekly trends, and media or organic performance. Try asking: 'Which products had the highest sales last week?' or 'What's the media performance for week 26?'"

def check_admin_password(password):
    """Check if the provided password matches admin password"""
    try:
        admin_password = st.secrets["ADMIN_PASSWORD"]
        return password == admin_password
    except:
        st.error("Admin password not configured in secrets.toml")
        return False

def admin_login_page():
    """Admin login page"""
    st.markdown("""
    <div class="admin-header">
        <h1>🔐 Admin Login</h1>
        <p>Administrator access for data management</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("admin_login"):
        st.header("🔑 Enter Admin Credentials")
        password = st.text_input("Admin Password", type="password", placeholder="Enter admin password")
        submitted = st.form_submit_button("Login as Admin", use_container_width=True)
        
        if submitted:
            if password and check_admin_password(password):
                st.session_state.admin_logged_in = True
                st.session_state.current_page = "admin_panel"
                st.rerun()
            else:
                st.error("❌ Invalid admin password")

def admin_panel():
    """Admin panel for data management"""
    st.markdown("""
    <div class="admin-header">
        <h1>👨‍💼 Admin Panel</h1>
        <p>Data Management & Configuration</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Logout button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.session_state.current_page = "home"
            st.rerun()
    
    # System Status Section for Admin
    st.header("🔧 System Status")
    db_ready, db_message = st.session_state.chatbot.check_database_exists_and_ready()
    
    col1, col2 = st.columns(2)
    with col1:
        if db_ready:
            st.success("✅ Database Ready")
        else:
            st.warning("⚠️ Database Not Ready")
        
        st.info(f"📁 DB Path: `{st.session_state.chatbot.db_path}`")
        st.info(f"📄 File Exists: {'Yes' if os.path.exists(st.session_state.chatbot.db_path) else 'No'}")
    
    with col2:
        if db_ready:
            st.metric("System Status", "Ready", delta="Operational")
        else:
            st.metric("System Status", "Not Ready", delta="Action Required")
    
    st.header("📊 Data Management")
    
    # Check database status
    # db_ready, db_message = st.session_state.chatbot.check_database_exists_and_ready()
    
    if db_ready:
        st.markdown(f"""
        <div class="success-box">
            <strong>✅ Data Status:</strong> {db_message}
        </div>
        """, unsafe_allow_html=True)
        
        # Show current database info
        try:
            conn = sqlite3.connect(st.session_state.chatbot.db_path)
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            st.info(f"📊 Available data sources: {len(tables)} datasets")
            st.info(f"📁 Database location: `{st.session_state.chatbot.db_path}`")
            
            # Show table details
            total_rows = 0
            st.subheader("📈 Data Overview")
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                total_rows += row_count
                st.text(f"• {table.replace('_', ' ')}: {row_count:,} records")
            
            st.success(f"📈 Total data: {total_rows:,} records across {len(tables)} datasets")
            conn.close()
            
        except Exception as e:
            st.warning(f"⚠️ Error reading data: {str(e)}")
    else:
        st.markdown(f"""
        <div class="info-box">
            <strong>ℹ️ Database Status:</strong> {db_message}
        </div>
        """, unsafe_allow_html=True)
    
    st.header("📁 Upload New Data")
    
    # Important note about persistence
    st.markdown("""
    <div class="info-box">
        <strong>🔗 Making Data Persistent:</strong><br>
        After uploading data, you must commit the <code>data/</code> folder to GitHub for persistence:
        <br><br>
        <code>
        git add data/<br>
        git commit -m "Update database"<br>
        git push
        </code>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Excel File", 
        type=['xlsx', 'xls'],
        help="Upload your Excel file - all sheets will be processed automatically"
    )
    
    if uploaded_file:
        try:
            # Read all sheet names
            xl_file = pd.ExcelFile(uploaded_file)
            sheet_names = xl_file.sheet_names
            
            st.success(f"✅ File uploaded successfully!")
            st.info(f"📊 Found {len(sheet_names)} sheet(s): {', '.join(sheet_names)}")
            
            # Preview of all sheets
            st.subheader("📋 Workbook Preview")
            for i, sheet_name in enumerate(sheet_names[:3]):  # Show first 3 sheets
                with st.expander(f"Sheet: {sheet_name}"):
                    preview_df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                    st.write(f"📈 {len(preview_df):,} rows × {len(preview_df.columns)} columns")
                    st.dataframe(preview_df.head(3), use_container_width=True)
            
            if len(sheet_names) > 3:
                st.info(f"... and {len(sheet_names) - 3} more sheets")
            
            # Convert to database button
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("💾 Process Data", use_container_width=True, type="primary"):
                    with st.spinner("🔄 Processing your business data..."):
                        if st.session_state.chatbot.create_database_from_excel(uploaded_file):
                            st.balloons()
                            st.success("🎉 Data processed successfully!")
                            st.success("📊 All sheets are ready for analysis")
                            st.info("💡 Users can now query data using the chatbot")
                            st.warning("⚠️ **Don't forget to commit the `data/` folder to GitHub!**")
                        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")

def chatbot_page():
    """Main chatbot interface"""
    st.markdown("""
    <div class="main-header">
        <h1>🧬 KRISPR Business Intelligence Chatbot</h1>
        <p>Ask questions about your business data and get intelligent insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize input key for clearing
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0
    
    # Check database status (but don't show to users)
    db_ready, db_message = st.session_state.chatbot.check_database_exists_and_ready()
    
    if not db_ready:
        st.markdown("""
        <div class="info-box">
            <strong>⚠️ System Notice:</strong> Data is being prepared. Please contact admin if this persists.
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Load database summary if not already loaded (silently)
    if not st.session_state.chatbot.data_summary:
        if not st.session_state.chatbot.load_existing_database_summary():
            st.error("❌ Error loading data. Please contact admin.")
            return
    
    # Main chat interface - full width
    st.header("💬 Chat with Your Data")
    
    # Chat history container with new styling
    st.markdown('<div class="chat-history">', unsafe_allow_html=True)
    
    # Display chat history
    for i, chat in enumerate(st.session_state.chat_history):
        st.markdown(f"""
        <div class="user-message">
            <strong>You:</strong> {chat['user']}
        </div>
        <div class="ai-message">
            <strong>KRISPR AI:</strong><br>{chat['ai']}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # User input
    user_question = st.text_input(
        "Ask a question about your data:", 
        placeholder="e.g., What is media units sold of Krispr Premium Rosemary, 40g in week 26?",
        key=f"user_input_{st.session_state.input_key}"
    )
    
    # Beautiful buttons with proper spacing
    st.markdown("<br>", unsafe_allow_html=True)  # Add some space
    
    col_send, col_clear, col_spacer = st.columns([2, 2, 6])
    
    with col_send:
        send_button = st.button("🚀 Send", key="send_btn", type="primary", help="Ask your question", use_container_width=True)
    
    with col_clear:
        clear_button = st.button("🗑️ Clear", key="clear_btn", type="secondary", help="Clear chat history", use_container_width=True)
    
    # Add custom CSS for beautiful buttons
    st.markdown("""
    <style>
    /* Send Button - Beautiful gradient with hover effect */
    div.stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(45deg, #667eea, #764ba2) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 14px 0 rgba(102, 126, 234, 0.3) !important;
        width: 100% !important;
        min-height: 50px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    div.stButton > button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(45deg, #5a6fd8, #6a42a0) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px 0 rgba(102, 126, 234, 0.4) !important;
    }
    
    div.stButton > button[data-testid="baseButton-primary"]:active {
        transform: translateY(0px) !important;
    }
    
    /* Clear Button - Elegant secondary style */
    div.stButton > button[data-testid="baseButton-secondary"] {
        background: linear-gradient(45deg, #f093fb, #f5576c) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 14px 0 rgba(240, 147, 251, 0.3) !important;
        width: 100% !important;
        min-height: 50px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    div.stButton > button[data-testid="baseButton-secondary"]:hover {
        background: linear-gradient(45deg, #e885f0, #e04863) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px 0 rgba(240, 147, 251, 0.4) !important;
    }
    
    div.stButton > button[data-testid="baseButton-secondary"]:active {
        transform: translateY(0px) !important;
    }
    
    /* Input Field - Modern styling */
    div.stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 2px solid #e1e5e9 !important;
        padding: 14px 18px !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        background-color: #fafbfc !important;
    }
    
    div.stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        background-color: white !important;
    }
    
    /* Button container spacing */
    .element-container:has(button) {
        margin-top: 20px !important;
    }
    
    /* Add gap between buttons */
    div[data-testid="column"]:has(button) {
        padding: 0 8px !important;
    }
    
    /* Hide Streamlit default styling */
    .stButton {
        margin-bottom: 0 !important;
    }
    
    /* Chat container improvements */
    .user-message, .ai-message {
        margin-bottom: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Handle button clicks
    if send_button and user_question:
        with st.spinner("🧠 Thinking..."):
            ai_response = st.session_state.chatbot.get_ai_response(user_question)
            st.session_state.chat_history.append({
                "user": user_question,
                "ai": ai_response
            })
            # Clear input by incrementing key
            st.session_state.input_key += 1
        st.rerun()
    
    if clear_button:
        st.session_state.chat_history = []
        st.session_state.input_key += 1
        st.rerun()

def home_page():
    """Home page with navigation"""
    st.markdown("""
    <div class="main-header">
        <h1>🧬 KRISPR Business Intelligence</h1>
        <p>Your AI-powered business data analysis platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.header("🚀 Welcome to KRISPR BI")
    
    # Clean home page without system status
    st.markdown("""
    <div class="info-box">
        <strong>🎯 Get Started:</strong> Choose an option below to access your business intelligence tools.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 💬 Business Intelligence Chatbot
        
        Ask questions about your business data:
        - "What is media units sold of Krispr Premium Rosemary, 40g in week 26?"
        - "Which product has maximum sales?"
        - "Compare performance across weeks"
        """)
        
        if st.button("🚀 Go to Chatbot", use_container_width=True, type="primary"):
            st.session_state.current_page = "chatbot"
            st.rerun()
    
    with col2:
        st.markdown("""
        ### 👨‍💼 Admin Panel
        
        Administrative access for:
        - Upload Excel files
        - Manage business data
        - Update datasets
        
        """)
        
        if st.button("🔐 Admin Login", use_container_width=True):
            st.session_state.current_page = "admin_login"
            st.rerun()

def main():
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = KrisprChatbot()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Initialize OpenAI
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        if not st.session_state.get('openai_initialized', False):
            if st.session_state.chatbot.initialize_openai(api_key):
                st.session_state.openai_initialized = True
    except Exception as e:
        st.error("⚠️ OpenAI API key not found in secrets.toml")
        st.stop()
    
    # Navigation
    with st.sidebar:
        st.header("🧭 Navigation")
        
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
        
        if st.button("💬 Chatbot", use_container_width=True):
            st.session_state.current_page = "chatbot"
            st.rerun()
        
        if st.session_state.admin_logged_in:
            if st.button("👨‍💼 Admin Panel", use_container_width=True):
                st.session_state.current_page = "admin_panel"
                st.rerun()
        else:
            if st.button("🔐 Admin Login", use_container_width=True):
                st.session_state.current_page = "admin_login"
                st.rerun()
        
        # Clean sidebar - no system status here
    
    # Route to appropriate page
    if st.session_state.current_page == "home":
        home_page()
    elif st.session_state.current_page == "chatbot":
        chatbot_page()
    elif st.session_state.current_page == "admin_login":
        admin_login_page()
    elif st.session_state.current_page == "admin_panel" and st.session_state.admin_logged_in:
        admin_panel()
    else:
        st.session_state.current_page = "home"
        home_page()

if __name__ == "__main__":
    main()
