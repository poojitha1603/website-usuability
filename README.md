# AI Website Usability Analyzer

A full-stack web application that analyzes any website's usability and performance in real time using Google PageSpeed Insights API.

## 🔍 What it does
- Evaluates website performance, SEO, accessibility, and mobile responsiveness
- Generates a letter grade (A to F) with a score out of 100
- Provides actionable improvement suggestions for each category
- Analyzes SEO elements like title tags, meta description, and Open Graph tags
- Checks accessibility issues like missing alt text and heading structure
- Detects mobile responsiveness using viewport and media query signals
- Analyzes color contrast and readability of page content

## 🛠️ Technologies Used
- **Backend:** Python, Flask, REST APIs
- **API:** Google PageSpeed Insights API
- **Scraping:** BeautifulSoup4
- **Frontend:** HTML5, CSS3, JavaScript
- **Deployment:** Render

## 🚀 How to run locally

1. Clone the repo
   git clone https://github.com/your-username/your-repo-name.git

2. Install dependencies
   pip install -r requirements.txt

3.
   Create a .env file and add:
   PAGESPEED_API_KEY

4. Run the app
   python app.py

5. Open in browser
   http://localhost:5000

## 🌐 Live Demo
https://website-usuability.onrender.com

## 📁 Project Structure
ai-website-usability-analyzer/
├── app.py
├── analyzer.py
├── scraper.py
├── requirements.txt
└── templates/
    └── index.html
