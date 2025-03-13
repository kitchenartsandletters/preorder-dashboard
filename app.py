#!/usr/bin/env python
"""
Preorder Admin Dashboard - Main Application

This is the main entry point for the Streamlit-based admin dashboard
for managing preorders, publication dates, and sales reporting.
"""
import os
import streamlit as st
from datetime import datetime

# Import components
from components.sidebar import render_sidebar
from components.header import render_header

# Import pages
from pages.dashboard import show_dashboard
from pages.preorder_management import show_preorder_management
from pages.override_management import show_override_management
from pages.approvals import show_approvals
from pages.reports import show_reports

# Configure the page
st.set_page_config(
    page_title="Preorder Admin Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set up session state for navigation if it doesn't exist
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'

def main():
    """Main function to render the dashboard"""
    # Initialize session state if needed
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'
    
    if 'test_mode' not in st.session_state:
        st.session_state.test_mode = True  # Default to test mode for easier initial setup
    
    # Render the header with title and user info
    render_header()
    
    # Render the sidebar navigation and get the selected page
    selected_page = render_sidebar()
    
    # Update the current page in session state
    if selected_page:
        st.session_state.current_page = selected_page
    
    # Display the appropriate page based on selection
    if st.session_state.current_page == 'dashboard':
        show_dashboard()
    elif st.session_state.current_page == 'preorder_management':
        show_preorder_management()
    elif st.session_state.current_page == 'override_management':
        show_override_management()
    elif st.session_state.current_page == 'approvals':
        show_approvals()
    elif st.session_state.current_page == 'reports':
        show_reports()
    
    # Add footer
    st.markdown("---")
    st.markdown(f"© {datetime.now().year} - Preorder Admin Dashboard v1.0.0")

if __name__ == "__main__":
    main()