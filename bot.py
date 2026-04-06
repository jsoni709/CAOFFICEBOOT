from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "mybot123"
WHATSAPP_TOKEN = "EAANbmDzhfUMBREfLLeXi4SHMW1Pig9lof0N6yeJoXVal5DaLgpdqIgxxIRR7L4L7i0SMlZBbn1G00cfvfGqMmmjwekoZBe5m3RGZBTZAhZA2rsgaotYxE0vLCPiquDPg49BesZBVUQbvXlfZAsxreP9N2kdMemJnxoZAWZCnMF5j5k3ZBU5X3G0k0jNux7oBSX6ohiri1APXbc8du8O0vXulBZCXNADCuHuiEIkVGsYhY9xiXlTX8tSVlCi0MU2IzxSJjwjBZCMR3l4KcRxzXey01Re8"
PHONE_NUMBER_ID = "1106377899206038"

def send_message(to, message):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
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
            "Welcome to Soni Soni & Co CA Office!\n\n"
            "Send your request in this format:\n"
            "ITR ABCDE1234F\n"
            "GST ABCDE1234F\n"
            "AUDIT ABCDE1234F\n"
            "FORM16 ABCDE1234F\n"
            "BALANCE ABCDE1234F\n"
            "COMPUTATION ABCDE1234F\n"
            "TDSRETURN ABCDE1234F\n"
            "NOTICE ABCDE1234F\n\n"
            "Replace ABCDE1234F with your PAN number."
        )
        return
    if not pan:
        send_message(sender, f"Please send your PAN number also.\nExample: {doc_type} ABCDE1234F")
        return
    send_message(sender,
        f"Dear Client,\n\n"
        f"We have received your request for {doc_type}.\n"
        f"PAN: {pan}\n\n"
        f"Our team will process your request and send the document shortly.\n\n"
        f"Thank you!\nSoni Soni & Co"
    )

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
