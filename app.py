from flask import Flask, render_template, request
import requests
import os

from scraper import extract_website_data, check_broken_links, extract_seo_data, check_mobile_responsiveness
from analyzer import (
    analyze_readability,
    analyze_accessibility,
    check_color_contrast,
    calculate_usability_score
)

app = Flask(__name__)

PAGESPEED_API_KEY = os.environ.get("PAGESPEED_API_KEY", "")  # Set in environment

def get_pagespeed_data(url):
    """Fetch real performance data from Google PageSpeed Insights API."""
    try:
        api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        params = {
            "url": url,
            "strategy": "mobile",
            "category": ["performance", "accessibility", "seo", "best-practices"]
        }
        if PAGESPEED_API_KEY:
            params["key"] = PAGESPEED_API_KEY

        response = requests.get(api_url, params=params, timeout=30)
        data = response.json()

        categories = data.get("lighthouseResult", {}).get("categories", {})
        audits = data.get("lighthouseResult", {}).get("audits", {})

        result = {
            "performance_score": round(categories.get("performance", {}).get("score", 0) * 100),
            "accessibility_score": round(categories.get("accessibility", {}).get("score", 0) * 100),
            "seo_score": round(categories.get("seo", {}).get("score", 0) * 100),
            "best_practices_score": round(categories.get("best-practices", {}).get("score", 0) * 100),
            "fcp": audits.get("first-contentful-paint", {}).get("displayValue", "N/A"),
            "lcp": audits.get("largest-contentful-paint", {}).get("displayValue", "N/A"),
            "cls": audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A"),
            "tbt": audits.get("total-blocking-time", {}).get("displayValue", "N/A"),
            "speed_index": audits.get("speed-index", {}).get("displayValue", "N/A"),
        }
        return result

    except Exception as e:
        return None


@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        input_url = request.form["url"].strip()
        final_url = input_url

        if not final_url.startswith("http"):
            final_url = "https://" + final_url

        try:
            # Step 1: Scrape
            html, text, final_url = extract_website_data(final_url)

            # Step 2: All analysis checks
            readability = analyze_readability(text)
            accessibility_issues, accessibility_score = analyze_accessibility(html)
            color_data = check_color_contrast(html)
            seo_data = extract_seo_data(html, final_url)
            mobile_data = check_mobile_responsiveness(html)
            broken_links, links_checked = check_broken_links(html, final_url)

            # Step 3: PageSpeed (Google API)
            pagespeed = get_pagespeed_data(final_url)

            # Step 4: Calculate overall score
            score, suggestions, breakdown = calculate_usability_score(
                readability, accessibility_score, seo_data,
                mobile_data, broken_links, pagespeed
            )

            # Step 5: Grade
            if score >= 85:
                grade = "A"
                grade_label = "Excellent"
                grade_color = "#22c55e"
            elif score >= 70:
                grade = "B"
                grade_label = "Good"
                grade_color = "#84cc16"
            elif score >= 55:
                grade = "C"
                grade_label = "Average"
                grade_color = "#f59e0b"
            elif score >= 40:
                grade = "D"
                grade_label = "Needs Work"
                grade_color = "#f97316"
            else:
                grade = "F"
                grade_label = "Poor"
                grade_color = "#ef4444"

            result = {
                "input_url": input_url,
                "final_url": final_url,
                "score": score,
                "grade": grade,
                "grade_label": grade_label,
                "grade_color": grade_color,
                "readability": readability,
                "accessibility_issues": accessibility_issues,
                "accessibility_score": accessibility_score,
                "color_data": color_data,
                "seo": seo_data,
                "mobile": mobile_data,
                "broken_links": broken_links,
                "links_checked": links_checked,
                "pagespeed": pagespeed,
                "breakdown": breakdown,
                "suggestions": suggestions
            }

        except Exception as e:
            result = {
                "error": "Could not analyze this website. It may block automated tools or the URL may be invalid. Try another URL."
            }

    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)
