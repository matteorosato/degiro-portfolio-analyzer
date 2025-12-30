"""
Portfolio Analyzer - Main Entrypoint
DeGiro Portfolio Analyzer Application

This is the main entrypoint for the DeGiro Portfolio Analyzer multipage Streamlit application.
Navigate through pages using the sidebar to access different features.
"""
import streamlit as st

# Configure the main page
st.set_page_config(
    page_title="DeGiro Portfolio Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

# Main page content
st.write("# DeGiro Portfolio Analyzer 📊")

st.sidebar.success("Select a page above to get started.")

st.markdown(
    """
    Welcome to the **DeGiro Portfolio Analyzer**! This application helps you analyze 
    and manage your investment portfolio with powerful visualization and analysis tools.
    
    ### 📌 Features
    
    **👈 Select a page from the sidebar** to access different features:
    
    - **📈 Dashboard**: Overview of your portfolio performance and key metrics
    - **💹 Stock Split Calculator**: Calculate optimal stock splits for your investments
    - **🔗 Ticker Mapping**: Manage ISIN to ticker symbol mappings
    - **📊 Portfolio Analysis**: Detailed analysis of portfolio performance over time
    - **🎯 Type Split Analysis**: Analyze portfolio allocation by asset type
    
    ### 🚀 Getting Started
    
    1. Upload your DeGiro transaction CSV file
    2. Review and adjust ticker mappings if needed
    3. Explore your portfolio metrics and performance
    4. Use analysis tools to optimize your investment strategy
    
    ### 📖 Documentation
    
    - [Project README](https://github.com/your-repo/degiro-portfolio-analyzer)
    - [API Documentation](http://localhost:8000/docs)
    - [User Guide](docs/user-guide.md)
    
    ### 🛠️ Technical Stack
    
    This application follows Streamlit best practices for multipage apps:
    - **Structure**: Based on [cookiecutter-streamlit template](https://github.com/andymcdgeo/cookiecutter-streamlit)
    - **Pages**: Following [Streamlit multipage conventions](https://docs.streamlit.io/get-started/tutorials/create-a-multipage-app)
    - **Backend**: FastAPI with domain-driven architecture
    - **Frontend**: Streamlit with modular components
    """
)

st.info("💡 **Tip**: Make sure the backend API is running on http://localhost:8000 for full functionality.")
