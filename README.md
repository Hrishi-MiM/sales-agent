# AI Sales Agent

This project sets up an AI-driven sales agent that can make automated calls and interact with clients using specified names and numbers.

## Setup Instructions

### 1. Clone the Repository
First, clone the repository to your local machine:

```bash
git clone https://github.com/Hrishi-MiM/sales-agent.git
cd sales-agent
```

### 2. Create and Activate the Virtual Environment

#### On Windows:
```bash
python -m venv env
```

#### On Linux:
```bash
python3 -m venv env
```

Once the environment is created, activate it.

#### To activate the virtual environment:

##### Windows:
```bash
env\Scripts\activate
```

##### Linux:
```bash
source env/bin/activate
```

### 3. Install Dependencies

With the virtual environment activated, install the required packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

1. Rename `sample_env.txt` to `.env`:
   ```bash
   mv sample_env.txt .env
   ```

2. Open the `.env` file and add your credentials for Twilio or any other services required by the project.

### 5. Run the Server

Start the server by running the following command:

```bash
python app.py
```

### 6. Set Up Ngrok

If Ngrok is not already installed, download it from the [Ngrok website](https://ngrok.com/download).

1. Start another terminal.
2. Run Ngrok to expose your local server to the web:

```bash
ngrok http http://127.0.0.1:8000
```

Ngrok will provide a forwarding URL (like `http://<ngrok_link>`) that you'll use in the next step.

### 7. Trigger an AI Call

In a different terminal, make a POST request using `curl` to trigger the AI call.

```bash
curl -X POST '<ngrok_link>/make-ai-call' \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_phone_number=<number_with_extension>" \
  -d "client_name=<client_name>"
```

- Replace `<ngrok_link>` with the link provided by Ngrok.
- Replace `<number_with_extension>` with the client’s phone number (e.g., `+11234567890`).
- Replace `<client_name>` with the client’s name (e.g., `John Doe`).

### Example Curl Command

```bash
curl -X POST 'http://12345678.ngrok.io/make-ai-call' \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_phone_number=+11234567890" \
  -d "client_name=John"
```

Upon running the command, the AI Sales Agent will place a call to the specified number and address the client by the provided name.

---

### Troubleshooting

- If the server does not start, ensure you have the correct Python version and all dependencies installed.
- For Ngrok-related issues, verify that the Ngrok link is correct and accessible from the outside network.
