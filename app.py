from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import pickle
from pathlib import Path

from fastapi.responses import HTMLResponse
from jinja2 import Template

# Request schema
class TweetRequest(BaseModel):
    tweet: str

# Load model and vectorizer
with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

with open("model.pkl", "rb") as f:
    model = pickle.load(f)

# Initialize app
app = FastAPI(title="Sentiment Analysis API")

# Setup templates
templates = Jinja2Templates(directory="templates")

# HTML templates as strings
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentiment Analysis Tool</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f3f4f6;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 640px;
            margin: 0 auto;
            padding: 2rem;
        }
        .card {
            background-color: white;
            border-radius: 0.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            padding: 2rem;
        }
        .title {
            font-size: 1.5rem;
            font-weight: bold;
            color: #1f2937;
            text-align: center;
            margin-bottom: 1rem;
        }
        .subtitle {
            color: #6b7280;
            text-align: center;
            margin-bottom: 2rem;
        }
        .textarea {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #d1d5db;
            border-radius: 0.375rem;
            min-height: 120px;
            resize: vertical;
        }
        .textarea:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }
        .button {
            background-color: #3b82f6;
            color: white;
            font-weight: medium;
            padding: 0.75rem 1.5rem;
            border-radius: 0.375rem;
            border: none;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: background-color 0.2s;
        }
        .button:hover {
            background-color: #2563eb;
        }
        .button:disabled {
            background-color: #9ca3af;
            cursor: not-allowed;
        }
        .loading-spinner {
            display: inline-block;
            width: 1rem;
            height: 1rem;
            border: 2px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
            margin-right: 0.5rem;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .counter {
            font-size: 0.875rem;
            color: #6b7280;
            text-align: right;
            margin-top: 0.25rem;
        }
        .counter.error {
            color: #ef4444;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1 class="title">Sentiment Analysis</h1>
            <p class="subtitle">Enter a tweet to analyze its sentiment</p>
            
            <form method="post" action="/predict" onsubmit="handleSubmit(event)">
                <div>
                    <textarea id="tweet" name="tweet" class="textarea" 
                        placeholder="Enter your tweet here..." required
                        oninput="updateCounter()"></textarea>
                    <div id="counter" class="counter">0/280 characters</div>
                </div>
                
                <div style="text-align: center; margin-top: 1.5rem;">
                    <button type="submit" id="submit-btn" class="button">
                        Analyze Sentiment
                    </button>
                </div>
            </form>
        </div>
    </div>

    <script>
        function handleSubmit(event) {
            const submitButton = document.getElementById('submit-btn');
            if (submitButton) {
                submitButton.innerHTML = `
                    <span class="loading-spinner"></span>
                    Analyzing...
                `;
                submitButton.disabled = true;
            }
        }

        function updateCounter() {
            const textarea = document.getElementById('tweet');
            const counter = document.getElementById('counter');
            if (textarea && counter) {
                const length = textarea.value.length;
                counter.textContent = `${length}/280 characters`;
                if (length > 280) {
                    counter.classList.add('error');
                } else {
                    counter.classList.remove('error');
                }
            }
        }

        // Initialize counter on page load
        document.addEventListener('DOMContentLoaded', updateCounter);
    </script>
</body>
</html>
"""

RESULT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis Result</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f3f4f6;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 640px;
            margin: 0 auto;
            padding: 2rem;
        }
        .card {
            background-color: white;
            border-radius: 0.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            padding: 2rem;
        }
        .title {
            font-size: 1.5rem;
            font-weight: bold;
            color: #1f2937;
            text-align: center;
            margin-bottom: 1rem;
        }
        .back-link {
            color: #3b82f6;
            text-align: center;
            display: block;
            margin-bottom: 2rem;
            text-decoration: none;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        .tweet-box {
            background-color: #f9fafb;
            padding: 1rem;
            border-radius: 0.375rem;
            border: 1px solid #e5e7eb;
            margin-bottom: 1.5rem;
        }
        .sentiment-box {
            padding: 1.5rem;
            border-radius: 0.375rem;
            border-width: 2px;
            text-align: center;
            font-weight: bold;
            font-size: 1.25rem;
            animation: fadeIn 0.5s ease-in;
        }
        .positive {
            background-color: #ecfdf5;
            border-color: #10b981;
            color: #047857;
        }
        .negative {
            background-color: #fef2f2;
            border-color: #ef4444;
            color: #b91c1c;
        }
        .sentiment-icon {
            font-size: 1.5rem;
            margin-right: 0.5rem;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1 class="title">Analysis Result</h1>
            <a href="/" class="back-link">Analyze another tweet</a>
            
            <div>
                <h2 style="font-size: 1.125rem; font-weight: 600; color: #4b5563; margin-bottom: 0.5rem;">
                    Original Tweet
                </h2>
                <div class="tweet-box">
                    {{ tweet }}
                </div>
                
                <h2 style="font-size: 1.125rem; font-weight: 600; color: #4b5563; margin-bottom: 0.5rem;">
                    Sentiment
                </h2>
                <div class="sentiment-box {{ sentiment_class }}">
                    {% if sentiment_class == 'positive' %}
                        😊 Positive
                    {% else %}
                        😞 Negative
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return HTMLResponse(content=INDEX_HTML)




@app.post("/predict", response_class=HTMLResponse)
async def predict_sentiment_ui(request: Request, tweet: str = Form(...)):
    X = vectorizer.transform([tweet])
    prediction = model.predict(X)[0]
    sentiment = "positive" if prediction == 1 else "negative"
    sentiment_class = "positive" if prediction == 1 else "negative"

    # Render HTML template from string
    result_template = Template(RESULT_HTML)
    rendered_html = result_template.render(tweet=tweet, sentiment_class=sentiment_class)

    return HTMLResponse(content=rendered_html)


# Keep the original API endpoint
@app.post("/api/predict")
def predict_sentiment_api(data: TweetRequest):
    text = data.tweet
    X = vectorizer.transform([text])
    prediction = model.predict(X)[0]
    sentiment = "positive" if prediction == 1 else "negative"
    return {"tweet": text, "sentiment": sentiment}
