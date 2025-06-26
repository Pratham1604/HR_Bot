# HR Interview Confirmation Bot

This repository contains a Flask-based HR bot designed to automate the initial interview process for small to medium-sized companies, particularly in the Indian context. The bot uses Twilio for voice calls, Sarvam AI for speech-to-text transcription, and OpenAI's GPT-4 for natural language understanding and response generation.

## Features

*   **Automated Interview Process**: Conducts initial screening interviews with candidates.
*   **Dynamic Questioning**: Uses GPT-4 to adapt questions based on candidate responses for a natural conversation flow.
*   **Twilio Integration**: Handles voice calls and recordings for seamless communication.
*   **Speech-to-Text (STT)**: Transcribes candidate voice responses using Sarvam AI's speech recognition.
*   **Natural Language Understanding**: Processes responses intelligently using GPT-4.
*   **Comprehensive Data Collection**: Gathers essential information including:
    - Candidate availability and preferred interview times
    - Professional background and experience
    - Education details
    - Current employment status
    - Expected compensation
    - Notice period
    - Location preferences

## Setup Instructions

Follow these steps to get the HR bot up and running on your local machine.

### Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)
*   Twilio account with a phone number
*   OpenAI API key
*   Sarvam AI API key
*   `ngrok` (already included in this repository)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/hr_bot.git
cd hr_bot/conversation_bot
```

### 2. Install Dependencies

It's recommended to use a virtual environment:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install required Python packages
pip install -r requirments.txt
```

### 3. Environment Setup

Create a `.env` file in the project root with the following variables:

```env
TWILIO_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=your_twilio_phone_number
NGROK_DOMAIN=your_ngrok_domain
SARVAM_API_KEY=your_sarvam_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 4. Run the Flask Application

Start your Flask application:

```bash
python app5.py
```

The server will run on `http://127.0.0.1:5000` by default.

### 5. Expose Your Local Server

Use the included `ngrok` to create a public URL:

```bash
# Extract ngrok (if you haven't already)
tar -xvf ngrok-v3-stable-linux-amd64.tgz

# Run ngrok to expose port 5000
./ngrok http 5000
```

Copy the `https://` URL provided by ngrok for the next step.

### 6. Configure Twilio Webhook

1. Log in to your [Twilio Console](https://www.twilio.com/console)
2. Navigate to your phone number's configuration
3. Under "Voice & Fax", set the following:
   - When a call comes in: Webhook
   - URL: `https://your-ngrok-url/voice`
   - HTTP Method: POST

## Project Structure

```
.
├── conversation_bot/
│   ├── .venv/                      # Python virtual environment
│   ├── requirments.txt             # Python dependencies
│   ├── app5.py                     # Main Flask application
│   ├── static/                     # Static files
│   ├── data/                       # Data storage for responses
│   ├── templates/                  # Flask templates
│   ├── ngrok-v3-stable-linux-amd64.tgz # ngrok executable
│   └── .env                       # Environment variables
```

## Dependencies

Key dependencies include:
- Flask
- Twilio
- python-dotenv
- openai
- requests
- Other utilities (see `requirments.txt` for full list)

## Company Configuration

The bot includes configurable company information in `app5.py`. You can modify the `COMPANY_INFO` variable to match your organization's details:

- Company description
- Address
- Contact information
- Services offered
- Other relevant details

## Interview Flow

The bot conducts a structured interview covering:
1. Initial availability check
2. Personal and professional background
3. Educational qualifications
4. Work experience and current role
5. Notice period and salary expectations
6. Location preferences and work mode
7. Additional questions from the candidate

The conversation flow is managed by GPT-4, ensuring natural and contextually appropriate interactions.

## Error Handling

The system includes robust error handling for:
- Failed audio recordings
- Transcription issues
- API failures
- Connection problems

## Contributing

Feel free to submit issues and enhancement requests!
