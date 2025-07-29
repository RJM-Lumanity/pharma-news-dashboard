import requests
import streamlit as st
import feedparser
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

# ---- Load RSS sources and therapy areas ----
with open("rss_sources.json", "r") as f:
    rss_sources = json.load(f)

with open("therapy_areas.json", "r") as f:
    therapy_areas = json.load(f)

st.title("Pharma News Dashboard 📰")
st.write("Showing articles from the last 7 days, grouped by therapy area.")

def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    for img in soup.find_all("img"):
        img.decompose()
    return soup.get_text()

import re

def article_in_last_30_days(entry):
    try:
        if hasattr(entry, "published_parsed"):
            published_struct = entry.published_parsed
        elif hasattr(entry, "updated_parsed"):
            published_struct = entry.updated_parsed
        else:
            return False

        published_date = datetime.fromtimestamp(time.mktime(published_struct))
        return published_date >= datetime.now() - timedelta(days=7)
    except:
        return False

import re

def matches_therapy_area(entry_text, keywords):
    # Normalize text (lowercase, remove punctuation)
    clean_text = re.sub(r"[^\w\s]", "", entry_text.lower())
    words = clean_text.split()  # split into words

    for keyword in keywords:
        keyword_clean = re.sub(r"[^\w\s]", "", keyword.lower())
        keyword_parts = keyword_clean.split()

        # ✅ If keyword has multiple words, check for full phrase match
        if len(keyword_parts) > 1:
            if keyword_clean in clean_text:
                return True
        else:
            # ✅ If single word, match as a standalone word
            if keyword_clean in words:
                return True

    return False

@st.cache_data(ttl=3600)  # cache for 1 hour
def fetch_full_article_text(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        article_body = (
            soup.find("article")
            or soup.find("div", class_="article-content")
            or soup.find("div", class_="content")
            or soup.body
        )

        if article_body:
            paragraphs = article_body.find_all("p")
            text = "\n".join(
                p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
            )
            return text
        else:
            paragraphs = soup.body.find_all("p")
            return "\n".join(
                p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
            )
    except Exception as e:
        print(f"Error fetching article at {url}: {e}")
        return ""


# Sidebar selectbox for therapy area
selected_area = st.sidebar.selectbox("Select therapy area", list(therapy_areas.keys()))

# ---- Fetch all articles from all sources ----
all_articles = []

for source_name, feed_url in rss_sources.items():
    feed = feedparser.parse(feed_url)

    for entry in feed.entries:
        # ✅ Get published date
        published_struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if not published_struct:
            continue  # skip if no date

        published_date = datetime.fromtimestamp(time.mktime(published_struct))
        if published_date < datetime.now() - timedelta(days=7):
            continue  # skip if older than 7 days

        # ✅ Extract title safely
        title_clean = BeautifulSoup(getattr(entry, "title", ""), "html.parser").get_text()

        # ✅ Extract summary safely (fallback to description if summary missing)
        raw_summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
        summary_clean = clean_html(raw_summary)

        # ✅ Combine text for keyword matching
        combined_text = f"{title_clean} {summary_clean}"

        all_articles.append({
            "title": title_clean,
            "link": getattr(entry, "link", ""),
            "published": getattr(entry, "published", "") or getattr(entry, "updated", ""),
            "summary": summary_clean,
            "text": combined_text,
            "source": source_name
        })

# ✅ Fetch full article text and combine with title for keyword matching
full_text = fetch_full_article_text(getattr(entry, "link", ""))
combined_text = f"{title_clean} {summary_clean} {full_text}"

        all_articles.append({
            "title": title_clean,
            "link": getattr(entry, "link", ""),
            "published": getattr(entry, "published", "") or getattr(entry, "updated", ""),
            "summary": summary_clean,
            "text": combined_text,
            "source": source_name
        })

# ---- Group by therapy area ----
grouped_articles = {area: [] for area in therapy_areas.keys()}

for article in all_articles:
    for area, keywords in therapy_areas.items():
        if matches_therapy_area(article["text"], keywords):
            grouped_articles[area].append(article)

# ---- Display articles grouped by therapy area ----
st.subheader(selected_area)

articles = grouped_articles[selected_area]

if not articles:
    st.write("_No articles found in the past 7 days_")
else:
    for art in articles:
        st.markdown(f"### [{art['title']}]({art['link']})")
        st.write(f"**Published:** {art['published']}")
        st.write(art['summary'])
        st.markdown("---")
