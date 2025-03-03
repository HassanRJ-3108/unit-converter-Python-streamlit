import streamlit as st
import requests
import os
from dotenv import load_dotenv
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
    initial_sidebar_state="expanded",
)

# Application title
st.sidebar.title("Smart Converter")


# API functions
def get_gemini_response(prompt):
    """Use Gemini AI to get responses"""
    if not GEMINI_API_KEY:
        st.sidebar.warning("⚠️ Gemini API key not set. Using fallback mode.")

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text


def get_currency_rates():
    """Get real-time currency rates using a free API"""
    CURRENCY_API_URL = "https://open.er-api.com/v6/latest/USD"

    response = requests.get(CURRENCY_API_URL)
    data = response.json()
    rates = data["rates"]
    rates["timestamp"] = data["time_last_update_utc"]
    return rates


# Function to create prompt for the AI model
def create_ai_prompt(text):
    return f"""
    You are a Smart Unit Converter. Your job is to convert units and currencies accurately. 
    - Always return the converted value and its unit. 
    - Format the response as: [value] [unit] (Example: '5 meters' or '10.5 USD').
    - Do not introduce yourself or explain how you work. Focus only on conversion. 
    - If the user says "hi", respond with "Hello! I am a Smart Unit Converter. How can I assist you?"  
    - For all other inputs, return only the converted value and unit.  
    - If conversion is not possible, say "Invalid input. Please enter a valid unit or currency."  
    Convert: {text}
    """


# Sidebar for converter selection
st.sidebar.subheader("Choose Converter")
converter_type = st.sidebar.radio(
    "Converter Type", ["Unit Converter", "Currency Converter"]
)

# Main content area
st.title("Smart Converter")

# Create tabs for different conversion methods
tab1, tab2 = st.tabs(["Chat Interface", "Selection Interface"])

# Chat interface (Primary)
with tab1:
    st.subheader("Convert with Natural Language")
    st.info(
        "Ask for any conversion in natural language like:\n'Convert 5 meters to feet' or '100 USD to EUR'"
    )

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
                st.markdown(response)

                # Add to chat history
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

# Selection interface (Secondary)
with tab2:
    st.subheader("Convert with Selection")

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
                st.success(result)

    else:  # Currency Converter
        # Get real-time currency rates
        with st.spinner("Getting latest currency rates..."):
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
            # Use Gemini AI for currency conversion
            prompt = f"Convert {amount} {from_currency} to {to_currency}"
            ai_prompt = create_ai_prompt(prompt)
            result = get_gemini_response(ai_prompt)

            # Display result
            st.success(result)
