from bs4 import BeautifulSoup
import re

# ─── Readability ────────────────────────────────────────────────────────────

def analyze_readability(text):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = re.findall(r'\w+', text)

    num_sentences = max(1, len(sentences))
    num_words = max(1, len(words))
    avg_words = num_words / num_sentences

    syllable_count = sum(_count_syllables(w) for w in words)
    flesch = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (syllable_count / max(1, num_words))
    flesch = round(max(0, min(100, flesch)), 1)

    if flesch >= 70:
        level = "Easy to read"
    elif flesch >= 50:
        level = "Moderate"
    else:
        level = "Difficult to read"

    return {
        "flesch_score": flesch,
        "avg_words_per_sentence": round(avg_words, 1),
        "total_words": num_words,
        "level": level
    }

def _count_syllables(word):
    word = word.lower()
    count = len(re.findall(r'[aeiou]+', word))
    if word.endswith('e') and count > 1:
        count -= 1
    return max(1, count)

# ─── Accessibility ───────────────────────────────────────────────────────────

def analyze_accessibility(html):
    soup = BeautifulSoup(html, "html.parser")
    issues = []
    score = 100

    # Images alt text
    images = soup.find_all("img")
    missing_alt = [img for img in images if not img.get("alt")]
    if missing_alt:
        issues.append(f"{len(missing_alt)} image(s) missing alt text — hurts screen reader accessibility")
        score -= min(20, len(missing_alt) * 5)

    # H1 structure
    h1_tags = soup.find_all("h1")
    if len(h1_tags) == 0:
        issues.append("No <h1> heading found — important for screen readers and SEO")
        score -= 15
    elif len(h1_tags) > 1:
        issues.append(f"Multiple <h1> tags ({len(h1_tags)}) found — only one is recommended per page")
        score -= 10

    # Form labels
    inputs = soup.find_all("input", attrs={"type": lambda t: t not in ["hidden", "submit", "button"]})
    labels = soup.find_all("label")
    label_fors = {label.get("for") for label in labels}
    unlabeled = [inp for inp in inputs if inp.get("id") not in label_fors and not inp.get("aria-label")]
    if unlabeled:
        issues.append(f"{len(unlabeled)} form input(s) missing labels — inaccessible to screen readers")
        score -= 10

    # Language attribute
    html_tag = soup.find("html")
    if html_tag and not html_tag.get("lang"):
        issues.append("Missing lang attribute on <html> tag — required for accessibility")
        score -= 5

    # Skip navigation link
    skip_link = soup.find("a", href="#main") or soup.find("a", string=re.compile("skip", re.I))
    if not skip_link:
        issues.append("No skip navigation link found — recommended for keyboard users")
        score -= 5

    return issues, max(0, score)

# ─── Color Contrast ──────────────────────────────────────────────────────────

def check_color_contrast(html):
    results = {
        "has_sufficient_contrast": True,
        "issues": [],
        "low_contrast_count": 0
    }

    # Look for inline styles with light-on-light or common low contrast combos
    light_colors = ["#fff", "#ffffff", "white", "#f0f0f0", "#fafafa", "#eeeeee", "#e0e0e0"]
    dark_colors = ["#000", "#000000", "black", "#111", "#222", "#333"]

    soup = BeautifulSoup(html, "html.parser")
    elements_with_style = soup.find_all(style=True)

    low_contrast = 0
    for el in elements_with_style:
        style = el.get("style", "").lower()
        has_color = "color:" in style
        has_bg = "background" in style

        if has_color and has_bg:
            # Very basic heuristic: both light = bad contrast
            color_is_light = any(c in style for c in light_colors)
            bg_is_light = any(c in style for c in light_colors)
            if color_is_light and bg_is_light:
                low_contrast += 1

    results["low_contrast_count"] = low_contrast
    if low_contrast > 0:
        results["has_sufficient_contrast"] = False
        results["issues"].append(f"{low_contrast} element(s) may have light-on-light color contrast issues")
    else:
        results["issues"].append("No obvious inline color contrast issues detected")

    # Check for small fonts (< 12px) which worsen readability
    small_fonts = re.findall(r'font-size\s*:\s*([0-9]+)px', html)
    tiny = [int(f) for f in small_fonts if int(f) < 12]
    if tiny:
        results["issues"].append(f"{len(tiny)} element(s) use font sizes below 12px — hard to read")
        results["low_contrast_count"] += len(tiny)

    return results

