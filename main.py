import os
from flask import Flask, request, jsonify
from notion_client import Client
from textblob import TextBlob

app = Flask(__name__)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
PORT = int(os.getenv("PORT", 8080))

if not NOTION_API_KEY or not NOTION_DATABASE_ID:
    raise Exception("Missing NOTION_API_KEY or NOTION_DATABASE_ID")

notion = Client(auth=NOTION_API_KEY)

# Simple keyword mapping for issue types and fixes
ISSUE_KEYWORDS = {
    "login": ("Login Issue", "Check login process and credentials."),
    "password": ("Login Issue", "Provide clear password reset instructions."),
    "bug": ("Bug", "Investigate and fix the reported bug."),
    "payment": ("Billing", "Verify payment processing and errors."),
    "upgrade": ("Feature Request", "Consider feature upgrade requests."),
    "slow": ("Performance", "Optimize system speed."),
    "error": ("Bug", "Check error logs and resolve."),
}

def classify_issue(email_text):
    text_lower = email_text.lower()
    for keyword, (issue, fix) in ISSUE_KEYWORDS.items():
        if keyword in text_lower:
            return issue, fix
    return "Other", "Review manually."

def analyze_tone(email_text):
    sentiment = TextBlob(email_text).sentiment.polarity
    if sentiment > 0.2:
        return "Positive"
    elif sentiment < -0.2:
        return "Negative"
    else:
        return "Neutral"

@app.route("/", methods=["GET"])
def home():
    return "✅ LTV Analyzer running locally with simple NLP."

@app.route("/analyze-email", methods=["POST"])
def analyze_email():
    data = request.get_json()
    email_body = data.get("email", "").strip()
    if not email_body:
        return jsonify({"error": "No email content provided"}), 400

    issue_type, suggested_fix = classify_issue(email_body)
    tone = analyze_tone(email_body)

    # Save to Notion
    notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties={
            "Message Snippet": {
                "title": [{"text": {"content": email_body[:100]}}]
            },
            "Issue Type": {
                "multi_select": [{"name": issue_type}]
            },
            "Tone": {
                "select": {"name": tone}
            },
            "Proposed Fix": {
                "rich_text": [{"text": {"content": suggested_fix}}]
            },
            "Status": {
                "select": {"name": "Logged"}
            },
            "Impact Level": {
                "select": {"name": "Medium"}
            },
        }
    )

    return jsonify({
        "status": "success",
        "data": {
            "issue_type": issue_type,
            "tone": tone,
            "suggested_fix": suggested_fix
        }
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
