from flask import Flask, request, Response, redirect, url_for, send_file
import os
import logging
from twilio.rest import Client
import openai
from dotenv import load_dotenv
from app.elevenlabs import generate_voice
import pandas as pd
from datetime import datetime

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

app = Flask(__name__)

# Load environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_phone_number = os.getenv("TWILIO_PHONE_NUMBER")

# Initialize the Twilio client
twilio_client = Client(account_sid, auth_token)

# Global variables to store the current customer information and conversation state
current_customer_name = None
current_customer_phone = None
previous_question = None
sales_contact_requested = False

# Function to generate voice response using ElevenLabs API


@app.route("/make-ai-call", methods=['POST'])
def make_ai_call():
    global current_customer_name, current_customer_phone, previous_question, sales_contact_requested
    client_phone_number = request.form.get('client_phone_number')
    client_name = request.form.get('client_name')
  
    current_customer_name = client_name
    current_customer_phone = client_phone_number
    previous_question = None  # Reset the conversation state
    sales_contact_requested = False  # Reset the sales contact request flag

    try:
        call = twilio_client.calls.create(
            from_=from_phone_number,
            to=client_phone_number,
            url=f"http://{request.host}/greet-client"
        )
        logging.info(f"Call initiated: {client_phone_number}, SID: {call.sid}")
        return {"call_sid": call.sid}, 200
    except Exception as e:
        logging.error(f"Error initiating call: {e}")
        return {"error": str(e)}, 500

@app.route("/greet-client", methods=['GET', 'POST'])
def greet_client():
    global current_customer_name
    greeting_text = (
        f"Hello {current_customer_name}, this is Ginie from Army of Me. I hope you're doing well today! "
        "We provide a range of accounting and financial services, including bookkeeping, tax preparation, payroll processing, and more. "
        "Is there a particular service you are interested in, or would you like an overview of our offerings?"
    )
    audio_url = generate_voice(greeting_text)

    response = f"""
    <Response>
        <Play>{audio_url}</Play>
        <Gather input="speech" action="/gather-input" method="POST" timeout="15" speechTimeout="auto"/>
    </Response>
    """
    logging.info(f"Greeting and service intro played for: {current_customer_name}")
    return Response(response, mimetype='text/xml')

@app.route("/gather-input", methods=['GET', 'POST'])
def gather_input():
    global current_customer_phone, current_customer_name, previous_question, sales_contact_requested

    if request.method == 'POST':
        user_input = request.form.get('SpeechResult')
        
        if user_input and user_input.strip():
            logging.info(f"User input received: {user_input}")

            # Check if the customer is satisfied or has said "thank you"
            if "thank you" in user_input.lower() or "thanks" in user_input.lower():
                logging.info("Customer is satisfied. Ending call.")
                return respond_and_end_call("Thank you for your time!")

            # Determine AI response based on conversation context
            if previous_question == "sales_contact_permission" and sales_contact_requested:
                # If already asked for consent and user has additional queries
                ai_response = generate_follow_up_response(user_input)
            elif previous_question == "sales_contact_permission" and not sales_contact_requested:
                ai_response, consent_given = handle_sales_contact_consent(user_input)
                if consent_given:
                    log_customer_consent(current_customer_name, current_customer_phone)
                    sales_contact_requested = True
                else:
                    logging.info(f"Customer declined consent: {current_customer_name}")
                    sales_contact_requested = False
            else:
                ai_response, service_name = generate_sales_response(user_input)
                # Always update the previous question for context, regardless of overview or specific service
                previous_question = "sales_contact_permission"
                ai_response += f" If you have any other queries about the services, then our Sales Person can connect with you. Is that okay for you, {current_customer_name}?"

            logging.info(f"AI response generated: {ai_response}")

            # Convert the AI response to audio
            audio_url = generate_voice(ai_response)

            response = f"""
            <Response>
                <Play>{audio_url}</Play>
                <Gather input="speech" action="/gather-input" method="POST" timeout="15" speechTimeout="auto"/>
            </Response>
            """
            return Response(response, mimetype='text/xml')

    # If no input is received, repeat the request for input
    response = """
    <Response>
        <Gather input="speech" action="/gather-input" method="POST" timeout="15" speechTimeout="auto"/>
    </Response>
    """
    return Response(response, mimetype='text/xml')

