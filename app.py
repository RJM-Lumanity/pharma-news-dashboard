import requests
import streamlit as st
import feedparser
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re

# ---- Load RSS sources and therapy areas ----
with open("rss_sources.json", "r") as f:
    rss_sources = json.load(f)

with open("therapy_areas.json", "r") as f:
    therapy_areas = json.load(f)

st.title("Pharma News Dashboard 📰")
st.write("Showing articles from the last 30 days, grouped by therapy area.")

def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    for img in soup.find_all("img"):
        img.decompose()
    return soup.get_text()

def matches_therapy_area(entry_text, keywords):
    clean_text = re.sub(r"[^\w\s]", "", entry_text.lower())
    words = clean_text.split()

    for keyword in keywords:
        keyword_clean = re.sub(r"[^\w\s]", "", keyword.lower())
        keyword_parts = keyword_clean.split()

        if len(keyword_parts) > 1:
            if keyword_clean in clean_text:
                return True
        else:
            if keyword_clean in words:
                return True
    return False

def fetch_full_article_text(url):
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
            return "\n".join(
                p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
            )

        paragraphs = soup.body.find_all("p")
        return "\n".join(
            p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
        )
    except Exception as e:
        print(f"Error fetching article at {url}: {e}")
        return ""

@st.cache_data(ttl=3600)
def fetch_all_articles():
    all_articles = []

    for source_name, feed_url in rss_sources.items():
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            published_struct = getattr(entry, "published_parsed", None) or getattr(
                entry, "updated_parsed", None
            )
            if not published_struct:
                continue

            published_date = datetime.fromtimestamp(time.mktime(published_struct))
            if published_date < datetime.now() - timedelta(days=300):
                continue

            title_clean = BeautifulSoup(
                getattr(entry, "title", ""), "html.parser"
            ).get_text()

            raw_summary = getattr(entry, "summary", "") or getattr(
                entry, "description", ""
            )
            summary_clean = clean_html(raw_summary)

            combined_text = f"{title_clean} {summary_clean}"

            all_articles.append(
                {
                    "title": title_clean,
                    "link": getattr(entry, "link", ""),
                    "published": getattr(entry, "published", "")
                    or getattr(entry, "updated", ""),
                    "summary": summary_clean,
                    "text": combined_text,
                    "source": source_name,
                }
            )

    return all_articles

# Sidebar selectbox
selected_area = st.sidebar.selectbox("Select therapy area", list(therapy_areas.keys()))

# Fetch articles once
all_articles = fetch_all_articles()

# Group by therapy area
grouped_articles = {area: [] for area in therapy_areas.keys()}

for article in all_articles:
    for area, keywords in therapy_areas.items():
        full_text = article["text"] + " " + fetch_full_article_text(article["link"])
        if matches_therapy_area(full_text, keywords):
            grouped_articles[area].append(article)

# Display
st.subheader(selected_area)
articles = grouped_articles[selected_area]

if not articles:
    st.write("_No articles found in the past  days_")
else:
    for art in articles:
        st.markdown(f"### [{art['title']}]({art['link']})")
        st.write(f"**Published:** {art['published']}")
        st.write(art["summary"])
        st.markdown("---")
