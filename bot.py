from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "mybot123"
WHATSAPP_TOKEN = "EAANbmDzhfUMBRCZBQroaZCMkYNaUeCJ231pNzHL9lKXlozpUN84ZB0xUTEwSkvpSfQfZAhAooWU1BSUjtjVBlsVUErMTWZBhhLaaz8awssVZCHZCswi6rzdLV7dZB0bVyHxgNuZCqnB3OfhnQB3VX6WdnDHOJupC65DesEms5zk2ZCueiBYqp6pElWB9P7wsZAV9pr05nUeeHH0o0r00VWU5OEZB24U2IO13ctkAo3QutLULi2Pptikd3bCVQMGwVAx883oRZABmIUfELxBU7vCZAcLQhOBgZDZD"
PHONE_NUMBER_ID = "1106377899206038"
AGENT_URL = "https://clint-translucent-zack.ngrok-free.dev/process"

def send_message(to, msg):
    url = "https://graph.facebook.com/v22.0/" + PHONE_NUMBER_ID + "/messages"
    headers = {"Authorization": "Bearer " + WHATSAPP_TOKEN, "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": msg}}
    requests.post(url, headers=headers, json=data)

def handle_message(sender, text):
    text = text.strip().upper()
    parts = text.split()
    keywords = ["ITR", "GST", "AUDIT", "FORM16", "BALANCE", "COMPUTATION", "TDSRETURN", "NOTICE"]
    doc_type = None
    pan = None
    for part in parts:
        if part in keywords:
            doc_type = part
        if len(part) == 10 and part.isalnum():
            pan = part
    if not doc_type:
        send_message(sender,
            "Welcome to Soni Soni & Co!\n\n"
            "Send your request:\n"
            "ITR ABCDE1234F\n"
            "GST ABCDE1234F\n"
            "AUDIT ABCDE1234F\n"
            "FORM16 ABCDE1234F\n"
            "BALANCE ABCDE1234F\n"
            "COMPUTATION ABCDE1234F\n\n"
            "Replace ABCDE1234F with your PAN."
        )
        return
    if not pan:
        send_message(sender, "Please send your PAN number also.\nExample: " + doc_type + " ABCDE1234F")
        return
    send_message(sender, "Request received! Fetching your " + doc_type + " for PAN " + pan + ". Please wait 2-3 minutes...")
    try:
        requests.post(AGENT_URL, json={"pan": pan, "doc_type": doc_type, "sender": sender}, timeout=5)
    except:
        pass

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        if "messages" in value:
            msg = value["messages"][0]
            sender = msg["from"]
            text = msg["text"]["body"]
            handle_message(sender, text)
    except Exception as e:
        print("Error:", e)
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
