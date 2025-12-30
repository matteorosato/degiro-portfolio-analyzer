# Assets

This directory contains static assets for the application:

- **css/**: Custom CSS stylesheets
- **images/**: Images, icons, and logos

## Usage

To use custom CSS in your Streamlit app:

```python
import streamlit as st

# Load custom CSS
with open("assets/css/custom_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
```
