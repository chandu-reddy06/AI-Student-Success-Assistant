# Student Success AI

A local-first academic command center that converts a student's attendance, CGPA, weak subject and study time into a readiness score, personalized actions and a 7-day study roadmap. It also includes an optional local AI coach using Ollama/Qwen 3 8B with a built-in fallback.

## Run
```bash
python -m pip install Flask
python app.py
```
Open `http://127.0.0.1:5000`.

## Optional local AI
Install Ollama and pull `qwen3:8b`. The app automatically uses it at `http://127.0.0.1:11434` when available; otherwise the built-in coach keeps the demo working.

## Stack
Python, Flask, SQLite, HTML, CSS, JavaScript, Ollama/Qwen (optional local AI).
