#  AI University Calendar Manager

An autonomous Python-based AI assistant that manages my university schedule. It imports the official `.ics` schedule and continuously monitors my university inbox. Using Google's Gemini 2.5 Flash, it parses emails from professors to detect schedule changes, cancellations, or upcoming exams, and automatically updates my Google Calendar in real-time.

##  Features

- **Initial Schedule Import:** Reads the official university `.ics` file and uploads all base classes to Google Calendar with proper timezone handling (`Europe/Madrid`).
- **AI-Powered Inbox Monitoring:** Connects to the university Gmail account via OAuth2, reading incoming emails and extracting unstructured data.
- **Smart Subject Identification:** Uses predefined mapping dictionaries to translate cryptic course codes (e.g., `C2.218.20606`) or professor email addresses into clean, readable subject names.
- **Automated Calendar Updates:** 
  - 🟡 **Changes/Make-up classes:** Added as 1.5-hour yellow events.
  - 🔴 **Exams:** Added as 2-hour red events for high visibility.
  - ⚠️ **Cancellations:** Ignored in creation but logged for reference.
- **Duplicate Prevention:** Checks the calendar for existing events at the same exact time with matching titles before creating new ones.
- **Cloud Automation:** Deployed on a free-tier Google Cloud Compute Engine VM (Debian), running autonomously every hour via a `cron` job.

##  Tech Stack

- **Language:** Python 3
- **AI Model:** Google Gemini 2.5 Flash (`google-genai` SDK)
- **Integrations:** Google Calendar API, Gmail API (OAuth2 Authentication)
- **Infrastructure:** Google Cloud Compute Engine (e2-micro), Linux `cron`
- **Libraries:** `google-api-python-client`, `icalendar`, `python-dotenv`

##  Project Structure

- `auth_google.py`: Handles OAuth2 authentication and token generation for Gmail and Calendar APIs.
- `import_ics.py`: Parses the initial university `.ics` file and uploads the base schedule.
- `manager_ai.py`: The core AI script. Fetches recent emails, prompts Gemini to extract JSON data, and updates Google Calendar.
- `limpiar_duplicados.py`: An interactive CLI tool to safely find and delete duplicated calendar events based on start times.
- `.env`: Stores the `GEMINI_API_KEY` (Not pushed to version control).
- `credentials.json` & `token.json`: Google OAuth2 secrets (Not pushed to version control).

##  Setup & Installation (Local)

**1. Clone the repository**
```bash
git clone [https://github.com/nickos07/ai-calendar-manager.git](https://github.com/nickos07/ai-calendar-manager.git)
cd ai-calendar-manager

```

**2. Install dependencies**

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib google-genai python-dotenv icalendar

```

**3. Configure Credentials**

* Go to Google Cloud Console, create a project, and enable **Gmail API** and **Google Calendar API**.
* Download your Desktop App OAuth 2.0 Client ID and save it in the root folder as `credentials.json`.
* Create a `.env` file in the root directory and add your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here

```



**4. Authenticate**
Run the authentication script. A browser window will open asking you to log into your university Google account.

```bash
python auth_google.py

```

This will generate a `token.json` file.

**5. Import Base Schedule (Optional)**
Place your university `.ics` file in the root folder (e.g., `mi_horario.ics`) and run:

```bash
python import_ics.py

```

##  Usage & Cloud Deployment

To run the AI manager manually and check for recent emails:

```bash
python manager_ai.py

```

**Deploying to Google Cloud (24/7 Automation):**

1. Spin up an `e2-micro` VM instance on Google Cloud Compute Engine.
2. SSH into the server and install Python/pip.
3. Upload all scripts, `.env`, `credentials.json`, and the generated `token.json` to the VM.
4. Open the cron editor (`crontab -e`) and add the following job to run the script automatically every hour:

```bash
0 * * * * cd /path/to/project && python3 manager_ai.py >> log_manager.txt 2>&1

```

The AI will now silently monitor your inbox and manage your calendar in the background!