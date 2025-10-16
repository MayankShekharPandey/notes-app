# 📝 Notes App

A full-stack notes application built with Flask and Supabase.

![Flask](https://img.shields.io/badge/Flask-2.3.3-green)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-blue)
![Python](https://img.shields.io/badge/Python-3.9+-yellow)

## 🚀 Live Demo

**[Access the app here](https://notes-app-theta-black.vercel.app/)**

## ✨ Features

- User authentication with Supabase
- Create, edit, delete notes
- Organize with categories
- Star important notes
- Search functionality
- Responsive design

## 🛠️ Tech Stack

- **Backend:** Flask, Python
- **Database:** Supabase (PostgreSQL)
- **Frontend:** HTML, CSS, Jinja2
- **Deployment:** Vercel

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/your-username/notes-app.git
cd notes-app
pip install -r requirements.txt

# Add .env file with Supabase credentials
echo "SUPABASE_URL=your_url" > .env
echo "SUPABASE_KEY=your_key" >> .env

# Run locally
python app.py
```

## 📁 Project Structure

```
notes-app/
├── app.py              # Main application
├── supabase_client.py  # Database config
├── requirements.txt    # Dependencies
├── static/style.css   # Styles
└── templates/         # HTML templates
```

## 🌐 Deployment

Deployed on Vercel with environment variables for Supabase credentials.

---

**Live at:** [notes-app-theta-black.vercel.app](https://notes-app-theta-black.vercel.app/)
```

## 🚀 **Push the Short Version**

```powershell
git add README.md
git commit -m "Shorter, cleaner README"
git push origin main
```
