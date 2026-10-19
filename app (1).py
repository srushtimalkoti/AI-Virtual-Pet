import os
import random
import json
import urllib.request
import urllib.error
import streamlit as st

PET_NAME = "Mochi"
GEMINI_MODEL = "gemini-2.5-flash"

st.set_page_config(page_title="Mochi — AI Virtual Pet", page_icon="🐾", layout="centered")

# Soft pastel theme using Streamlit-supported markdown/CSS.
st.markdown("""
<style>
.stApp { background: #fff7f0; }
.block-container { max-width: 820px; padding-top: 1.5rem; }
.mochi-header {
  background: #f8d8c5; border-radius: 18px; padding: 18px 12px;
  text-align: center; color: #653f36; margin-bottom: 16px;
}
.pet-card {
  background: white; border: 1px solid #f1d9ce; border-radius: 18px;
  padding: 18px; text-align: center; margin-bottom: 14px;
}
.mood { color: #b45b72; font-weight: 700; font-size: 1.1rem; }
.chat-user { color: #346b7a; font-weight: 700; }
.chat-pet { color: #b45b72; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

def init_state():
    defaults = {
        "hunger": 65, "happiness": 65, "energy": 75,
        "messages": [{"speaker": "Mochi", "text": "Meow! Hi, I'm Mochi 🐱 Your new virtual friend. Want to play or chat?"}],
        "chat_history": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_mood():
    if st.session_state.hunger < 30:
        return "Hungry", "🍎", "🐱"
    if st.session_state.energy < 25:
        return "Sleepy", "💤", "😴"
    if st.session_state.happiness < 30:
        return "Sad", "😿", "😿"
    if st.session_state.happiness > 75 and st.session_state.energy > 35:
        return "Playful", "🎾", "😸"
    return "Happy", "😊", "🐱"

def add_message(speaker, text):
    st.session_state.messages.append({"speaker": speaker, "text": text})

def local_reply(message):
    text = message.lower()
    if any(word in text for word in ["hungry", "food", "eat", "snack"]):
        return "Did someone say food? 🍎 You can press Feed Mochi to give me a snack!"
    if any(word in text for word in ["play", "game", "ball", "fun"]):
        return "I love playtime! 🎾 Press Play and let's have some fun."
    if any(word in text for word in ["sad", "upset", "bad day", "unhappy"]):
        st.session_state.happiness = max(0, st.session_state.happiness - 2)
        return "Aww, I'm here with you. 💗 Want to tell me what happened?"
    if any(word in text for word in ["hello", "hi", "hey"]):
        return "Hiii! 😸 I'm Mochi, your curious little cat. How is your day going?"
    if any(word in text for word in ["name", "who are you"]):
        return "I'm Mochi! 🐱 A friendly, playful cat who loves snacks and chatting."
    if any(word in text for word in ["tired", "sleep", "rest"]):
        return "A little rest sounds lovely. 💤 Press Rest and I'll recharge!"
    if "love" in text or "friend" in text:
        return "Awww, you're my favourite human friend! Sending you a tiny purr. 💗"
    return random.choice([
        "That's interesting! Tell me a little more. 🐾",
        "I'm listening with my tiny cat ears. 😺",
        "Hmm… let me think about that! What happened next?",
        "Thanks for telling me! I'm happy we can chat. 💗"
    ])

def gemini_reply(message, api_key):
    mood, _, _ = get_mood()
    prompt = (
        f"You are {PET_NAME}, a friendly, playful virtual cat in a virtual pet app. "
        f"Your current mood is {mood}; fullness is {st.session_state.hunger}/100, "
        f"happiness is {st.session_state.happiness}/100, and energy is {st.session_state.energy}/100. "
        "Reply to the user's latest message in character. Be kind, concise (1-3 sentences), "
        "and context-aware. If they mention feeding, playing, or resting, suggest the matching "
        "app button when useful. Do not claim to perform an action unless the user pressed a button. "
        f"User message: {message}"
    )
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        f"?key={api_key}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}],
               "generationConfig": {"temperature": 0.8, "maxOutputTokens": 120}}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()

def respond(message):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        try:
            return gemini_reply(message, api_key)
        except Exception:
            return local_reply(message)
    return local_reply(message)

init_state()
mood, mood_emoji, pet_face = get_mood()

st.markdown(
    "<div class='mochi-header'><h1>🐾 MOCHI'S LITTLE WORLD</h1>"
    '<p>Your friendly AI-powered virtual pet</p></div>',
    unsafe_allow_html=True
)
st.markdown(
    f'<div class="pet-card"><div style="font-size:5rem">{pet_face}</div>'
    f'<h2 style="color:#653f36;margin:0">{PET_NAME}</h2>'
    f'<div class="mood">Mood: {mood} {mood_emoji}</div></div>',
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🍎 Fullness", f"{st.session_state.hunger}%")
    st.progress(st.session_state.hunger / 100)
with col2:
    st.metric("💗 Happiness", f"{st.session_state.happiness}%")
    st.progress(st.session_state.happiness / 100)
with col3:
    st.metric("⚡ Energy", f"{st.session_state.energy}%")
    st.progress(st.session_state.energy / 100)

def feed_pet():
    if st.session_state.hunger >= 95:
        add_message(PET_NAME, "I'm already full! Save the snacks for later, please. 😺")
    else:
        st.session_state.hunger = min(100, st.session_state.hunger + 25)
        st.session_state.happiness = min(100, st.session_state.happiness + 5)
        add_message(PET_NAME, random.choice([
            "Yum yum! Thank you for the tasty snack! 🍎",
            "That was delicious! You're the best. 💗",
            "Munch, munch… I feel much better now!"
        ]))

def play_pet():
    if st.session_state.energy < 15:
        add_message(PET_NAME, "I'm too sleepy to play right now. Let me rest first. 💤")
    else:
        st.session_state.happiness = min(100, st.session_state.happiness + 20)
        st.session_state.energy = max(0, st.session_state.energy - 15)
        st.session_state.hunger = max(0, st.session_state.hunger - 8)
        add_message(PET_NAME, random.choice([
            "Yay! Let's chase the ball again! 🎾",
            "That was so much fun! You're my favourite playmate!",
            "Wheee! Playtime makes me so happy! 😸"
        ]))

def rest_pet():
    st.session_state.energy = min(100, st.session_state.energy + 30)
    st.session_state.happiness = min(100, st.session_state.happiness + 3)
    add_message(PET_NAME, "Purr... I had a little nap and feel refreshed. 💤")

st.subheader("Take care of Mochi")
a, b, c = st.columns(3)
with a:
    st.button("🍎 Feed Mochi", use_container_width=True, on_click=feed_pet)
with b:
    st.button("🎾 Play", use_container_width=True, on_click=play_pet)
with c:
    st.button("😴 Rest", use_container_width=True, on_click=rest_pet)

st.subheader("💬 Chat with Mochi")
for item in st.session_state.messages:
    with st.chat_message("user" if item["speaker"] == "You" else "assistant",
                         avatar="🙂" if item["speaker"] == "You" else "🐱"):
        st.write(item["text"])

user_message = st.chat_input("Message Mochi...")
if user_message:
    add_message("You", user_message)
    st.session_state.chat_history.append({"role": "user", "text": user_message})
    st.session_state.happiness = min(100, st.session_state.happiness + 3)
    reply = respond(user_message)
    add_message(PET_NAME, reply)
    st.session_state.chat_history.append({"role": "assistant", "text": reply})
    st.rerun()

if os.getenv("GEMINI_API_KEY"):
    st.caption("✨ Generative AI chat enabled (Gemini)")
else:
    st.caption("🐾 Demo chat mode. Add GEMINI_API_KEY in your hosting secrets to enable Gemini AI.")
