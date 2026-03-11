# Inniverse AI Lab

This project is a Streamlit web application for interacting with Google's Gemini AI.

## Setup and Installation

### Prerequisites

- Python 3.8+

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd inniverse-ai
   ```

2. **Create a virtual environment:**
   - On Windows:
     ```bash
     python -m venv .venv
     ```
   - On macOS/Linux:
     ```bash
     python3 -m venv .venv
     ```

3. **Activate the virtual environment:**
   - On Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up your environment variables:**
   Create a file named `.env` in the root of the project and add your Gemini API key:
   ```
   GEMINI_API_KEY="your_api_key_here"
   ```

### Using Your Own API Key

Alternatively, you can enter your Gemini API key directly in the application. In the sidebar, you will find a "Gemini API Key" field where you can paste your key. This will override any environment variable you have set.

## Running the Application

Once you have completed the setup, you can run the application using the provided script:

- On Windows:
  ```bash
  run_app.bat
  ```
- On macOS/Linux:
  ```bash
  ./run_app.sh
  ```

This will start the Streamlit server, and you can access the application in your web browser at `http://localhost:8501`.
