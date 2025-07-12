from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import json

# Load scheme data
with open("schemes.json", encoding="utf-8") as f:
    scheme_data = json.load(f)

# Match user with eligible schemes
def get_matching_schemes(user):
    matches = []
    for s in scheme_data:
        c = s.get("criteria", {})
        if (
            ("age_max" not in c or user["age"] <= c["age_max"]) and
            ("income_max" not in c or user["income"] <= c["income_max"]) and
            ("occupation" not in c or user["occupation"].lower() in [o.lower() for o in c.get("occupation", [])]) and
            ("gender" not in c or user["gender"].lower() == c["gender"].lower())
        ):
            matches.append(s)
    return matches

# Flask setup
app = Flask(__name__)
user_data = {}

@app.route("/", methods=["GET"])
def home():
    return "✅ eSahyog WhatsApp Bot is Running!"

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip().lower()
    user_id = request.values.get("From")
    resp = MessagingResponse()
    msg = resp.message()

    # Restart logic
    if incoming_msg in ["restart", "start", "hi", "hello"]:
        user_data[user_id] = {"step": "start"}
        msg.body("🔁 Welcome back to eSahyog!\nLet’s find the perfect scheme for you.\nFirst — how old are you?")
        return str(resp)

    # Initialize user
    if user_id not in user_data:
        user_data[user_id] = {"step": "start"}

    step = user_data[user_id]["step"]

    # Step-by-step flow
    if step == "start":
        try:
            age = int(incoming_msg)
            user_data[user_id]["age"] = age
            msg.body("💰 Got it! Now tell me your *monthly income* in INR.")
            user_data[user_id]["step"] = "income"
        except ValueError:
            msg.body("Please enter your age as a number, like *23*.")
    elif step == "income":
        try:
            income = int(incoming_msg)
            user_data[user_id]["income"] = income
            msg.body("👩‍🌾 Nice! What is your occupation? (e.g. student, farmer, worker)")
            user_data[user_id]["step"] = "occupation"
        except ValueError:
            msg.body("Please enter income as a number, like *25000*.")
    elif step == "occupation":
        user_data[user_id]["occupation"] = incoming_msg
        msg.body("🚻 And your gender? (male/female/other)")
        user_data[user_id]["step"] = "gender"
    elif step == "gender":
        user_data[user_id]["gender"] = incoming_msg
        schemes = get_matching_schemes(user_data[user_id])
        if not schemes:
            msg.body("😔 Sorry, no matching schemes were found.\nYou can still explore: https://www.myscheme.gov.in/")
        else:
            reply = "🎯 Based on your profile, here are schemes you qualify for:\n\n"
            for i, s in enumerate(schemes[:5]):  # Limit to 5 for readability
                reply += f"{i+1}. *{s['name']}*\n{s['description']}\n🔗 {s['link']}\n\n"
            msg.body(reply + "💡 Type 'restart' to try again.")
        user_data[user_id]["step"] = "done"
    else:
        msg.body("👋 Type *restart* to begin again.")

    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
