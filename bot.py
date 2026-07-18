from flask import Flask, request
import requests
import os
import io
import time
import threading
app = Flask(__name__)
VERIFY_TOKEN = "mybot123"
WHATSAPP_TOKEN = "EAANbmDzhfUMBRwShlPPmvZB9y0xNM4riOXNitA5Ldm3NAJF8zhYJ4KWoTC95dRDs0VdMyxYG9VFZCj2ZACnapoOZB1ImlJwk68ZBQEL2ZApdivjJiv0FuEZCYebuSzlBQuOykcLtG2pojFAZAQHDrE2BOH3qtMbVQMVkCfGDNlGRdUollLHdAPDZCgyhQBFUnDMuoXAZDZD"
PHONE_NUMBER_ID = "1106377899206038"
AGENT_URL = "https://clint-translucent-zack.ngrok-free.dev/process"
def send_message(to, msg):
    url = "https://graph.facebook.com/v22.0/" + PHONE_NUMBER_ID + "/messages"
    headers = {"Authorization": "Bearer " + WHATSAPP_TOKEN, "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": msg}}
    resp = requests.post(url, headers=headers, json=data)
    print("send_message to:", to, "status:", resp.status_code, "resp:", resp.text[:300])
def handle_message(sender, text):
    text_upper = text.strip().upper()
    parts = text_upper.split()
    keywords = ["ITR", "GST", "AUDIT", "FORM16", "BS", "COMPUTATION", "TDSRETURN", "NOTICE"]
    found_keywords = []
    pan = None
    include_bs = False
    years = []
    for part in parts:
        if part in keywords:
            if part == "BS":
                include_bs = True
            elif part not in found_keywords:
                found_keywords.append(part)
        if len(part) == 4 and part.isdigit() and 2007 <= int(part) <= 2026:
            years.append(part)
        if len(part) == 10 and part.isalnum():
            pan = part
    if not years:
        years = ["2025"]
    doc_type = None
    if "ITR" in found_keywords and "AUDIT" in found_keywords:
        doc_type = "ITR_AUDIT"
    elif "ITR" in found_keywords and include_bs:
        doc_type = "ITR_BS"
    elif include_bs:
        doc_type = "BALANCE"
    elif found_keywords:
        doc_type = found_keywords[0]
    if not doc_type:
        send_message(sender,
            "Welcome to Soni Soni & Co!\n\n"
            "Send your request:\n"
            "ITR ABCDE1234F\n"
            "ITR 2024 ABCDE1234F\n"
            "ITR 2023 2024 2025 ABCDE1234F\n"
            "ITR BS ABCDE1234F\n"
            "ITR BS 2024 ABCDE1234F\n"
            "ITR BS 2023 2024 2025 ABCDE1234F\n"
            "ITR AUDIT ABCDE1234F\n"
            "ITR AUDIT 2023 2024 2025 ABCDE1234F\n"
            "BS ABCDE1234F\n"
            "BS 2024 ABCDE1234F\n"
            "BS 2023 2024 2025 ABCDE1234F\n"
            "COMPUTATION ABCDE1234F\n"
            "COMPUTATION 2024 ABCDE1234F\n"
            "COMPUTATION 2023 2024 2025 ABCDE1234F\n"
            "AUDIT ABCDE1234F\n"
            "AUDIT 2024 ABCDE1234F\n"
            "AUDIT 2023 2024 2025 ABCDE1234F\n\n"
            "Replace ABCDE1234F with your PAN.\n"
            "Year is optional - default is current year.\n"
            "All commands support multiple years at once."
        )
        return
    if not pan:
        send_message(sender, "Please send your PAN number also.\nExample: ITR AUDIT 2024 2025 ABCDE1234F")
        return
    years_display = ", ".join(y + "-" + str(int(y) + 1)[-2:] for y in years)
    if len(years) > 1:
        send_message(sender, "Request received! Fetching " + doc_type + " for PAN " + pan + " for years: " + years_display + ". Processing all years in one session, please wait...")
    else:
        send_message(sender, "Request received! Fetching " + doc_type + " for PAN " + pan + " Year " + years_display + ". Please wait 5-8 minutes...")
    try:
        requests.post(AGENT_URL, json={"pan": pan, "doc_type": doc_type, "sender": sender, "years": years}, timeout=5)
    except Exception:
        pass
@app.route("/send_message", methods=["POST"])
def send_message_route():
    data = request.get_json()
    send_message(data["to"], data["msg"])
    return "OK", 200
@app.route("/send_doc", methods=["POST"])
def send_doc_route():
    to = request.form.get("to")
    name = request.form.get("name")
    f = request.files.get("file")
    print("Sending doc to:", to, "name:", name)
    url = "https://graph.facebook.com/v22.0/" + PHONE_NUMBER_ID + "/messages"
    headers = {"Authorization": "Bearer " + WHATSAPP_TOKEN}
    file_content = f.read()
    print("File size bytes:", len(file_content))
    media = requests.post(
        "https://graph.facebook.com/v22.0/" + PHONE_NUMBER_ID + "/media",
        headers=headers,
        files={"file": (name, io.BytesIO(file_content), "application/pdf")},
        data={"messaging_product": "whatsapp"}
    )
    print("Media upload response:", media.status_code, media.text)
    mid = media.json().get("id")
    if not mid:
        print("MEDIA UPLOAD FAILED for", name, "-", media.text)
        return "MEDIA_UPLOAD_FAILED: " + media.text, 502
    data = {"messaging_product": "whatsapp", "to": to, "type": "document", "document": {"id": mid, "filename": name}}
    resp = requests.post(url, headers=headers, json=data)
    print("Send doc response:", resp.status_code, resp.text)
    if resp.status_code != 200:
        print("SEND DOC FAILED for", name, "-", resp.text)
        return "SEND_FAILED: " + resp.text, 502
    return "OK", 200
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
            if msg.get("type") != "text":
                print("Non-text message ignored:", msg.get("type"))
                return "OK", 200
            sender = msg["from"]
            text = msg["text"]["body"]
            print("Message from", sender, ":", text)
            threading.Thread(target=handle_message, args=(sender, text), daemon=True).start()
        else:
            print("No messages, keys:", list(value.keys()))
    except Exception as e:
        print("Webhook error:", e)
    return "OK", 200
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
