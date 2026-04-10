# GitHub Change Notification Email Service

This repository is intended to support a webhook-driven email notification flow using GitHub, Azure App Service, and Azure Communication Services Email.

The main objective of this repo is:

When a user makes some change in a GitHub repository, an email is sent to a customer-defined recipient.

This README focuses on the business workflow, deployment model, webhook configuration, and validation steps needed to achieve that outcome.

---

## Table of Contents

1. [Objective](#objective)
2. [Expected Output](#expected-output)
3. [End-to-End Flow](#end-to-end-flow)
4. [Prerequisites](#prerequisites)
5. [Create Azure Communication Services](#create-azure-communication-services)
6. [Local Setup](#local-setup)
7. [Test & Validate Email Flow](#test--validate-email-flow)
8. [GitHub Webhook Integration](#github-webhook-integration)
9. [Deploy to Azure App Service](#deploy-to-azure-app-service)
10. [API Endpoints](#api-endpoints)
11. [Troubleshooting](#troubleshooting)

---

## Objective

The objective of this repository is to enable email notifications from GitHub repository activity.

The intended business flow is:

1. A developer or contributor makes a change in a GitHub repository.
2. GitHub raises an event for that change.
3. GitHub sends a webhook request to the deployed API.
4. The API uses Azure Communication Services to send an email.
5. The configured customer recipient receives the notification email.

Typical repository changes that may be used as triggers include:

- Push to a branch
- Pull request created, updated, merged, or closed
- Issue created or updated
- Release published
- Other repository events selected in GitHub webhook settings

## Expected Output

At the end of a successful setup, the expected output is:

- The API is deployed and reachable on Azure App Service.
- Azure Communication Services Email is configured with a valid sender.
- A customer-defined email address is configured as the notification recipient.
- A webhook is created in the GitHub repository.
- The webhook is configured for the required GitHub events.
- When a selected repository event occurs, the deployed service receives the request.
- An email notification is sent to the configured customer recipient.

## End-to-End Flow

The intended end-to-end workflow for this repo is:

```text
GitHub repository change
-> GitHub webhook event
-> Azure App Service hosted API
-> Azure Communication Services Email
-> Customer inbox
```

## Customer-Defined Recipient

The customer-defined recipient is the email address that should receive notifications when GitHub activity happens.

In this solution, that recipient is expected to be configured through:

- `ACS_EMAIL_DEFAULT_TO`

This keeps the notification target simple and makes the flow easy to validate.

## Prerequisites

- **Python 3.10+** (local development)
- **Azure Subscription** (for ACS and App Service)
- **Azure CLI** (for deployment)
- **curl or Postman** (for testing endpoints)
- **Git** (optional, for version control)

---

## Create Azure Communication Services

### Step 1: Create a Resource Group (optional, if you don't have one)

```bash
az group create \
  --name "myResourceGroup" \
  --location "eastus"
```

### Step 2: Create Azure Communication Services Resource

```bash
az communication create \
  --name "myEmailService" \
  --location "global" \
  --data-location "United States" \
  --resource-group "myResourceGroup"
```

**Output:** Save the connection string from the output (you'll need this later).

### Step 3: Get the Connection String

```bash
az communication show \
  --name "myEmailService" \
  --resource-group "myResourceGroup" \
  --query connectionString \
  --output tsv
```

**Copy the connection string** — you'll use it as `ACS_EMAIL_CONNECTION_STRING`.

### Step 4: Set Up Email Sender (Domain)

Azure Communication Services requires a verified sender domain. You have two options:

#### Option A: Use Azure Managed Domain (Quickest)

```bash
az communication email domain create \
  --name "AzureManagedDomain" \
  --email-service-name "myEmailService" \
  --resource-group "myResourceGroup"
```

Then get the sender email:

```bash
az communication email domain show \
  --name "AzureManagedDomain" \
  --email-service-name "myEmailService" \
  --resource-group "myResourceGroup" \
  --query "fromSenderDomain" \
  --output tsv
```

**Result:** You'll get an email like `donotreply@<xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx>.azurecomm.net`

**Set as `ACS_EMAIL_SENDER`** in your environment.

#### Option B: Use Your Own Domain

1. Go to [Azure Portal](https://portal.azure.com)
2. Search for "Email Communication Services"
3. Select your service → **Domains** → **+ Add Domain**
4. Follow the DNS verification steps
5. Once verified, use the domain as your `ACS_EMAIL_SENDER`

---

## Local Setup

### Step 1: Clone or Navigate to Project

```bash
cd c:\Workspace\AzureCommunicationservices\emailFunction
```

### Step 2: Create Virtual Environment

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Environment Variables

**PowerShell:**

```powershell
$env:ACS_EMAIL_CONNECTION_STRING = "your-connection-string-from-acs"
$env:ACS_EMAIL_SENDER = "donotreply@<xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx>.azurecomm.net"
$env:ACS_EMAIL_DEFAULT_TO = "your-email@example.com"
```

**Linux/macOS bash:**

```bash
export ACS_EMAIL_CONNECTION_STRING="your-connection-string-from-acs"
export ACS_EMAIL_SENDER="donotreply@<xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx>.azurecomm.net"
export ACS_EMAIL_DEFAULT_TO="your-email@example.com"
```

### Step 5: Run Locally

```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

**Expected Output:**

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

---

## Test & Validate Email Flow

### Health Check (No Auth Required)

Test if the app is running:

```bash
curl http://localhost:8000/health
```

**Expected Response:**

```json
{"status":"ok"}
```

---

### Send Email - Basic Test

**Request:**

```bash
curl -X POST "http://localhost:8000/email" \
  -H "Content-Type: application/json" \
  -d '{}'
```

This uses default settings from environment variables.

**Expected Response (Success - 200):**

```json
{
  "status": "sent",
  "messageId": "message-id-string"
}
```

**Expected Response (Missing Settings - 500):**

```json
{
  "detail": "Missing required settings: ACS_EMAIL_CONNECTION_STRING, ACS_EMAIL_SENDER, ACS_EMAIL_DEFAULT_TO."
}
```

---

### Send Email - Custom Recipient

**Request:**

```bash
curl -X POST "http://localhost:8000/email" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "recipient@example.com",
    "subject": "Test Email from App Service",
    "plainText": "Hello! This is a test message.",
    "html": "<html><body><h1>Hello!</h1><p>This is an HTML email.</p></body></html>"
  }'
```

**Expected Response (Success - 200):**

```json
{
  "status": "sent",
  "messageId": "unique-message-id"
}
```

---

### Send Email - From Postman

1. **Open Postman**
2. **Create new POST request** to `http://localhost:8000/email`
3. **Set Headers:**
   - `Content-Type: application/json`
4. **Set Body (raw JSON):**

```json
{
  "to": "test@example.com",
  "subject": "Test from Postman",
  "plainText": "This email was sent from Postman via the Email API"
}
```

5. **Click Send**

---

## Error Responses & Meanings

| Status | Meaning | Action |
|--------|---------|--------|
| **200** | Email sent successfully | Check your inbox |
| **400** | DomainNotLinked error | Verify sender domain is verified in ACS |
| **500** | Missing environment variables | Set ACS_EMAIL_CONNECTION_STRING, ACS_EMAIL_SENDER, ACS_EMAIL_DEFAULT_TO |
| **502** | ACS service connection error | Check connection string; verify internet connectivity |

---

## GitHub Webhook Integration

This repository is intended to use GitHub webhooks as the main trigger for sending notification emails.

When GitHub detects a selected event in the repository, it sends an HTTP request to the deployed service. The service then uses Azure Communication Services Email to notify the customer-defined recipient.

### How It Works

1. GitHub detects an event (e.g., PR opened, code pushed)
2. GitHub sends an HTTP POST to your webhook URL
3. Your service processes the event details
4. Your service sends an email to the configured customer recipient
5. The customer receives a notification about the repository change

### Setting Up GitHub Webhook

#### Step 1: Get Your App Service URL

```bash
# Your deployed API endpoint
https://eysampletrigger.azurewebsites.net/email
```

#### Step 2: Add Webhook to GitHub Repository

1. Go to your GitHub repository
2. Click **Settings** (top-right menu)
3. Click **Webhooks** (left sidebar)
4. Click **Add webhook** button
5. Fill in the following:

| Field | Value |
|-------|-------|
| **Payload URL** | `https://eysampletrigger.azurewebsites.net/email` |
| **Content type** | `application/json` |
| **Secret** | *(optional, for authentication)* |
| **SSL verification** | ☑ Enable SSL verification |

#### Step 3: Select Events to Trigger

Choose which GitHub events trigger the webhook:

- **Push events** — Code pushed to repository
- **Pull requests** — PR opened/closed/merged
- **Issues** — Issue opened/closed
- **Releases** — Release published
- **Discussions** — New discussion
- **Repository** — Repository created/deleted
- **All events** — *(everything)*

**Recommended starting point:** Check **Push events** and **Pull requests**

Choose event options based on what the customer expects to be notified about:

- Use `Push events` when every code change should trigger an email.
- Use `Pull requests` when the customer only wants review and merge workflow updates.
- Use `Releases` when only release-related changes matter.
- Use a custom event selection when notifications should be filtered.

#### Step 4: Save the Webhook

Click **Add webhook** to save.

---

### GitHub Webhook Payload Structure

When GitHub sends a webhook, it includes a JSON payload like this:

#### Push Event Example

```json
{
  "repository": {
    "name": "my-repo",
    "full_name": "username/my-repo",
    "html_url": "https://github.com/username/my-repo"
  },
  "pusher": {
    "name": "john-doe",
    "email": "john@example.com"
  },
  "ref": "refs/heads/main",
  "commits": [
    {
      "id": "abcd1234",
      "message": "Add new feature",
      "author": {
        "name": "John Doe",
        "email": "john@example.com"
      }
    }
  ]
}
```

#### Pull Request Event Example

```json
{
  "action": "opened",
  "pull_request": {
    "number": 42,
    "title": "Add dark mode",
    "user": {
      "login": "jane-smith"
    },
    "html_url": "https://github.com/username/my-repo/pull/42"
  },
  "repository": {
    "name": "my-repo",
    "full_name": "username/my-repo"
  }
}
```

---

### Update Email Endpoint to Process GitHub Events

Modify `app.py` to extract GitHub webhook data and format it as an email:

#### Option 1: Simple Approach (Use Existing /email Endpoint)

GitHub will POST to `/email`, but the payload structure differs. Add this helper function to `app.py`:

```python
def extract_github_event_info(payload: dict) -> dict:
    """Extract email details from GitHub webhook payload."""
    repo_name = payload.get("repository", {}).get("name", "unknown")
    event_type = payload.get("action", "event")
    
    if "pusher" in payload:  # Push event
        pusher = payload.get("pusher", {}).get("name", "Unknown")
        commits = payload.get("commits", [])
        commit_count = len(commits)
        summary = f"{pusher} pushed {commit_count} commit(s) to {repo_name}"
        details = "\n".join([f"  • {c['message']}" for c in commits[:5]])
        return {
            "subject": f"[GitHub] {repo_name} - Push by {pusher}",
            "plainText": f"{summary}\n\n{details}",
            "html": f"<h3>{summary}</h3><pre>{details}</pre>"
        }
    
    elif "pull_request" in payload:  # PR event
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number")
        pr_title = pr.get("title", "Untitled")
        pr_user = pr.get("user", {}).get("login", "Unknown")
        return {
            "subject": f"[GitHub] PR #{pr_number} {event_type.upper()}: {pr_title}",
            "plainText": f"PR #{pr_number} by {pr_user}: {pr_title}",
            "html": f"<h3>PR #{pr_number}: {pr_title}</h3><p>By: {pr_user}</p>"
        }
    
    elif "issue" in payload:  # Issue event
        issue = payload.get("issue", {})
        issue_number = issue.get("number")
        issue_title = issue.get("title", "Untitled")
        issue_user = issue.get("user", {}).get("login", "Unknown")
        return {
            "subject": f"[GitHub] Issue #{issue_number} {event_type.upper()}: {issue_title}",
            "plainText": f"Issue #{issue_number} by {issue_user}: {issue_title}",
            "html": f"<h3>Issue #{issue_number}: {issue_title}</h3><p>By: {issue_user}</p>"
        }
    
    return {"subject": "GitHub Event", "plainText": "GitHub webhook event"}
```

Then update the `/email` endpoint to handle both formats:

```python
@app.post("/email")
def send_email(payload: EmailRequest = None, **kwargs) -> dict:
    # Check if payload is GitHub webhook (raw dict POST)
    if payload is None and kwargs:
        payload_dict = kwargs
        email_info = extract_github_event_info(payload_dict)
        subject = email_info.get("subject")
        plain_text = email_info.get("plainText")
        html_body = email_info.get("html")
    else:
        # Standard email request
        subject = payload.subject or "Azure App Service Email Test"
        plain_text = payload.plainText or "Hello from Azure App Service API."
        html_body = payload.html or f"<html><body><h1>{plain_text}</h1></body></html>"
    
    # ... rest of send_email logic
```

#### Option 2: Dedicated GitHub Endpoint (Recommended)

Add a dedicated endpoint for GitHub webhooks in `app.py`:

```python
@app.post("/webhook/github")
def github_webhook(request: dict) -> dict:
    """Handle GitHub webhook events and send email notifications."""
    
    connection_string = _get_setting("ACS_EMAIL_CONNECTION_STRING")
    sender_address = _get_setting("ACS_EMAIL_SENDER")
    default_recipient = _get_setting("ACS_EMAIL_DEFAULT_TO")
    
    if not connection_string or not sender_address or not default_recipient:
        raise HTTPException(
            status_code=500,
            detail="Missing ACS settings"
        )
    
    # Extract GitHub event info
    repo_name = request.get("repository", {}).get("name", "unknown")
    event_type = "Unknown"
    subject = "GitHub Event"
    plain_text = "A GitHub event occurred"
    html_body = "<p>A GitHub event occurred</p>"
    
    if "pusher" in request:  # Push event
        pusher = request.get("pusher", {}).get("name", "Unknown")
        commits = request.get("commits", [])
        event_type = "Push"
        subject = f"[GitHub] {repo_name} - Pushed by {pusher}"
        plain_text = f"{pusher} pushed {len(commits)} commit(s)\n" + \
                     "\n".join([f"• {c['message']}" for c in commits[:5]])
        html_body = f"<h3>{pusher} pushed {len(commits)} commit(s)</h3>" + \
                    "".join([f"<p>• {c['message']}</p>" for c in commits[:5]])
    
    elif "pull_request" in request:  # PR event
        pr = request.get("pull_request", {})
        action = request.get("action", "updated")
        pr_number = pr.get("number")
        pr_title = pr.get("title")
        pr_user = pr.get("user", {}).get("login", "Unknown")
        event_type = f"Pull Request {action}"
        subject = f"[GitHub] PR #{pr_number} {action.upper()}: {pr_title}"
        plain_text = f"PR #{pr_number} {action} by {pr_user}: {pr_title}"
        html_body = f"<h3>PR #{pr_number} {action.upper()}</h3><p>{pr_title}</p><p>By: {pr_user}</p>"
    
    elif "issue" in request:  # Issue event
        issue = request.get("issue", {})
        action = request.get("action", "updated")
        issue_number = issue.get("number")
        issue_title = issue.get("title")
        issue_user = issue.get("user", {}).get("login", "Unknown")
        event_type = f"Issue {action}"
        subject = f"[GitHub] Issue #{issue_number} {action.upper()}: {issue_title}"
        plain_text = f"Issue #{issue_number} {action} by {issue_user}: {issue_title}"
        html_body = f"<h3>Issue #{issue_number} {action.upper()}</h3><p>{issue_title}</p><p>By: {issue_user}</p>"
    
    elif "release" in request:  # Release event
        release = request.get("release", {})
        tag_name = release.get("tag_name", "Unknown")
        release_name = release.get("name", tag_name)
        event_type = "Release"
        subject = f"[GitHub] Release: {release_name}"
        plain_text = f"New release: {release_name} ({tag_name})"
        html_body = f"<h3>New Release: {release_name}</h3><p>Tag: {tag_name}</p>"
    
    try:
        client = EmailClient.from_connection_string(connection_string)
        message = {
            "senderAddress": sender_address,
            "recipients": {"to": [{"address": default_recipient}]},
            "content": {
                "subject": subject,
                "plainText": plain_text,
                "html": html_body,
            },
        }
        
        poller = client.begin_send(message)
        result = poller.result()
        message_id = getattr(result, "message_id", None)
        
        return {
            "status": "sent",
            "event": event_type,
            "repository": repo_name,
            "messageId": message_id
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(ex)}")
```

Then update your GitHub webhook URL to:
```
https://eysampletrigger.azurewebsites.net/webhook/github
```

---

### Testing GitHub Webhook Locally

#### Test with curl

```bash
curl -X POST "http://localhost:8000/webhook/github" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "opened",
    "repository": {
      "name": "my-repo",
      "full_name": "username/my-repo"
    },
    "pull_request": {
      "number": 42,
      "title": "Add new feature",
      "user": {
        "login": "john-doe"
      }
    }
  }'
```

#### Test with Postman

1. Create **POST** request to `http://localhost:8000/webhook/github`
2. Set **Body** to **raw JSON**
3. Paste the sample payload above
4. Click **Send**

---

### GitHub Webhook Event Types & Options

| Event | Triggers | Use Case |
|-------|----------|----------|
| **Push** | Code committed and pushed | Notify team of commits |
| **Pull Request** | PR opened/closed/merged/synchronized | Code review notifications |
| **Issues** | Issue opened/closed/reopened | Bug/feature tracking |
| **Discussions** | Discussion created/answered | Team conversations |
| **Release** | Release published | Deployment notifications |
| **Repository** | Repo created/deleted/archived | Repo lifecycle events |
| **Workflow** | CI/CD workflow run completed | Build/test status |
| **Deployment** | Deployment created/completed | Deployment status |

---

### Add Conditional Logic (Optional)

You can configure the email API to send emails **only for certain events**:

```python
# In your webhook handler, add this check:
WEBHOOK_EVENTS_TO_NOTIFY = ["push", "pull_request", "release"]

def github_webhook(request: dict) -> dict:
    # Determine event type
    event_type = None
    if "pusher" in request:
        event_type = "push"
    elif "pull_request" in request:
        event_type = "pull_request"
    elif "release" in request:
        event_type = "release"
    
    # Only send email if event is in our notify list
    if event_type not in WEBHOOK_EVENTS_TO_NOTIFY:
        return {"status": "ignored", "reason": f"Event type '{event_type}' not configured for notification"}
    
    # ... continue with email sending
```

---

### Webhook Troubleshooting

#### Check Webhook Delivery History

1. Go to GitHub repo → **Settings** → **Webhooks**
2. Click the webhook URL
3. Scroll down to **Recent Deliveries**
4. Click on any delivery to see **Request** and **Response**

#### Common Issues

| Problem | Solution |
|---------|----------|
| Webhook not firing | Ensure event type is checked in webhook settings |
| 404 error | Verify webhook URL is correct and endpoint exists |
| 500 error | Check email settings (ACS_EMAIL_CONNECTION_STRING, etc.) |
| Email not sent | Verify recipient email is correct; check application logs |
| Webhook disabled | GitHub disables webhooks after 5 failed deliveries; re-enable manually |

---

## Deploy to Azure App Service

### Step 1: Create App Service Plan (if you don't have one)

```bash
az appservice plan create \
  --name "myAppServicePlan" \
  --resource-group "myResourceGroup" \
  --sku B1 \
  --is-linux
```

### Step 2: Create App Service (Python 3.10)

```bash
az webapp create \
  --resource-group "myResourceGroup" \
  --plan "myAppServicePlan" \
  --name "myEmailAPI" \
  --runtime "PYTHON|3.10" \
  --deployment-method local_git
```

### Step 3: Set Required Environment Variables

```bash
az webapp config appsettings set \
  --resource-group "myResourceGroup" \
  --name "myEmailAPI" \
  --settings \
    ACS_EMAIL_CONNECTION_STRING="your-connection-string" \
    ACS_EMAIL_SENDER="your-sender@azurecomm.net" \
    ACS_EMAIL_DEFAULT_TO="default-recipient@example.com" \
    WEBSITES_PORT=8000
```

### Step 4: Set Startup Command

```bash
az webapp config set \
  --resource-group "myResourceGroup" \
  --name "myEmailAPI" \
  --startup-file "gunicorn -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:8000 app:app"
```

### Step 5: Deploy Code via Git

```bash
# Get deployment credentials
az webapp deployment user set \
  --user-name "myDeploymentUser" \
  --password "StrongPassword123!"

# Initialize git repo and deploy
git init
git config user.email "you@example.com"
git config user.name "Your Name"
git add .
git commit -m "Initial deployment"
git remote add azure <git-clone-uri-from-step-2>
git push azure master
```

Alternatively, **zip deploy:**

```bash
# Create zip file
Compress-Archive -Path "app.py", "requirements.txt" -DestinationPath "app.zip"

# Deploy
az webapp deployment source config-zip \
  --resource-group "myResourceGroup" \
  --name "myEmailAPI" \
  --src-path "app.zip"
```

### Step 6: Verify Deployment

```bash
# Check logs
az webapp log tail \
  --resource-group "myResourceGroup" \
  --name "myEmailAPI"

# Look for: "Application startup complete"
```

---

## API Endpoints

### GET /health

**Purpose:** Health check endpoint  
**Authentication:** None  
**Request:** No body needed

```bash
curl http://localhost:8000/health
```

**Response:**

```json
{"status":"ok"}
```

---

### POST /email

**Purpose:** Send an email via Azure Communication Services  
**Authentication:** None  
**Request Body (all fields optional):**

```json
{
  "to": "recipient@example.com",           // Optional; uses ACS_EMAIL_DEFAULT_TO if not provided
  "subject": "Email Subject",              // Optional; defaults to "Azure App Service Email Test"
  "plainText": "Plain text content",       // Optional; defaults to standard message
  "html": "<html>...</html>"               // Optional; overrides plainText for HTML rendering
}
```

**Response (Success - 200):**

```json
{
  "status": "sent",
  "messageId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

**Response (Error - 400):**

```json
{
  "detail": "Sender domain is not linked to this Communication Service. Use the correct sender or connection string."
}
```

**Response (Error - 500):**

```json
{
  "detail": "Missing required settings: ACS_EMAIL_CONNECTION_STRING, ACS_EMAIL_SENDER, ACS_EMAIL_DEFAULT_TO."
}
```

---

## Test Validation Checklist

- [ ] **Health endpoint responds**: `curl http://localhost:8000/health` returns `{"status":"ok"}`
- [ ] **Email with defaults**: `curl -X POST http://localhost:8000/email -H "Content-Type: application/json" -d '{}'` returns message ID
- [ ] **Email with custom recipient**: Specify `"to"` field and verify email received
- [ ] **Email with custom subject & text**: Verify subject and body in received email
- [ ] **HTML email rendering**: Send HTML content and verify formatting in email client
- [ ] **Error handling**: Test with missing environment variables; expect 500 status
- [ ] **Domain validation**: Test with wrong sender; expect 400 DomainNotLinked error
- [ ] **Azure deployment**: App starts on App Service; `/health` returns 200
- [ ] **Azure email sending**: Send email from deployed App Service; verify delivery

---

## Troubleshooting

### Issue: "Missing required settings" (500 error)

**Cause:** Environment variables not set  
**Solution:**

```powershell
# Verify variables are set
echo $env:ACS_EMAIL_CONNECTION_STRING
echo $env:ACS_EMAIL_SENDER
echo $env:ACS_EMAIL_DEFAULT_TO

# If empty, re-set them:
$env:ACS_EMAIL_CONNECTION_STRING = "your-connection-string"
$env:ACS_EMAIL_SENDER = "your-sender"
$env:ACS_EMAIL_DEFAULT_TO = "your-email"
```

---

### Issue: "DomainNotLinked" (400 error)

**Cause:** Sender domain not verified in Azure Communication Services  
**Solution:**

1. Go to [Azure Portal](https://portal.azure.com)
2. Find your Email Communication Service
3. Click **Domains**
4. Verify your sender domain has **Status: Verified**
5. If it's not verified, follow the DNS verification steps or use Azure Managed Domain

---

### Issue: "Email service connection error" (502 error)

**Cause:** Invalid connection string or network issue  
**Solution:**

1. Verify connection string from Azure Portal (ACS → Keys)
2. Check internet connectivity: `ping 8.8.8.8`
3. If using corporate network, check firewall rules for Azure endpoints

---

### Issue: App not starting on Azure App Service

**Cause:** Wrong startup command or Python version  
**Solution:**

```bash
# Check logs
az webapp log tail --resource-group "myResourceGroup" --name "myEmailAPI"

# Verify Python 3.10+
az webapp config show --resource-group "myResourceGroup" --name "myEmailAPI" --query linuxFxVersion

# Re-set startup command
az webapp config set \
  --resource-group "myResourceGroup" \
  --name "myEmailAPI" \
  --startup-file "gunicorn -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:8000 app:app"

# Restart
az webapp restart --resource-group "myResourceGroup" --name "myEmailAPI"
```

---

### Issue: Email not received (but API returns 200)

**Cause:** Email in spam folder or recipient address invalid  
**Solution:**

1. Check spam/junk folder
2. Verify recipient email is valid format
3. Check ACS email logs in Azure Portal
4. Try sending to a different test email address

---

## Project Structure

```
emailFunction/
├── app.py                 # FastAPI application with email endpoints
├── requirements.txt       # Python dependencies
├── README.md             # Documentation (this file)
└── .venv/               # Virtual environment (local only)
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.116.1 | Web framework |
| uvicorn | 0.35.0 | ASGI server |
| gunicorn | 23.0.0 | Production server |
| pydantic | v2 | Request validation |
| azure-communication-email | v1.1.0 | Azure Email API |
| email-validator | 2.2.0 | Email validation |

---

## Support & Resources

- [Azure Communication Services Documentation](https://learn.microsoft.com/en-us/azure/communication-services/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure CLI Reference](https://learn.microsoft.com/en-us/cli/azure/)

---

## Final Outcome Summary

The main outcome expected from this repository is a working GitHub-to-email notification flow.

In practical terms, that means:

- A change happens in the GitHub repository.
- GitHub sends a webhook request.
- The deployed service handles the request.
- Azure Communication Services sends the email.
- The customer-defined recipient receives the notification.

If these steps are working end to end, then the repository objective has been achieved.

---

## License

MIT (or your preferred license)

---

## Questions?

For issues or questions, check the **Troubleshooting** section or review the Azure Communication Services documentation linked above.
