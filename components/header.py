"""
Header component for the Preorder Admin Dashboard.
"""
import streamlit as st
from datetime import datetime

def render_header():
    """
    Renders the dashboard header with title and user information.
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Title and description based on current page
        if st.session_state.current_page == 'dashboard':
            st.title("Preorder Dashboard")
            st.subheader("Overview of preorder sales and publication status")
        elif st.session_state.current_page == 'preorder_management':
            st.title("Preorder Management")
            st.subheader("View and manage all preorder titles")
        elif st.session_state.current_page == 'override_management':
            st.title("Publication Date Overrides")
            st.subheader("Manage publication date overrides for titles")
        elif st.session_state.current_page == 'approvals':
            st.title("Preorder Approvals")
            st.subheader("Review and approve preorder titles for release")
        elif st.session_state.current_page == 'reports':
            st.title("Sales Reports")
            st.subheader("Generate and view preorder sales reports")
    
    with col2:
        # Show date and time 
        current_date = datetime.now().strftime("%B %d, %Y")
        st.markdown(f"**Date:** {current_date}")
        
        # Refresh button
        if st.button("🔄 Refresh Data", key="refresh_data"):
            st.experimental_rerun()
            
    # Divider
    st.divider()