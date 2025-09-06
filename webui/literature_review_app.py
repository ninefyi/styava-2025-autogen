import streamlit as st
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import arxiv

load_dotenv()

def google_search(query: str, num_results: int = 2, max_chars: int = 500):
    api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": api_key, "cx": search_engine_id, "q": query, "num": num_results}
    response = requests.get(url, params=params)
    results = response.json().get("items", [])
    def get_page_content(url: str) -> str:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            words = text.split()
            content = ""
            for word in words:
                if len(content) + len(word) + 1 > max_chars:
                    break
                content += " " + word
            return content.strip()
        except Exception as e:
            return ""
    enriched_results = []
    for item in results:
        body = get_page_content(item["link"])
        enriched_results.append(
            {"title": item["title"], "link": item["link"], "snippet": item["snippet"], "body": body}
        )
    return enriched_results

def arxiv_search(query: str, max_results: int = 2):
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
    results = []
    for paper in client.results(search):
        results.append(
            {
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "published": paper.published.strftime("%Y-%m-%d"),
                "abstract": paper.summary,
                "pdf_url": paper.pdf_url,
            }
        )
    return results

st.title("Literature Review App")

topic = st.text_input("Enter topic for literature review:", "no code tools for building multi agent ai systems")

search_arxiv_clicked = st.button("Search Arxiv")
search_google_clicked = st.button("Search Google")

if search_arxiv_clicked:
    st.session_state['show'] = 'arxiv'
elif search_google_clicked:
    st.session_state['show'] = 'google'

with st.container():
    if st.session_state.get('show') == 'arxiv':
        with st.spinner("Loading..."):
            results = arxiv_search(topic)
            st.subheader("Arxiv Search Results")
            for r in results:
                st.markdown(f"**{r['title']}**")    
                st.write(f"Authors: {', '.join(r['authors'])}")
                st.write(f"Published: {r['published']}")
                st.write(r['abstract'])
                st.write(f"[PDF Link]({r['pdf_url']})")
                st.write("---")
    elif st.session_state.get('show') == 'google':
        with st.spinner("Loading..."):
            results = google_search(topic)
            st.subheader("Google Search Results")
            for r in results:
                st.markdown(f"**{r['title']}**")
                st.write(r['snippet'])
                st.write(r['body'])
                st.write(f"[Link]({r['link']})")
                st.write("---")