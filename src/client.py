import streamlit as st
import requests

# Set page configuration
st.set_page_config(
    page_title="Bank Product Recommendation System",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stSelectbox {
        margin-bottom: 2rem;
    }
    .section-header {
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# Header with nice formatting
st.title("🏦 Bank Product Recommendation System")
st.markdown("---")

# Fetch customer IDs from the FastAPI endpoint
response = requests.get("http://127.0.0.1:8000/customers")
if response.status_code == 200:
    customer_ids = response.json().get("customer_ids", [])
else:
    st.error("Failed to fetch customer IDs")
    customer_ids = []

# Ensure customer_ids is not empty
if customer_ids:
    # Create two columns for layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Select customer ID from the list
        selected_customer_id = st.selectbox("Select Customer ID", customer_ids)
        
        # Button to get recommendation
        if st.button("Get Recommendation", type="primary"):
            with st.spinner("Generating recommendations..."):
                recommendation_response = requests.post(
                    f"http://127.0.0.1:8000/recommendation?customer_id={selected_customer_id}"
                )
                
                if recommendation_response.status_code == 200:
                    response_json = recommendation_response.json()
                    
                    if "recommendation" in response_json:
                        recommendation = response_json["recommendation"]
                        
                        # Extract relevant sections
                        sections = recommendation.split("Analysis:")[-1].split("Available Products:")[0]
                        final_recommendations = recommendation.split("Recommendation:")[-1]
                        
                        with col2:
                            # Display Analysis
                            st.markdown("### 📊 Financial Analysis")
                            st.markdown(sections)
                            
                            st.markdown("### 💡 Recommendations")
                            st.markdown(final_recommendations)
                            
                    else:
                        st.error("Key 'recommendation' not found in the response.")
                else:
                    st.error(f"Failed to get recommendation: {recommendation_response.status_code}")
else:
    st.warning("No customer IDs available to select.")

# Add footer
st.markdown("---")
st.markdown("🏢 Powered by Advanced Banking Analytics")