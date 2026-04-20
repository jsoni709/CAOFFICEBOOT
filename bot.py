from flask import Flask, request
import requests
import os
app = Flask(__name__)
VERIFY_TOKEN = "mybot123"
WHATSAPP_TOKEN = "EAANbmDzhfUMBRYfyLIpZBLgAwtrea0QKkdzR4ZBbcyR4ZB6VdEJshp4f4MQ9857OnmdENmyigi2WXKcIz0Up6Ng93T3VJvh6ga87ywFwZBLcp0s7dAFHnpYtuJIJ57hY27DuZBR15BkUNU6yjY1dlLKkBOukZCCZBoT9YXy3ed7XDMPvySup4ItI5LaNiMOtHlsSo8nGiDwyu4RWZCW0V7JGhRwH7tBtzckTyg7MLWlcZADItcvuIIBZCFGZACdOZBlyApNL2plo1GCzm2FBZAjoHkBLH"
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
        send_message(sender, "Welcome to Soni Soni & Co!\n\nSend your request:\nITR ABCDE1234F\nGST ABCDE1234F\nAUDIT ABCDE1234F\nFORM16 ABCDE1234F\nBALANCE ABCDE1234F\nCOMPUTATION ABCDE1234F\n\nReplace ABCDE1234F with your PAN.")
        return
    if not pan:
        send_message(sender, "Please send your PAN number also.\nExample: " + doc_type + " ABCDE1234F")
        return
    send_message(sender, "Request received! Fetching your " + doc_type + " for PAN " + pan + ". Please wait 2-3 minutes...")
    try:
        requests.post(AGENT_URL, json={"pan": pan, "doc_type": doc_type, "sender": sender}, timeout=5)
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
    url = "https://graph.facebook.com/v22.0/" + PHONE_NUMBER_ID + "/messages"
    headers = {"Authorization": "Bearer " + WHATSAPP_TOKEN}
    media = requests.post("https://graph.facebook.com/v22.0/" + PHONE_NUMBER_ID + "/media", headers=headers, files={"file": (name, f, "application/pdf")}, data={"messaging_product": "whatsapp"})
    mid = media.json().get("id")
    if mid:
        data = {"messaging_product": "whatsapp", "to": to, "type": "document", "document": {"id": mid, "filename": name}}
        requests.post(url, headers=headers, json=data)
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
            sender = msg["from"]
            text = msg["text"]["body"]
            handle_message(sender, text)
    except Exception as e:
        print("Error:", e)
    return "OK", 200
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
