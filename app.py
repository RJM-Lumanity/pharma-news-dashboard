import streamlit as st
import feedparser
import json
from bs4 import BeautifulSoup

# ---- Load RSS feeds ----
with open("rss_sources.json", "r") as f:
    rss_sources = json.load(f)

st.title("Pharma News Dashboard 📰")
st.write("This dashboard pulls the latest pharma news from selected sources.")

# ---- Sidebar ----
source = st.sidebar.selectbox("Choose a news source", list(rss_sources.keys()))
feed_url = rss_sources[source]
feed = feedparser.parse(feed_url)

st.subheader(f"Latest articles from {source}")

def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    for img in soup.find_all("img"):
        img.decompose()  # remove images
    return soup.get_text()

# ---- Display Articles ----
for entry in feed.entries[:10]:
    # Clean title if it contains HTML
    raw_title = entry.title
    clean_title = BeautifulSoup(raw_title, "html.parser").get_text()

    st.markdown(f"### [{clean_title}]({entry.link})")
    st.write(f"**Published:** {entry.published}")

    if hasattr(entry, "summary"):
        summary_text = clean_html(entry.summary)
        st.write(summary_text.strip())
    else:
        st.write("_No summary available_")

    st.markdown("---")
