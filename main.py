import os
import json
from flask import Flask, request, jsonify
from notion_client import Client
from replit import ai  # Only if you want to use Replit AI

app = Flask(__name__)

# Load environment variables
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
PORT = int(os.getenv("PORT", 8080))

if not NOTION_API_KEY or not NOTION_DATABASE_ID:
    raise Exception("Missing NOTION_API_KEY or NOTION_DATABASE_ID environment variables.")

notion = Client(auth=NOTION_API_KEY)

@app.route("/", methods=["GET"])
def home():
    return "✅ LTV Analyzer is running with Replit AI!"

@app.route("/analyze-email", methods=["POST"])
def analyze_email():
    try:
        data = request.get_json()
        email_body = data.get("email", "").strip()
        if not email_body:
            return jsonify({"error": "No email content provided"}), 400

        prompt = f"""
You’re an intelligent customer service analyzer. Here's a customer message:

\"\"\"{email_body}\"\"\"

Categorize the message:
1. What type of issue is this? (Login Issue, UX Confusion, Bug, Billing, Feature Request, Other)
2. What is the user trying to do or confused about?
3. What is the customer’s emotional tone?
4. Suggest a possible fix (UX copy change, help article, feature tweak, etc.)

Return your answer in JSON format like:
{{
  "issue_type": "Login Issue",
  "user_goal": "Trying to log in with Google",
  "tone": "Confused",
  "suggested_fix": "Clarify Google login option with tooltip"
}}
"""

        # Call Replit AI to analyze
        ai_response = ai.completions.create(
            prompt=prompt,
            model="chat-bison",
            temperature=0.2,
        )

        # Parse AI output - expecting JSON string
        structured = json.loads(ai_response)

        # Create a new page in Notion
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Message Snippet": {
                    "title": [{"text": {"content": email_body[:100]}}]
                },
                "Issue Type": {
                    "multi_select": [{"name": structured.get("issue_type", "Other")}]
                },
                "Affected Feature/Page": {
                    "multi_select": [{"name": "Unknown"}]  # Customize as needed
                },
                "Tone": {
                    "select": {"name": structured.get("tone", "Neutral")}
                },
                "Proposed Fix": {
                    "rich_text": [{"text": {"content": structured.get("suggested_fix", "")}}]
                },
                "Status": {
                    "select": {"name": "Logged"}
                },
                "Impact Level": {
                    "select": {"name": "Medium"}
                },
            }
        )

        return jsonify({"status": "success", "data": structured})

    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse AI response JSON"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
