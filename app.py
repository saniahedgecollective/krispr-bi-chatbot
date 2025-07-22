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
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fresh, Light CSS with KRISPR brand colors
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles - Fresh & Light */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #f0f8f0 0%, #e8f5e8 30%, #f8fff8 70%, #e3f2fd 100%);
        min-height: 100vh;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        margin: 1rem;
        border: 1px solid rgba(76, 175, 80, 0.1);
        box-shadow: 0 8px 32px rgba(76, 175, 80, 0.1);
    }
    
    /* Fresh Header with Green Gradient */
    .main-header {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.9) 0%, rgba(129, 199, 132, 0.8) 50%, rgba(165, 214, 167, 0.7) 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
        box-shadow: 0 12px 30px rgba(76, 175, 80, 0.2);
        animation: gentleGlow 4s ease-in-out infinite alternate;
    }
    
    @keyframes gentleGlow {
        0% { box-shadow: 0 12px 30px rgba(76, 175, 80, 0.2); }
        100% { box-shadow: 0 15px 35px rgba(129, 199, 132, 0.25); }
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        animation: shimmer 4s infinite;
        z-index: 1;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    .main-header h1 {
        position: relative;
        z-index: 2;
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
    }
    
    .main-header p {
        position: relative;
        z-index: 2;
        font-size: 1.1rem;
        font-weight: 400;
        opacity: 0.95;
    }
    
    /* Admin Header - Light Orange/Red */
    .admin-header {
        background: linear-gradient(135deg, rgba(255, 87, 34, 0.8) 0%, rgba(255, 152, 0, 0.7) 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 10px 25px rgba(255, 87, 34, 0.2);
    }
    
    /* Light Feature Cards */
    .feature-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(76, 175, 80, 0.2);
        padding: 2rem;
        border-radius: 18px;
        margin-bottom: 2rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        box-shadow: 0 6px 20px rgba(76, 175, 80, 0.08);
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(76, 175, 80, 0.15);
        border-color: rgba(76, 175, 80, 0.3);
        background: rgba(255, 255, 255, 0.95);
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(76, 175, 80, 0.1), transparent);
        transition: left 0.6s;
    }
    
    .feature-card:hover::before {
        left: 100%;
    }
    
    /* Light Chat Containers */
    .chat-container {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        border: 1px solid rgba(76, 175, 80, 0.15);
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.05);
    }
    
    .user-message {
        background: linear-gradient(135deg, rgba(33, 150, 243, 0.12) 0%, rgba(100, 181, 246, 0.08) 100%);
        padding: 1.2rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        border: 1px solid rgba(33, 150, 243, 0.2);
        backdrop-filter: blur(8px);
        animation: slideInLeft 0.4s ease-out;
        color: #1565C0;
        font-weight: 500;
    }
    
    .ai-message {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.12) 0%, rgba(129, 199, 132, 0.08) 100%);
        padding: 1.2rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        border: 1px solid rgba(76, 175, 80, 0.2);
        backdrop-filter: blur(8px);
        animation: slideInRight 0.4s ease-out;
        color: #1B5E20;
        font-weight: 500;
    }
    
    /* Better text contrast for readability */
    .user-message strong {
        color: #0D47A1 !important;
        font-weight: 700;
    }
    
    .ai-message strong {
        color: #0D4F14 !important;
        font-weight: 700;
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInRight {
        from { transform: translateX(20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Light Status Boxes */
    .success-box {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(129, 199, 132, 0.08) 100%);
        border: 1px solid rgba(76, 175, 80, 0.25);
        padding: 1.2rem;
        border-radius: 12px;
        margin: 1rem 0;
        color: #2e7d32;
        backdrop-filter: blur(8px);
    }
    
    .info-box {
        background: linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(100, 181, 246, 0.08) 100%);
        border: 1px solid rgba(33, 150, 243, 0.25);
        padding: 1.2rem;
        border-radius: 12px;
        margin: 1rem 0;
        color: #1565c0;
        backdrop-filter: blur(8px);
    }
    
    /* Smaller, KRISPR-branded Primary Buttons */
    div.stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #FFA726 0%, #FFB74D 50%, #FFCC02 100%) !important;
        color: #1B5E20 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 24px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 3px 12px rgba(255, 167, 38, 0.3) !important;
        width: auto !important;
        min-height: 36px !important;
        max-width: 120px !important;
        position: relative !important;
        overflow: hidden !important;
        text-transform: none !important;
        margin: 0 auto !important;
    }
    
    div.stButton > button[data-testid="baseButton-primary"]:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(255, 167, 38, 0.4) !important;
        background: linear-gradient(135deg, #FF9800 0%, #FFA726 50%, #FFB74D 100%) !important;
        color: #0D4F14 !important;
    }
    
    div.stButton > button[data-testid="baseButton-primary"]::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 100% !important;
        height: 100% !important;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent) !important;
        transition: left 0.5s !important;
    }
    
    div.stButton > button[data-testid="baseButton-primary"]:hover::before {
        left: 100% !important;
    }
    
    /* Form submit button specific styling */
    div[data-testid="stForm"] button[data-testid="baseButton-primary"] {
        width: 120px !important;
        margin: 10px auto !important;
        display: block !important;
    }
    
    /* Smaller Secondary Button with KRISPR orange */
    div.stButton > button[data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, #FF7043 0%, #FF8A65 50%, #FFAB91 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 3px 12px rgba(255, 112, 67, 0.3) !important;
        width: auto !important;
        min-height: 36px !important;
        max-width: 120px !important;
        position: relative !important;
        overflow: hidden !important;
        text-transform: none !important;
        margin: 0 auto !important;
    }
    
    div.stButton > button[data-testid="baseButton-secondary"]:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(255, 112, 67, 0.4) !important;
        background: linear-gradient(135deg, #f4511e 0%, #ff7043 50%, #ff8a65 100%) !important;
    }
    
    /* Regular Navigation buttons - Smaller & KRISPR branded */
    div.stButton > button:not([data-testid="baseButton-primary"]):not([data-testid="baseButton-secondary"]) {
        background: rgba(255, 255, 255, 0.9) !important;
        color: #2E7D32 !important;
        border: 1px solid rgba(76, 175, 80, 0.3) !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        backdrop-filter: blur(8px) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        min-height: 36px !important;
        font-size: 13px !important;
        text-shadow: none !important;
    }
    
    div.stButton > button:not([data-testid="baseButton-primary"]):not([data-testid="baseButton-secondary"]):hover {
        background: linear-gradient(135deg, #FFF3E0 0%, #FFECB3 100%) !important;
        border-color: rgba(255, 167, 38, 0.5) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(255, 167, 38, 0.15) !important;
        color: #1B5E20 !important;
    }
    
    /* Light Input Field */
    div.stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 1px solid rgba(76, 175, 80, 0.3) !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
        transition: all 0.3s ease !important;
        background: rgba(255, 255, 255, 0.9) !important;
        backdrop-filter: blur(8px) !important;
        color: #2e7d32 !important;
        font-weight: 500 !important;
    }
    
    div.stTextInput > div > div > input:focus {
        border-color: rgba(76, 175, 80, 0.6) !important;
        box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.15) !important;
        background: rgba(255, 255, 255, 1) !important;
        outline: none !important;
    }
    
    div.stTextInput > div > div > input::placeholder {
        color: rgba(76, 175, 80, 0.7) !important;
    }
    
    /* Light Sidebar */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(15px) !important;
        border-right: 1px solid rgba(76, 175, 80, 0.1) !important;
    }
    
    .css-1d391kg h2 {
        color: #2e7d32 !important;
        font-weight: 600 !important;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Home page enhancements */
    .home-feature {
        text-align: center;
        padding: 1.8rem 1rem;
    }
    
    .home-feature h3 {
        color: #2e7d32;
        font-size: 1.6rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    .home-feature p {
        color: #4caf50;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }
    
    /* Text colors for better readability */
    .stMarkdown, .stText {
        color: #2e7d32;
    }
    
    /* Loading animations */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
    
    /* Button spacing improvements */
    .element-container:has(button) {
        margin-top: 15px !important;
    }
    
    div[data-testid="column"]:has(button) {
        padding: 0 6px !important;
    }
</style>

<script>
// Enhanced Enter key functionality with multiple selectors
function setupEnterKeyHandler() {
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            // Try multiple ways to find the input field
            let input = document.querySelector('input[placeholder*="business data"]') ||
                       document.querySelector('input[placeholder*="Ask about"]') ||
                       document.querySelector('input[placeholder*="Search"]') ||
                       document.querySelector('div[data-testid="textInput"] input') ||
                       document.querySelector('.stTextInput input');
            
            if (input && document.activeElement === input && input.value.trim()) {
                e.preventDefault();
                
                // Try multiple ways to find the send button
                let sendButton = document.querySelector('button[key="send_btn"]') ||
                               document.querySelector('button[data-testid="baseButton-primary"]') ||
                               document.querySelector('button:contains("Send")') ||
                               Array.from(document.querySelectorAll('button')).find(btn => btn.textContent.includes('Send'));
                
                if (sendButton) {
                    sendButton.click();
                }
            }
        }
    });
}

