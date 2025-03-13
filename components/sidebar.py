"""
Sidebar navigation component for the Preorder Admin Dashboard.
"""
import streamlit as st
import os

def render_sidebar():
    """
    Renders the sidebar navigation and returns the selected page.
    
    Returns:
        str: The selected page identifier, or None if no new selection was made
    """
    with st.sidebar:
        # Header section with title (without external image)
        st.title("Preorder Admin")
        st.divider()

        # Navigation section
        st.subheader("Navigation")
        
        # Dashboard - Overview and summary
        if st.sidebar.button("📊 Dashboard", 
                           key="nav_dashboard", 
                           use_container_width=True,
                           type="primary" if st.session_state.current_page == 'dashboard' else "secondary"):
            return "dashboard"
        
        # Preorder Management - List and edit individual preorders
        if st.sidebar.button("📚 Preorder Management", 
                           key="nav_preorder_management", 
                           use_container_width=True,
                           type="primary" if st.session_state.current_page == 'preorder_management' else "secondary"):
            return "preorder_management"
        
        # Override Management - Manage publication date overrides
        if st.sidebar.button("📅 Override Management", 
                           key="nav_override_management", 
                           use_container_width=True,
                           type="primary" if st.session_state.current_page == 'override_management' else "secondary"):
            return "override_management"
        
        # Approvals - Review and process approval requests
        if st.sidebar.button("✅ Approvals", 
                           key="nav_approvals", 
                           use_container_width=True,
                           type="primary" if st.session_state.current_page == 'approvals' else "secondary"):
            return "approvals"
        
        # Reports - Generate and view reports
        if st.sidebar.button("📈 Reports", 
                           key="nav_reports", 
                           use_container_width=True,
                           type="primary" if st.session_state.current_page == 'reports' else "secondary"):
            return "reports"
        
        # Settings and information section
        st.divider()
        st.subheader("Settings")
        
        # Test mode toggle
        test_mode = st.sidebar.toggle("Test Mode (Use Sample Data)", value=True)
        st.session_state.test_mode = test_mode
        
        if test_mode:
            st.sidebar.info("📌 Test mode active - using sample data")
        
        # Environment info
        st.sidebar.divider()
        environment = os.getenv("ENVIRONMENT", "development")
        st.sidebar.caption(f"Environment: {environment}")
        st.sidebar.caption("Version 1.0.0")
        
    return None  # No new selection