import streamlit as st
import feedparser
import json

# ---- Load RSS feeds from file ----
with open("rss_sources.json", "r") as f:
    rss_sources = json.load(f)

st.title("Pharma News Dashboard 📰")
st.write("This dashboard pulls the latest pharma news from selected sources.")

# ---- Sidebar to pick a source ----
source = st.sidebar.selectbox("Choose a news source", list(rss_sources.keys()))

# ---- Fetch articles ----
feed_url = rss_sources[source]
feed = feedparser.parse(feed_url)

st.subheader(f"Latest articles from {source}")

# ---- Display each article ----
for entry in feed.entries[:10]:  # Show only the 10 most recent
    st.markdown(f"### [{entry.title}]({entry.link})")
    st.write(f"**Published:** {entry.published}")
    st.write(entry.summary)
    st.markdown("---")