// Run the setup immediately and also after a delay to ensure Streamlit has loaded
setupEnterKeyHandler();
setTimeout(setupEnterKeyHandler, 1000);
setTimeout(setupEnterKeyHandler, 2000);

// Also run when the page content changes (Streamlit re-renders)
const observer = new MutationObserver(function(mutations) {
    setupEnterKeyHandler();
});
observer.observe(document.body, { childList: true, subtree: true });
</script>
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
            
            if question_lower in ['who are you', 'what are you','what can you do ?', 'introduce yourself']:
                return "I'm KRISPR Business Intelligence Assistant, your expert data analyst. I can help you understand your business data, find specific metrics, analyze trends, and provide actionable insights. What would you like to know about your data?"
            
            # For ALL OTHER questions (including data questions), process with SQL
            # Prepare database context
            context = f"""
            You are KRISPR Business Intelligence Assistant, an expert data analyst. You have access to business data from multiple sources.
            
            DATABASE INFORMATION:
            - Total Data Sources: {self.data_summary['total_tables']}
            
            AVAILABLE DATA SOURCES AND SCHEMA:
            """
            
            # Add detailed table information with enhanced column guidance
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
                for i, row in enumerate(table_info['sample_data'][:3]):  # Show 3 rows instead of 5 for context
                    context += f"\nRow {i+1}: {row}"
                
                # Enhanced column analysis for media/organic detection
                context += f"""
            
            IMPORTANT COLUMN ANALYSIS for {table_info['table_name']}:
            """
                # Look for media/organic related columns
                media_organic_columns = []
                for col in table_info['sample_columns']:
                    if any(keyword in col.lower() for keyword in ['media', 'msv', 'organic', 'osv', 'units_sold', 'performance', 'sold']):
                        media_organic_columns.append(col)
                
                if media_organic_columns:
                    context += f"Media/Organic Related Columns: {', '.join(media_organic_columns)}\n"
                
                # Look for week columns
                week_columns = [col for col in table_info['sample_columns'] if 'week' in col.lower()]
                if week_columns:
                    context += f"Week Columns: {', '.join(week_columns)}\n"
                
                # Add product information if available
                if table_info['product_columns']:
                    context += f"""
            Product Columns in {table_info['table_name']}:
            """
                    for prod_col in table_info['product_columns']:
                        context += f"""
            - {prod_col['column']} (original: {prod_col['original_name']})
              Sample products: {prod_col['unique_values'][:5]}
            """
            
            context += f"""
            
            INSTRUCTIONS:
            1. You are a business intelligence assistant with access to comprehensive business data
            2. When users ask questions, ALWAYS generate and execute queries to find precise answers
            3. Use SELECT statements to query the data - NEVER give up without trying SQL first
            4. For media vs organic comparisons, look for columns containing:
               - 'media', 'MSV', 'Media_Units_Sold', 'media_sold', 'media_performance'
               - 'organic', 'OSV', 'Org_Units_Sold', 'organic_sold', 'organic_performance'
            5. For vendor/supplier questions, look for columns like 'vendor', 'supplier', 'source', etc.
            6. For sales questions, look for columns like 'units', 'sales', 'quantity', 'amount', etc.
            7. For week questions, look for columns containing 'week' or numeric week values
            8. For weekly comparisons, use GROUP BY week to compare across different weeks
            9. For performance comparisons, calculate totals, averages, or ratios as needed
            10. ALWAYS try to find relevant data - be creative with column name variations
            11. Use the clean column names (system-compatible) in your queries
            12. When searching for week 25/26, use WHERE week = 25 or WHERE week_number = 25
            13. For comparisons, use SUM(), AVG(), or direct column comparisons
            14. Group results by vendor/week/product as needed for breakdowns
            15. NEVER mention "SQLite", "database", or technical terms - just provide business insights
            
            IMPORTANT COMPARISON EXAMPLES:
            - Media vs Organic: SELECT week, SUM(media_units_sold) as media, SUM(org_units_sold) as organic FROM table WHERE week = 25;
            - Weekly Sales Comparison: SELECT week, SUM(units_sold) FROM table GROUP BY week ORDER BY week;
            - Product Performance: SELECT product, SUM(units_sold) FROM table WHERE week BETWEEN 20 AND 25 GROUP BY product;
            
            IMPORTANT: Format your query EXACTLY like this (no markdown, no code blocks):
            SQL_QUERY: SELECT column FROM table WHERE condition;
            EXPLANATION: [your explanation here]
            
            DO NOT use ```sql or ``` formatting. Just provide the plain query after "SQL_QUERY:"
            ALWAYS TRY TO GENERATE A QUERY - don't give generic "I couldn't find data" responses without trying SQL first.
            
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
                        - NEVER mention file names, table names, sheet names, or database structure details
                        - Don't say things like "from Raw_Data_Date_Wise" or "reading from table X"
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
                        return "I searched the data but couldn't find specific results for your query. Could you try rephrasing your question? For example: 'Compare media and organic units sold for week 25' or 'Show me weekly sales trends for the last 5 weeks'."
                else:
                    # If query failed, try to provide helpful debugging info
                    error_msg = query_result.get("error", "Unknown error")
                    if "no such column" in error_msg.lower():
                        available_tables = list(self.data_summary['tables'].keys()) if self.data_summary else []
                        return f"I tried to analyze your request but had trouble finding the right data columns. Available datasets: {', '.join(available_tables)}. Could you try asking: 'What columns are available?' or rephrase your question with different terms?"
                    else:
                        return "I encountered a technical issue while analyzing your data. Could you try rephrasing your question? For media vs organic comparisons, try: 'Compare media and organic performance for week 25'"
            else:
                # If no SQL query found, provide more specific guidance
                if any(word in user_question.lower() for word in ['weather', 'news', 'time', 'date', 'recipe', 'movie', 'music', 'sports', 'politics']):
                    return "I focus on business data analysis. I can help with questions like: 'Compare media and organic sales for week 25', 'Show weekly sales trends', or 'Which products performed best last week'."
                else:
                    # Try to give more specific guidance based on their question
                    if any(word in user_question.lower() for word in ['compare', 'comparison', 'vs', 'versus']):
                        return "I can help with comparisons! Try asking: 'Compare media and organic units sold for week 25' or 'Compare sales performance across different weeks'. What specific metrics would you like to compare?"
                    elif any(word in user_question.lower() for word in ['media', 'organic']):
                        return "I can analyze media vs organic performance! Try: 'What were the media and organic units sold in week 25?' or 'Compare MSV and OSV for last week'. What specific week are you interested in?"
                    elif any(word in user_question.lower() for word in ['week', 'weekly']):
                        return "I can analyze weekly trends! Try: 'Show me sales by week' or 'Compare week 24 vs week 25 performance'. Which weeks would you like to compare?"
                    else:
                        return ai_response
            
        except Exception as e:
            return "I had trouble processing your request. For media vs organic analysis, try: 'Compare media and organic performance for week 25'. For weekly comparisons, try: 'Show sales trends by week'. What specific analysis would you like?"

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
        <h1>🔐 Admin Access</h1>
        <p>Secure data management portal</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation bar at top
    col1, col2, col3 = st.columns([2, 2, 4])
    with col1:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
    with col2:
        if st.button("🌱 Go to Chatbot", use_container_width=True):
            st.session_state.current_page = "chatbot"
            st.rerun()
    
    st.markdown("---")
    
    with st.form("admin_login"):
        st.header("🔑 Authentication Required")
        password = st.text_input("Admin Password", type="password", placeholder="Enter your secure password")
        submitted = st.form_submit_button("Access Admin Panel", use_container_width=True)
        
        if submitted:
            if password and check_admin_password(password):
                st.session_state.admin_logged_in = True
                st.session_state.current_page = "admin_panel"
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

def admin_panel():
    """Admin panel for data management"""
    st.markdown("""
    <div class="admin-header">
        <h1>👨‍💼 Admin Control Panel</h1>
        <p>Data Management & System Configuration</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation bar at top
    col1, col2, col3, col4 = st.columns([2, 2, 1, 3])
    with col1:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
    with col2:
        if st.button("🌱 Go to Chatbot", use_container_width=True):
            st.session_state.current_page = "chatbot"
            st.rerun()
    with col3:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.session_state.current_page = "home"
            st.rerun()
    
    st.markdown("---")
    
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
        After uploading data, commit the <code>data/</code> folder to GitHub for persistence.
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
                if st.button("Process Data", use_container_width=True, type="primary"):
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
        <h1>🌱 KRISPR AI Analyst</h1>
        <p>Fresh insights from your business data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation bar at top
    col1, col2, col3, col4 = st.columns([2, 1, 1, 4])
    with col1:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
    with col2:
        if st.button("🔐 Admin", use_container_width=True):
            st.session_state.current_page = "admin_login"
            st.rerun()
    with col3:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.input_key += 1
            st.rerun()
    
    st.markdown("---")
    
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
    
    # Display chat history
    for i, chat in enumerate(st.session_state.chat_history):
        st.markdown(f"""
        <div class="user-message">
            <strong>💬 You:</strong> {chat['user']}
        </div>
        <div class="ai-message">
            <strong>🌱 KRISPR AI:</strong><br>{chat['ai']}
        </div>
        """, unsafe_allow_html=True)
    
    # User input with form for Enter key support
    with st.form(key="chat_form", clear_on_submit=True):
        user_question = st.text_input(
            "Search your business data:", 
            placeholder="Ask about products, sales, performance, weekly trends...",
            key=f"user_input_{st.session_state.input_key}"
        )
        
        # Centered submit button
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            submitted = st.form_submit_button("Send", type="primary", use_container_width=True)
    
    # Handle form submission (Enter key or button click)
    if submitted and user_question:
        with st.spinner("🧠 Analyzing your data..."):
            ai_response = st.session_state.chatbot.get_ai_response(user_question)
            st.session_state.chat_history.append({
                "user": user_question,
                "ai": ai_response
            })
            # Clear input by incrementing key
            st.session_state.input_key += 1
        st.rerun()

def home_page():
    """Enhanced home page with fresh design"""
    st.markdown("""
    <div class="main-header">
        <h1>🌱 KRISPR Digital Analyst</h1>
        <p>AI-powered insights for sustainable business growth</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Two column layout for features
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="home-feature">
                <h3>🤖 AI Business Analyst</h3>
                <p>Get instant insights from your business data with natural language queries</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Start Analysis", use_container_width=True, type="primary", key="chatbot_btn"):
            st.session_state.current_page = "chatbot"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="home-feature">
                <h3>📊 Data Management</h3>
                <p>Upload and manage your business datasets securely</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Admin Access", use_container_width=True, key="admin_btn"):
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
    
    # Navigation in sidebar
    with st.sidebar:
        st.markdown("<h2 style='color: #2e7d32; text-align: center; margin-bottom: 2rem;'>🧭 Navigation</h2>", unsafe_allow_html=True)
        
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
        
        if st.button("🌱 AI Analyst", use_container_width=True):
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
