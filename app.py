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

def article_in_last_7_days(entry):
    try:
        published_struct = entry.published_parsed
        published_date = datetime.fromtimestamp(time.mktime(published_struct))
        return published_date >= datetime.now() - timedelta(days=7)
    except:
        return False

def matches_therapy_area(entry_text, keywords):
    text_lower = entry_text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)

# Sidebar selectbox for therapy area
selected_area = st.sidebar.selectbox("Select therapy area", list(therapy_areas.keys()))

# ---- Fetch all articles from all sources ----
all_articles = []
for source_name, feed_url in rss_sources.items():
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        if article_in_last_7_days(entry):
            title_clean = BeautifulSoup(entry.title, "html.parser").get_text()
            summary_clean = clean_html(entry.summary) if hasattr(entry, "summary") else ""
            combined_text = f"{title_clean} {summary_clean}"
            all_articles.append({
                "title": title_clean,
                "link": entry.link,
                "published": entry.published,
                "summary": summary_clean,
                "text": combined_text
            })

# ---- Group by therapy area ----
grouped_articles = {area: [] for area in therapy_areas.keys()}

for article in all_articles:
    for area, keywords in therapy_areas.items():
        if matches_therapy_area(article["text"], keywords):
            grouped_articles[area].append(article)

# ---- Display articles grouped by therapy area ----
for area, articles in grouped_articles.items():
    st.subheader(area)
    if not articles:
        st.write("_No articles found in the past 7 days_")
    else:
        for art in articles:
            st.markdown(f"### [{art['title']}]({art['link']})")
            st.write(f"**Published:** {art['published']}")
            st.write(art['summary'])
            st.markdown("---")