# ─── Final Score ─────────────────────────────────────────────────────────────

def calculate_usability_score(readability, accessibility_score, seo_data,
                               mobile_data, broken_links, pagespeed=None):
    score = 0
    suggestions = []
    breakdown = {}

    # 1. Readability (15 pts)
    flesch = readability["flesch_score"]
    if flesch >= 70:
        r_score = 15
    elif flesch >= 50:
        r_score = 10
        suggestions.append("✏️ Simplify sentence structure to improve readability (Flesch score: {})".format(flesch))
    else:
        r_score = 5
        suggestions.append("✏️ Content is hard to read (Flesch score: {}). Use shorter sentences and simpler words.".format(flesch))
    score += r_score
    breakdown["Readability"] = {"score": r_score, "max": 15}

    # 2. Accessibility (20 pts)
    a_score = round(accessibility_score * 20 / 100)
    score += a_score
    breakdown["Accessibility"] = {"score": a_score, "max": 20}

    # 3. SEO (25 pts)
    seo_score = 0
    if seo_data.get("title"):
        t_len = seo_data["title_length"]
        if 30 <= t_len <= 60:
            seo_score += 8
        else:
            seo_score += 4
            suggestions.append("🔍 Title tag length ({} chars) should be 30–60 characters for best SEO.".format(t_len))
    else:
        suggestions.append("🔍 Missing <title> tag — critical for SEO.")

    if seo_data.get("meta_description"):
        d_len = seo_data["meta_description_length"]
        if 120 <= d_len <= 160:
            seo_score += 7
        else:
            seo_score += 3
            suggestions.append("🔍 Meta description ({} chars) should be 120–160 characters.".format(d_len))
    else:
        suggestions.append("🔍 Missing meta description — affects click-through rate in search results.")

    if seo_data.get("h1_count") == 1:
        seo_score += 5
    elif seo_data.get("h1_count") == 0:
        suggestions.append("🔍 Add exactly one <h1> tag to improve SEO structure.")

    if seo_data.get("og_title"):
        seo_score += 5
    else:
        suggestions.append("🔍 Add Open Graph tags (og:title, og:description) for better social media sharing.")

    score += seo_score
    breakdown["SEO"] = {"score": seo_score, "max": 25}

    # 4. Mobile Responsiveness (20 pts)
    mob_score = 0
    if mobile_data.get("has_viewport"):
        mob_score += 10
    else:
        suggestions.append("📱 Missing viewport meta tag — page will not render correctly on mobile devices.")
    if mobile_data.get("has_media_queries"):
        mob_score += 5
    else:
        suggestions.append("📱 No CSS media queries detected — consider adding responsive breakpoints.")
    if mobile_data.get("has_responsive_classes"):
        mob_score += 5
    if mobile_data.get("has_fixed_widths"):
        mob_score = max(0, mob_score - 5)
        suggestions.append("📱 Fixed pixel widths detected in CSS — use percentages or max-width for responsiveness.")
    score += mob_score
    breakdown["Mobile"] = {"score": mob_score, "max": 20}

    # 5. Broken Links (10 pts)
    link_score = 10 if not broken_links else max(0, 10 - len(broken_links) * 3)
    if broken_links:
        suggestions.append("🔗 {} broken link(s) found — fix these to improve user experience and SEO.".format(len(broken_links)))
    score += link_score
    breakdown["Links"] = {"score": link_score, "max": 10}

    # 6. PageSpeed (10 pts)
    if pagespeed:
        ps = pagespeed.get("performance_score", 0)
        p_score = round(ps * 10 / 100)
        score += p_score
        breakdown["Performance"] = {"score": p_score, "max": 10}
        if ps < 50:
            suggestions.append("⚡ PageSpeed score is low ({}). Optimize images, minify CSS/JS, enable caching.".format(ps))
        elif ps < 80:
            suggestions.append("⚡ PageSpeed score ({}) can be improved. Consider lazy loading and compression.".format(ps))
    else:
        breakdown["Performance"] = {"score": 0, "max": 10, "note": "PageSpeed data unavailable"}

    return min(100, score), suggestions, breakdown
