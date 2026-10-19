"""
AI-Powered Desktop Virtual Pet — Mochi
Requirements: Python 3.9+ (Tkinter is included with most Python installations)
Optional AI chat: set the GEMINI_API_KEY environment variable to a Google Gemini API key.
Without an API key, the pet still works using built-in context-aware replies.
"""

import json
import os
import random
import threading
import urllib.error
import urllib.request
import tkinter as tk
from tkinter import ttk

PET_NAME = "Mochi"
GEMINI_MODEL = "gemini-2.5-flash"


class VirtualPetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mochi — AI Virtual Pet")
        self.root.geometry("720x700")
        self.root.minsize(620, 620)
        self.root.configure(bg="#FFF7F0")

        self.hunger = 65       # higher means more satisfied
        self.happiness = 65
        self.energy = 75
        self.mood = "Happy"
        self.chat_history = []

        self._setup_styles()
        self._build_ui()
        self.update_pet_display()
        self.add_message("Mochi", "Meow! Hi, I'm Mochi 🐱 Your new virtual friend. Want to play or chat?")
        self.root.after(45000, self.natural_needs_tick)

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TProgressbar", thickness=14, background="#F59EAE",
                        troughcolor="#F0E4DE", bordercolor="#F0E4DE",
                        lightcolor="#F59EAE", darkcolor="#F59EAE")
        style.configure("Pet.TButton", font=("Segoe UI", 10, "bold"),
                        padding=(10, 8), background="#F8C8A8")
        style.map("Pet.TButton", background=[("active", "#F3AE91")])

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#F8D8C5", padx=18, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="🐾  MOCHI'S LITTLE WORLD", font=("Segoe UI", 18, "bold"),
                 bg="#F8D8C5", fg="#653F36").pack()
        tk.Label(header, text="Your friendly AI-powered desktop pet",
                 font=("Segoe UI", 10), bg="#F8D8C5", fg="#79574D").pack(pady=(3, 0))

        pet_card = tk.Frame(self.root, bg="#FFFFFF", padx=16, pady=12,
                            highlightbackground="#F1D9CE", highlightthickness=1)
        pet_card.pack(fill="x", padx=18, pady=(14, 8))

        self.pet_art = tk.Label(pet_card, text="🐱", font=("Segoe UI Emoji", 78),
                                bg="#FFFFFF", fg="#7A4937")
        self.pet_art.pack()
        self.pet_name_label = tk.Label(pet_card, text="Mochi", font=("Segoe UI", 17, "bold"),
                                        bg="#FFFFFF", fg="#653F36")
        self.pet_name_label.pack()
        self.mood_label = tk.Label(pet_card, text="Mood: Happy 😊",
                                   font=("Segoe UI", 11, "bold"), bg="#FFFFFF", fg="#B45B72")
        self.mood_label.pack(pady=(2, 8))

        stats = tk.Frame(pet_card, bg="#FFFFFF")
        stats.pack(fill="x", padx=8)
        self.stat_bars = {}
        for key, label in [("hunger", "Fullness"), ("happiness", "Happiness"), ("energy", "Energy")]:
            line = tk.Frame(stats, bg="#FFFFFF")
            line.pack(fill="x", pady=3)
            tk.Label(line, text=label, width=11, anchor="w", bg="#FFFFFF",
                     fg="#654A42", font=("Segoe UI", 9)).pack(side="left")
            bar = ttk.Progressbar(line, maximum=100, value=65)
            bar.pack(side="left", fill="x", expand=True, padx=(4, 8))
            value_label = tk.Label(line, text="65%", width=5, bg="#FFFFFF",
                                   fg="#654A42", font=("Segoe UI", 9))
            value_label.pack(side="right")
            self.stat_bars[key] = (bar, value_label)

        actions = tk.Frame(self.root, bg="#FFF7F0")
        actions.pack(fill="x", padx=18, pady=6)
        ttk.Button(actions, text="🍎 Feed Mochi", style="Pet.TButton",
                   command=self.feed_pet).pack(side="left", expand=True, fill="x", padx=4)
        ttk.Button(actions, text="🎾 Play", style="Pet.TButton",
                   command=self.play_with_pet).pack(side="left", expand=True, fill="x", padx=4)
        ttk.Button(actions, text="😴 Rest", style="Pet.TButton",
                   command=self.rest_pet).pack(side="left", expand=True, fill="x", padx=4)

        chat_frame = tk.Frame(self.root, bg="#FFFFFF", padx=12, pady=10,
                              highlightbackground="#F1D9CE", highlightthickness=1)
        chat_frame.pack(fill="both", expand=True, padx=18, pady=(6, 16))
        tk.Label(chat_frame, text="💬 Chat with Mochi", font=("Segoe UI", 12, "bold"),
                 bg="#FFFFFF", fg="#653F36").pack(anchor="w", pady=(0, 6))

        self.chat_box = tk.Text(chat_frame, height=8, wrap="word", state="disabled",
                                font=("Segoe UI", 10), bg="#FFFBF8", fg="#49352F",
                                relief="flat", padx=8, pady=8)
        self.chat_box.pack(fill="both", expand=True)
        self.chat_box.tag_configure("user", foreground="#346B7A", font=("Segoe UI", 10, "bold"))
        self.chat_box.tag_configure("pet", foreground="#B45B72", font=("Segoe UI", 10, "bold"))

        input_row = tk.Frame(chat_frame, bg="#FFFFFF")
        input_row.pack(fill="x", pady=(8, 0))
        self.message_entry = ttk.Entry(input_row, font=("Segoe UI", 10))
        self.message_entry.pack(side="left", fill="x", expand=True, ipady=7)
        self.message_entry.bind("<Return>", lambda event: self.send_message())
        ttk.Button(input_row, text="Send ➤", style="Pet.TButton",
                   command=self.send_message).pack(side="left", padx=(8, 0))
        self.message_entry.focus_set()

        ai_key = os.getenv("GEMINI_API_KEY")
        ai_status = "AI chat enabled ✨" if ai_key else "Demo chat mode (add GEMINI_API_KEY for Generative AI)"
        tk.Label(self.root, text=ai_status, font=("Segoe UI", 8),
                 bg="#FFF7F0", fg="#98796F").pack(pady=(0, 5))

    def add_message(self, speaker, message):
        self.chat_box.configure(state="normal")
        tag = "user" if speaker == "You" else "pet"
        self.chat_box.insert("end", f"{speaker}: ", tag)
        self.chat_box.insert("end", message + "\n\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def update_pet_display(self):
        if self.hunger < 30:
            self.mood = "Hungry"
        elif self.energy < 25:
            self.mood = "Sleepy"
        elif self.happiness < 30:
            self.mood = "Sad"
        elif self.happiness > 75 and self.energy > 35:
            self.mood = "Playful"
        else:
            self.mood = "Happy"

        mood_faces = {
            "Happy": "🐱", "Hungry": "🐱", "Sleepy": "😴",
            "Sad": "😿", "Playful": "😸"
        }
        mood_emojis = {"Happy": "😊", "Hungry": "🍎", "Sleepy": "💤",
                       "Sad": "😿", "Playful": "🎾"}
        self.pet_art.configure(text=mood_faces[self.mood])
        self.mood_label.configure(text=f"Mood: {self.mood} {mood_emojis[self.mood]}")
        values = {"hunger": self.hunger, "happiness": self.happiness, "energy": self.energy}
        for key, value in values.items():
            bar, label = self.stat_bars[key]
            bar["value"] = value
            label.configure(text=f"{value}%")

    def feed_pet(self):
        if self.hunger >= 95:
            self.add_message(PET_NAME, "I'm already full! Save the snacks for later, please. 😺")
        else:
            self.hunger = min(100, self.hunger + 25)
            self.happiness = min(100, self.happiness + 5)
            self.add_message(PET_NAME, random.choice([
                "Yum yum! Thank you for the tasty snack! 🍎",
                "That was delicious! You're the best. 💗",
                "Munch, munch… I feel much better now!"
            ]))
        self.update_pet_display()

    def play_with_pet(self):
        if self.energy < 15:
            self.add_message(PET_NAME, "I'm too sleepy to play right now. Let me rest first. 💤")
        else:
            self.happiness = min(100, self.happiness + 20)
            self.energy = max(0, self.energy - 15)
            self.hunger = max(0, self.hunger - 8)
            self.add_message(PET_NAME, random.choice([
                "Yay! Let's chase the ball again! 🎾",
                "That was so much fun! You're my favourite playmate!",
                "Wheee! Playtime makes me so happy! 😸"
            ]))
        self.update_pet_display()

    def rest_pet(self):
        self.energy = min(100, self.energy + 30)
        self.happiness = min(100, self.happiness + 3)
        self.add_message(PET_NAME, "Purr... I had a little nap and feel refreshed. 💤")
        self.update_pet_display()

    def send_message(self):
        message = self.message_entry.get().strip()
        if not message:
            return
        self.message_entry.delete(0, "end")
        self.add_message("You", message)
        self.chat_history.append({"role": "user", "text": message})
        self.happiness = min(100, self.happiness + 3)
        self.update_pet_display()

        # Do network work in a background thread so the interface stays responsive.
        threading.Thread(target=self._get_reply_worker, args=(message,), daemon=True).start()

    def _get_reply_worker(self, message):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                reply = self._gemini_reply(message, api_key)
            except Exception:
                reply = self._local_reply(message)
        else:
            reply = self._local_reply(message)
        self.root.after(0, lambda: self._finish_reply(reply))

    def _finish_reply(self, reply):
        self.add_message(PET_NAME, reply)
        self.chat_history.append({"role": "assistant", "text": reply})
        self.update_pet_display()

    def _local_reply(self, message):
        text = message.lower()
        if any(word in text for word in ["hungry", "food", "eat", "snack"]):
            return "Did someone say food? 🍎 You can press Feed Mochi to give me a snack!"
        if any(word in text for word in ["play", "game", "ball", "fun"]):
            return "I love playtime! 🎾 Press Play and let's have some fun."
        if any(word in text for word in ["sad", "upset", "bad day", "unhappy"]):
            self.happiness = max(0, self.happiness - 2)
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

    def _gemini_reply(self, message, api_key):
        prompt = (
            f"You are {PET_NAME}, a friendly, playful virtual cat in a desktop pet app. "
            f"Your current mood is {self.mood}; fullness is {self.hunger}/100, "
            f"happiness is {self.happiness}/100, and energy is {self.energy}/100. "
            "Reply to the user's latest message in character. Be kind, concise (1-3 sentences), "
            "and context-aware. If they mention feeding, playing, or resting, suggest the matching "
            "app button when useful. Do not claim to perform an action unless the user pressed a button. "
            f"User message: {message}"
        )
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + GEMINI_MODEL + ":generateContent?key=" + api_key
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}],
                   "generationConfig": {"temperature": 0.8, "maxOutputTokens": 120}}
        request = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    def natural_needs_tick(self):
        # Small changes make the pet feel alive over time.
        self.hunger = max(0, self.hunger - 3)
        self.energy = max(0, self.energy - 2)
        if self.hunger < 25:
            self.happiness = max(0, self.happiness - 2)
        self.update_pet_display()
        self.root.after(45000, self.natural_needs_tick)


if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualPetApp(root)
    root.mainloop()
