# krispr-bi-chatbot
# KRISPR Business Intelligence Chatbot

A powerful AI-powered business intelligence chatbot that analyzes Excel data and provides insights through natural language queries.

## 🌟 Features

- **Excel Data Integration**: Upload and analyze Excel files (.xlsx, .xls)
- **AI-Powered Insights**: Natural language queries powered by OpenAI GPT
- **Interactive Visualizations**: Create charts and graphs dynamically
- **Real-time Analysis**: Get instant insights and recommendations
- **Auto-updating**: Supports future data updates in your files
- **Streamlit Web Interface**: User-friendly web application

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/krispr-bi-chatbot.git
   cd krispr-bi-chatbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser** and go to `http://localhost:8501`

### Streamlit Cloud Deployment

1. **Push your code to GitHub**
   - Create a new repository on GitHub
   - Push all files including `app.py` and `requirements.txt`

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select your repository
   - Choose `app.py` as the main file
   - Click "Deploy"

## 📊 How to Use

### Step 1: Configure API Key
- Enter your OpenAI API key in the sidebar
- The app will validate and confirm the connection

### Step 2: Upload Excel Data
- Click "Browse files" to upload your Excel file
- Supported formats: .xlsx, .xls
- The app will automatically analyze your data structure

### Step 3: Start Chatting
- Use the chat interface to ask questions about your data
- Examples:
  - "What are the main trends in sales?"
  - "Show me the top 5 products by revenue"
  - "What patterns do you see in customer behavior?"
  - "Create a visualization showing sales by region"

### Step 4: Use Quick Actions
- **Data Overview**: Get instant dataset summary
- **Suggest Visualizations**: AI recommendations for charts
- **Find Patterns**: Discover hidden insights in your data

### Step 5: Create Visualizations
- Use the visualization builder
- Choose chart types: bar, line, scatter, histogram
- Select columns for X/Y axes and color coding

## 🔧 File Structure

```
krispr-bi-chatbot/
│
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── .gitignore         # Git ignore file
└── data/              # Sample data folder (optional)
    └── sample.xlsx    # Your Excel files here
```

## 📈 Data Requirements

Your Excel file should:
- Have clear column headers in the first row
- Contain structured data (avoid merged cells)
- Include numeric data for analysis
- Be in .xlsx or .xls format

## 🔑 Environment Variables

For production deployment, you can set environment variables:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## 🛠️ Advanced Features

### Data Update Support
- The app automatically refreshes when you upload a new version
- No need to restart the application
- Maintains chat history during data updates

### Custom Visualizations
- Supports multiple chart types
- Interactive Plotly charts
- Color coding by categorical variables
- Responsive design

### AI Context Awareness
- The AI understands your specific data structure
- Provides context-aware insights
- Suggests relevant analysis based on your data types

## 🐛 Troubleshooting

### Common Issues

1. **"OpenAI API Error"**
   - Check your API key is valid
   - Ensure you have OpenAI credits available

2. **"Excel file not loading"**
   - Verify file format (.xlsx or .xls)
   - Check for merged cells or complex formatting
   - Ensure first row contains headers

3. **"Visualization not showing"**
   - Verify column selection
   - Check data types match chart requirements
   - Ensure data contains values

### Getting Help

- Check the error messages in the app
- Review your data format
- Verify API key configuration

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For support or questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review Streamlit and OpenAI documentation

---

**Built with ❤️ using Streamlit and OpenAI**