@app.route("/output_audio.mp3", methods=['GET'])
def serve_audio():
    try:
        file_path = os.path.join(os.getcwd(), "output_audio.mp3")
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='audio/mpeg')
        else:
            logging.error("File not found: output_audio.mp3")
            return "File not found", 404
    except Exception as e:
        logging.error(f"Error serving audio file: {e}")
        return str(e), 500


def generate_sales_response(user_input):
    """Generate a sales response based on the input and call flow"""
    # Define the services and their details
    services = {
        "bookkeeping": "We offer comprehensive bookkeeping and accounting services starting at $15 per hour, including managing accounts receivable and payable, credit card reconciliation, and year-end closings.",
        "financial statements": "We prepare accurate financial statements like Income Statements, Balance Sheets, and Cash Flow Statements to help you understand your financial position.",
        "auditing": "Our internal and external auditing services ensure your financial records' accuracy and compliance with regulations.",
        "tax preparation": "We provide tax services that meet all regulations while minimizing liabilities and offer strategies for future tax planning.",
        "payroll": "Our payroll services include wage calculations, tax withholdings, and timely salary payments while ensuring full compliance.",
        "management reporting": "We offer detailed management reporting and financial analysis to provide insights into your business performance."
    }

    service_name = None

    # Check if user wants an overview or a specific service
    if "overall" in user_input.lower() or "overview" in user_input.lower():
        # If user wants an overview of all services
        return "\n".join(services.values()), "overview"

    # Check if user is interested in a specific service
    for service, details in services.items():
        if service in user_input.lower():
            service_name = service
            return details, service_name

    # If no specific service is mentioned, provide a general response
    general_response = "Is there a particular service you are interested in, or would you like an overview of our offerings?"
    return general_response, None

def generate_follow_up_response(user_input):
    """Generate a follow-up response if the user has additional queries"""
    # Check if the user has more queries about services
    service_inquiry = ["more", "services", "anything else", "other services", "additional services"]
    if any(query in user_input.lower() for query in service_inquiry):
        return "We offer a range of services including bookkeeping, financial statements, tax preparation, payroll, and more. Do you have any specific questions about these services?"
    else:
        return "Thank you for your time! If you have any other queries, feel free to reach out to us."

def handle_sales_contact_consent(user_input):
    """Handle the customer's response to sales contact permission request"""
    positive_responses = ["yes", "sure", "okay", "fine", "cool", "alright", "no problem"]
    if any(response in user_input.lower() for response in positive_responses):
        return "Great! Our Sales Person will connect with you soon. Thank you!", True
    else:
        return "Thank you for your time! If you have any questions, feel free to reach out to us.", False

def respond_and_end_call(final_message):
    """Respond with a final message and immediately end the call"""
    audio_url = generate_voice(final_message)
    response = f"""
    <Response>
        <Play>{audio_url}</Play>
        <Hangup/>
    </Response>
    """
    return Response(response, mimetype='text/xml')

def log_customer_consent(customer_name, customer_phone):
    """Log customer consent in an Excel file"""
    try:
        # Define the Excel file path
        file_path = "customer_interest_log.xlsx"

        # Check if the file exists
        if os.path.exists(file_path):
            # Load the existing data
            df = pd.read_excel(file_path)
        else:
            # Create a new DataFrame if file doesn't exist
            df = pd.DataFrame(columns=["Customer Name", "Phone Number", "Consent Given", "Time"])

        # Add the new entry
        new_entry = {
            "Customer Name": customer_name,
            "Phone Number": customer_phone,
            "Consent Given": "Yes",
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)

        # Save the updated data back to the file
        df.to_excel(file_path, index=False)
        logging.info(f"Customer consent logged: {customer_name}")
    except Exception as e:
        logging.error(f"Error logging customer consent: {e}")


if __name__ == "__main__":
    app.run(port=8000)
