"""
Publication Date Override Management Page for the Preorder Admin Dashboard.

This module provides the interface for managing publication date overrides.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# Initialize data service
from data.data_service import DataService

def show_override_management():
    """
    Display the publication date override management page.
    """
    # Initialize data service with test mode from session state
    test_mode = st.session_state.get('test_mode', False)
    data_service = DataService(test_mode=test_mode)
    
    st.subheader("Current Publication Date Overrides")
    
    with st.spinner("Loading override data..."):
        # Get current overrides
        overrides = data_service.get_pub_date_overrides()
        
        # Get preorder products for reference
        preorder_products = data_service.get_preorder_products()
        
        # Create a mapping of ISBN to product details
        isbn_to_product = {}
        for product in preorder_products:
            if product.get('barcode'):
                isbn_to_product[product['barcode']] = product
    
    # Convert overrides to DataFrame for display
    if overrides:
        override_data = []
        for isbn, corrected_date in overrides.items():
            # Get product information if available
            product = isbn_to_product.get(isbn, {})
            title = product.get('title', 'Unknown')
            original_date = product.get('pub_date', 'Unknown')
            
            override_data.append({
                'ISBN': isbn,
                'Title': title,
                'Original Date': original_date,
                'Corrected Date': corrected_date
            })
        
        override_df = pd.DataFrame(override_data)
        
        # Display current overrides
        st.dataframe(override_df, use_container_width=True)
        
        # Add options to edit or delete overrides
        if st.button("Delete Selected Overrides"):
            st.warning("Delete functionality not yet implemented")
    else:
        st.info("No publication date overrides found.")
    
    # Add new override section
    st.subheader("Add or Update Override")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Option to select from existing preorder products
        st.subheader("Select Product")
        
        # Create a list of products with title and ISBN
        product_options = []
        for product in preorder_products:
            if product.get('barcode'):
                product_options.append({
                    'label': f"{product['title']} (ISBN: {product['barcode']})",
                    'value': product['barcode']
                })
        
        # Sort by title
        product_options.sort(key=lambda x: x['label'])
        
        # Add a search box for products
        search_term = st.text_input("Search Products", "")
        
        # Filter product options based on search term
        if search_term:
            filtered_options = [opt for opt in product_options 
                              if search_term.lower() in opt['label'].lower()]
        else:
            filtered_options = product_options
        
        # Display a limited number of options with pagination
        page_size = 10
        total_pages = max(1, (len(filtered_options) + page_size - 1) // page_size)
        
        # Initialize page number in session state if it doesn't exist
        if 'override_page' not in st.session_state:
            st.session_state.override_page = 0
            
        # Pagination controls
        col_prev, col_page, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if st.button("← Previous", key="prev_page"):
                st.session_state.override_page = max(0, st.session_state.override_page - 1)
                
        with col_page:
            st.write(f"Page {st.session_state.override_page + 1} of {total_pages}")
            
        with col_next:
            if st.button("Next →", key="next_page"):
                st.session_state.override_page = min(total_pages - 1, st.session_state.override_page + 1)
        
        # Get the current page of options
        start_idx = st.session_state.override_page * page_size
        end_idx = min(start_idx + page_size, len(filtered_options))
        current_page_options = filtered_options[start_idx:end_idx]
        
        # Display radio buttons for product selection
        selected_isbn = None
        if current_page_options:
            options_dict = {opt['value']: opt['label'] for opt in current_page_options}
            selected_isbn = st.radio(
                "Select a product to override:",
                options=options_dict.keys(),
                format_func=lambda x: options_dict[x],
                key="product_selector"
            )
        else:
            st.info("No products match your search.")
        
        # Manual ISBN entry option
        st.subheader("Or Enter ISBN Manually")
        manual_isbn = st.text_input("ISBN", "")
        
        # Determine which ISBN to use
        isbn_to_use = selected_isbn if selected_isbn else manual_isbn
        
        # Show current publication date if available
        if isbn_to_use and isbn_to_use in isbn_to_product:
            product = isbn_to_product[isbn_to_use]
            st.info(f"Current publication date: {product.get('pub_date', 'Unknown')}")
        
        # Show current override if available
        if isbn_to_use and isbn_to_use in overrides:
            st.success(f"Current override: {overrides[isbn_to_use]}")
    
    with col2:
        st.subheader("Set New Publication Date")
        
        # Date input for new publication date
        default_date = datetime.now().date() + timedelta(days=30)
        new_pub_date = st.date_input(
            "New Publication Date",
            value=default_date,
            min_value=datetime.now().date() - timedelta(days=365),  # Allow dates up to a year in the past
            max_value=datetime.now().date() + timedelta(days=3650)   # Allow dates up to 10 years in the future
        )
        
        # Format the date as YYYY-MM-DD
        formatted_date = new_pub_date.strftime("%Y-%m-%d")
        
        # Add notes field
        override_notes = st.text_area("Notes (optional)", "")
        
        # Update button
        if st.button("Update Publication Date"):
            if isbn_to_use:
                # Confirm the change
                st.warning(f"Are you sure you want to override the publication date for ISBN {isbn_to_use} to {formatted_date}?")
                
                col_confirm, col_cancel = st.columns([1, 1])
                
                with col_confirm:
                    if st.button("Confirm", key="confirm_override"):
                        # Update the override
                        success = data_service.update_pub_date_override(isbn_to_use, formatted_date)
                        
                        if success:
                            st.success(f"Successfully updated publication date for ISBN {isbn_to_use}")
                            # Refresh the page to show the updated override
                            st.experimental_rerun()
                        else:
                            st.error("Failed to update publication date")
                
                with col_cancel:
                    if st.button("Cancel", key="cancel_override"):
                        pass  # Do nothing, the form will remain as is
            else:
                st.error("Please select a product or enter an ISBN")
    
    # Publication Date Issues Section
    st.subheader("Publication Date Issues")
    
    # Calculate statistics about publication dates
    future_pub_dates = []
    past_pub_dates = []
    missing_pub_dates = []
    malformed_pub_dates = []
    today = datetime.now().date()
    
    for product in preorder_products:
        pub_date_str = product.get('pub_date')
        
        if not pub_date_str:
            missing_pub_dates.append(product)
            continue
            
        try:
            pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d').date()
            
            if pub_date > today:
                future_pub_dates.append(product)
            else:
                past_pub_dates.append(product)
                
        except ValueError:
            malformed_pub_dates.append(product)
    
    # Create tabs for different issue types
    issue_tabs = st.tabs(["Past Dates", "Missing Dates", "Malformed Dates"])
    
    with issue_tabs[0]:
        st.markdown(f"**{len(past_pub_dates)} Products with Past Publication Dates**")
        
        if past_pub_dates:
            past_dates_data = []
            for product in past_pub_dates:
                past_dates_data.append({
                    'ISBN': product.get('barcode'),
                    'Title': product.get('title'),
                    'Publication Date': product.get('pub_date'),
                    'Days Past': (today - datetime.strptime(product.get('pub_date'), '%Y-%m-%d').date()).days
                })
            
            past_dates_df = pd.DataFrame(past_dates_data)
            
            # Sort by days past (descending)
            past_dates_df = past_dates_df.sort_values('Days Past', ascending=False)
            
            # Display table
            st.dataframe(past_dates_df, use_container_width=True)
            
            # Add option to batch update
            if st.button("Batch Update Selected to Future Date"):
                st.warning("Batch update functionality not yet implemented")
        else:
            st.info("No products with past publication dates.")
    
    with issue_tabs[1]:
        st.markdown(f"**{len(missing_pub_dates)} Products with Missing Publication Dates**")
        
        if missing_pub_dates:
            missing_dates_data = []
            for product in missing_pub_dates:
                missing_dates_data.append({
                    'ISBN': product.get('barcode'),
                    'Title': product.get('title'),
                    'Collections': ', '.join(product.get('collections', []))
                })
            
            missing_dates_df = pd.DataFrame(missing_dates_data)
            
            # Display table
            st.dataframe(missing_dates_df, use_container_width=True)
            
            # Add option to batch update
            if st.button("Set Default Dates for Selected"):
                st.warning("Batch update functionality not yet implemented")
        else:
            st.info("No products with missing publication dates.")
    
    with issue_tabs[2]:
        st.markdown(f"**{len(malformed_pub_dates)} Products with Malformed Publication Dates**")
        
        if malformed_pub_dates:
            malformed_dates_data = []
            for product in malformed_pub_dates:
                malformed_dates_data.append({
                    'ISBN': product.get('barcode'),
                    'Title': product.get('title'),
                    'Malformed Date': product.get('pub_date')
                })
            
            malformed_dates_df = pd.DataFrame(malformed_dates_data)
            
            # Display table
            st.dataframe(malformed_dates_df, use_container_width=True)
            
            # Add option to batch update
            if st.button("Fix Selected Dates"):
                st.warning("Date fixing functionality not yet implemented")
        else:
            st.info("No products with malformed publication dates.")