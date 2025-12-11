from flask import Flask, render_template, request, redirect, url_for
import os
import json
from datetime import datetime
from random import choice, randint

app = Flask(__name__)

# File to store entries
DATA_FILE = "entries.json"


# Initialize the database (JSON file)
def init_db():
    try:
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w") as f:
                json.dump([], f)
    except Exception:
        # If the environment disallows file creation, fail silently; handlers will surface errors later.
        pass

# Ensure the data file exists on import (required when running under Gunicorn/Render)
init_db()

# Home page
@app.route('/')
def home():
    return render_template("index.html")


# Mock analysis endpoint (no external API).
# Expects JSON: { "text": "..." }
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json() or {}
    text = data.get('text', '')

    # If an OpenAI API key is present, attempt to use it for a richer analysis.
    # This is optional and falls back to the local mocked analyzer below.
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        try:
            import openai
            openai.api_key = openai_key
            # Ask the model to return a compact JSON with the required fields.
            prompt = (
                "Extract the user's emotion, a stress score 0-100 (integer), "
                "up to 6 keywords, and a short calming reflection from the text. "
                "Return ONLY a JSON object with keys: emotion, stress, keywords, reflection. "
                "Example: {\"emotion\":\"sad\", \"stress\":45, \"keywords\":[\"tired\"], \"reflection\":\"...\"}\n\n"
                f"Text: {text}"
            )
            resp = openai.ChatCompletion.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You are a calm assistant that outputs compact JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=300,
            )
            content = resp['choices'][0]['message']['content']
            # Try to extract first JSON object from the model output
            import re
            m = re.search(r"\{[\s\S]*\}", content)
            if m:
                parsed = json.loads(m.group(0))
                # Ensure fields we expect exist, coerce types
                parsed.setdefault('emotion', 'neutral')
                parsed.setdefault('stress', 0)
                parsed.setdefault('keywords', [])
                parsed.setdefault('reflection', '')
                # Normalize stress to int 0-100
                try:
                    parsed['stress'] = int(max(0, min(100, int(parsed['stress']))))
                except Exception:
                    parsed['stress'] = 0
                return parsed
        except Exception:
            # If anything goes wrong with external API, fall back to mock below
            pass

    # Very simple mock: pick an emotion from a list based on keywords
    emotions = ['happy', 'sad', 'anxious', 'angry', 'neutral', 'calm', 'stressed']
    keywords_map = {
        'happy': ['joy', 'good', 'great', 'happy', 'excited'],
        'sad': ['sad', 'down', 'lonely', 'gloom'],
        'anxious': ['nervous', 'anxious', 'worried', 'panic'],
        'angry': ['angry', 'mad', 'furious', 'upset'],
        'stressed': ['stress', 'overwhelm', 'overwhelmed', 'pressure'],
        'calm': ['calm', 'relaxed', 'peace'],
        'neutral': []
    }

    text_l = (text or '').lower()
    detected = 'neutral'
    found_keywords = []
    for emo, kws in keywords_map.items():
        for kw in kws:
            if kw in text_l:
                detected = emo
                found_keywords.append(kw)

    # If none matched, pick one lightly at random (mock behavior)
    if detected == 'neutral' and text_l.strip():
        detected = choice(emotions)

    # Mock stress level 0-100
    stress = min(100, max(0, randint(10, 90) + (20 if detected in ('anxious','stressed') else 0)))

    # Simple reflection templates
    reflections = {
        'happy': "It sounds like you're feeling good today — that's wonderful. Take a moment to notice what made you feel this way.",
        'sad': "It sounds like you're feeling down. It's okay to sit with that feeling — be gentle with yourself.",
        'anxious': "It sounds like you're feeling anxious. Try a slow breath and notice one small thing that felt okay today.",
        'angry': "It sounds like you're feeling angry. Your feelings are valid; maybe name the cause and a small next step.",
        'stressed': "It sounds like you're feeling overwhelmed. A short break or a walk could help you reset.",
        'calm': "You sound calm — that's a nice space to be in. Notice what helped you arrive here.",
        'neutral': "Thanks for sharing — taking this step matters."
    }

    response = {
        'emotion': detected,
        'stress': stress,
        'keywords': found_keywords,
        'reflection': reflections.get(detected)
    }

    return response

# Add a new emotion entry
@app.route('/add', methods=['POST'])
def add_entry():
    emotion = request.form.get("emotion")
    note = request.form.get("note", "")
    # allow note as JSON field name 'note' if saved from client
    if not note:
        note = request.form.get('note', '')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = {
        "emotion": emotion,
        "note": note,
        "timestamp": timestamp
    }

    # Load existing entries
    with open(DATA_FILE, "r") as f:
        entries = json.load(f)

    # If stress was included in form (optional), try to attach
    try:
        stress_val = request.form.get('stress')
        if stress_val:
            entry['stress'] = int(stress_val)
    except Exception:
        pass

    entries.append(entry)

    # Save back
    with open(DATA_FILE, "w") as f:
        json.dump(entries, f, indent=4)

    return redirect(url_for('entries'))

# View all entries
@app.route('/entries')
def entries():
    with open(DATA_FILE, "r") as f:
        entries = json.load(f)
    return render_template("entries.html", entries=entries)


@app.route('/api/entries')
def api_entries():
    # Return raw entries as JSON for client-side charts
    with open(DATA_FILE, "r") as f:
        entries = json.load(f)
    return { 'entries': entries }


@app.route('/history')
def history():
    # Page with Chart.js visualization
    return render_template('history.html')

if __name__ == '__main__':
    init_db()
    print("Starting Flask server...")
    app.run(debug=True)

