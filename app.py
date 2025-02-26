import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import json
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_API_KEY)

# Set page configuration
st.set_page_config(
    page_title="Smart Converter",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with dark/light theme compatibility
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: var(--text-color);
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        color: var(--text-color);
    }
    .result-container {
        background-color: rgba(128, 128, 128, 0.1);
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    .chat-container {
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .stTextInput, .stSelectbox {
        color: var(--text-color);
    }
</style>
""", unsafe_allow_html=True)

# Application title
st.sidebar.markdown("<div class='main-header'>Smart Converter</div>", unsafe_allow_html=True)

# API functions
def get_gemini_response(prompt):
    """Use Gemini AI to get responses"""
    if not GEMINI_API_KEY:
        st.sidebar.warning("⚠️ Gemini API key not set. Using fallback mode.")
        return handle_conversion_fallback(prompt)
    
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Generate response
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error with Gemini API: {e}")
        return handle_conversion_fallback(prompt)

def get_currency_rates():
    """Get real-time currency rates using a free API"""
    CURRENCY_API_URL = "https://open.er-api.com/v6/latest/USD"
    
    try:
        response = requests.get(CURRENCY_API_URL)
        data = response.json()
        if data["result"] == "success":
            rates = data["rates"]
            rates["timestamp"] = data["time_last_update_utc"]
            return rates
        else:
            raise Exception("Failed to get currency rates")
    except Exception as e:
        st.warning(f"⚠️ Could not fetch real-time currency rates: {e}")
        return {
            "USD": 1.0, "EUR": 0.93, "GBP": 0.79, "JPY": 150.34,
            "CAD": 1.35, "AUD": 1.53, "CNY": 7.21, "INR": 83.12, 
            "PKR": 278.50, "timestamp": "Using cached rates (may not be current)"
        }

def handle_conversion_fallback(prompt):
    """Fallback function for when API fails or is not available"""
    words = prompt.lower().split()
    result = ""
    
    if "meter" in prompt and "centimeter" in prompt:
        for i, word in enumerate(words):
            if word.replace('.', '', 1).isdigit():
                value = float(word)
                if "meter" in prompt and "centimeter" in prompt:
                    result = f"{value} meters = {value * 100} centimeters"
                break
    elif "dollar" in prompt or "usd" in prompt:
        for i, word in enumerate(words):
            if word.replace('.', '', 1).isdigit():
                value = float(word)
                if "euro" in prompt or "eur" in prompt:
                    result = f"{value} USD ≈ {value * 0.93} EUR"
                elif "pkr" in prompt or "rupee" in prompt:
                    result = f"{value} USD ≈ {value * 278.50} PKR"
                break
    
    if not result:
        result = "I couldn't process this conversion. Please try using the selection interface."
        
    return result

# Function to create prompt for the AI model
def create_ai_prompt(text):
    return f"""Convert {text}. Respond only with the converted value and units, nothing else. 
    Format: [value] [unit]. Example: '5 meters' or '10.5 USD'"""

# Sidebar for converter selection
st.sidebar.markdown("<div class='sub-header'>Choose Converter</div>", unsafe_allow_html=True)
converter_type = st.sidebar.radio(
    "Converter Type",
    ["Unit Converter", "Currency Converter"]
)

# Main content area
st.markdown("<div class='main-header'>Smart Converter</div>", unsafe_allow_html=True)

# Create tabs for different conversion methods
tab1, tab2 = st.tabs(["Chat Interface", "Selection Interface"])

# Chat interface (Primary)
with tab1:
    st.markdown("<div class='sub-header'>Convert with Natural Language</div>", unsafe_allow_html=True)
    st.markdown("<div class='chat-container'>Ask for any conversion in natural language like:<br>'Convert 5 meters to feet' or '100 USD to EUR'</div>", unsafe_allow_html=True)
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Get user input
    if prompt := st.chat_input("Type your conversion request..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process with Gemini AI
        with st.chat_message("assistant"):
            with st.spinner("Getting latest conversion data..."):
                # Create AI prompt and get response
                ai_prompt = create_ai_prompt(prompt)
                response = get_gemini_response(ai_prompt)
                
                # Display the response
                st.markdown(f"<div class='result-container'>{response}</div>", unsafe_allow_html=True)
                
                # Add to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})

# Selection interface (Secondary)
with tab2:
    st.markdown("<div class='sub-header'>Convert with Selection</div>", unsafe_allow_html=True)
    
    if converter_type == "Unit Converter":
        # Unit conversion categories
        category = st.selectbox(
            "Select Measurement Category",
            ["Length", "Weight", "Volume", "Temperature", "Area", "Time", "Data", "Speed"]
        )
        
        # Units based on category
        units = {
            "Length": ["Meter", "Kilometer", "Centimeter", "Millimeter", "Inch", "Foot", "Yard", "Mile"],
            "Weight": ["Gram", "Kilogram", "Milligram", "Pound", "Ounce", "Ton"],
            "Volume": ["Liter", "Milliliter", "Cubic Meter", "Gallon", "Quart", "Pint", "Cup"],
            "Temperature": ["Celsius", "Fahrenheit", "Kelvin"],
            "Area": ["Square Meter", "Square Kilometer", "Square Centimeter", "Square Inch", "Square Foot", "Acre", "Hectare"],
            "Time": ["Second", "Millisecond", "Minute", "Hour", "Day", "Week", "Month", "Year"],
            "Data": ["Byte", "Kilobyte", "Megabyte", "Gigabyte", "Terabyte", "Bit"],
            "Speed": ["Meter per Second", "Kilometer per Hour", "Mile per Hour", "Knot"]
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            from_unit = st.selectbox("From Unit", units[category])
            value = st.number_input("Enter Value", value=1.0, step=0.1)
        
        with col2:
            to_unit = st.selectbox("To Unit", units[category])
        
        if st.button("Convert Units"):
            with st.spinner("Getting latest conversion data..."):
                # Use Gemini AI to get the conversion
                prompt = f"Convert {value} {from_unit} to {to_unit}"
                ai_prompt = create_ai_prompt(prompt)
                result = get_gemini_response(ai_prompt)
                
                # Display result
                st.markdown(f"<div class='result-container'>{result}</div>", unsafe_allow_html=True)
    
    else:  # Currency Converter
        # Get real-time currency rates
        with st.spinner("Fetching latest exchange rates..."):
            rates = get_currency_rates()
            currencies = [k for k in rates.keys() if k != "timestamp"]
            last_updated = rates["timestamp"]
        
        st.caption(f"Exchange rates last updated: {last_updated}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            from_currency = st.selectbox("From Currency", currencies)
            amount = st.number_input("Enter Amount", value=1.0, step=0.1)
        
        with col2:
            to_currency = st.selectbox("To Currency", currencies)
        
        if st.button("Convert Currency"):
            try:
                # Use Gemini AI for currency conversion
                prompt = f"Convert {amount} {from_currency} to {to_currency}"
                ai_prompt = create_ai_prompt(prompt)
                result = get_gemini_response(ai_prompt)
                
                # Display result
                st.markdown(f"<div class='result-container'>{result}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error during conversion: {e}")

