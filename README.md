# Email-Assistant-using-Generative-AI

This project helps automate Gmail label creation, email classification, and workflow execution using **Python**, **Google Cloud Gmail API**, **NVIDIA NIM API**, and **[n8n](https://n8n.io/)**.

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone <your_repo_url>
cd <your_repo_name>
````

---

### 2. Create a Virtual Environment

Using **Conda**:

```bash
conda env create -f environment.yml
python -m ipykernel install --user --name=mail_asst --display-name "Python (mail_asst)"
```

This installs all dependencies and creates a Jupyter kernel named **Python (mail\_asst)**.

---

### 3. Google Cloud Setup (Free)

1. Create a [Google Cloud account](https://cloud.google.com/).
2. Create a **new project**.
3. Enable **Gmail API** for the project.
4. Configure **OAuth Consent Screen**:

   * Go to: **APIs & Services → OAuth Consent Screen**
   * Add yourself as a **Test User**.
5. Create **OAuth credentials**:

   * Type: **Web Application**
   * Save **Client ID** and **Client Secret**
   * Add redirect URIs (e.g., `http://localhost:8080`)
6. Ensure your app requests the required Gmail scopes:

   * `https://www.googleapis.com/auth/gmail.modify`
   * `https://www.googleapis.com/auth/gmail.labels`

---

### 4. Configuration Files

Create a folder named `config/` with the following:

#### `client_secret.json`

```json
{
  "web": {
    "client_id": "<your client id>",
    "project_id": "<your project id>",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "<your client secret>",
    "redirect_uris": [
      "<your redirect URIs>"
    ]
  }
}
```

#### `config.env`

```env
EMAIL="your_email@example.com"
```

#### `nvidia_token.env`

```env
NVIDIA_API_TOKEN="your_nvidia_nim_api_token"
```

> 🔑 Get the NVIDIA API token from [NVIDIA NIM](https://build.nvidia.com/) (free).

---

### 5. Generate Tokens & Create Labels

Run the Jupyter notebooks in order:

1. **`generate_token.ipynb`** → Generates Gmail OAuth token.
2. **`create_labels.ipynb`** → Creates Gmail labels with hierarchy.

---

### 6. Install n8n for Workflow Automation

#### 🖥 macOS/Linux

```bash
brew install node   # installs Node.js and npm | install brew if its not installed already
npm install -g n8n
```

#### 🖥 Windows

1. Download & install **Node.js (LTS)** from [nodejs.org](https://nodejs.org/).
   (This also installs `npm`.)
2. Open **Command Prompt** or **PowerShell**, then run:

   ```bash
   npm install -g n8n
   ```

---

### 7. Import & Configure Workflow

* Import the provided **n8n workflow JSON**.
* Update:

  * **Gmail credentials** (OAuth tokens).
  * **Email ID** inside nodes.
  * **Paths** for Python script execution.
* Save and activate the workflow.

---

## ✅ Summary of Features

* Automates Gmail **label creation**:

  * `Job Update` parent with children:

    * Applied
    * Interview
    * Rejected
    * etc.
  * Top-level: `Meet Request`, `Requires Attention`
* Uses Gmail API with OAuth2 (idempotent).
* Integrates with **NVIDIA NIM** for AI-powered classification.
* Executes scalable workflows via **n8n**.

---

## 📌 Notes

* Google Cloud usage is **free** for Gmail API + OAuth.
* Tokens are stored locally in `token.json`.
* Re-running label creation is safe (no duplicates).

---

## 🛠 Tech Stack

* **Python** (Gmail API + automation scripts)
* **LangGraph** (AI workflow orchestration)
* **Conda** (environment & dependencies)
* **Jupyter** (setup scripts)
* **Google Cloud** (Gmail API, OAuth)
* **NVIDIA NIM API** (AI classification)
* **n8n** (Event trigger and workflow)

```
```
