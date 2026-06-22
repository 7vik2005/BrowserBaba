import requests
import sys
import io

def test_full_flow():
    # Force UTF-8 output encoding for Windows terminals
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 1. Ingest
    ingest_url = "http://127.0.0.1:8000/api/ingest"
    ingest_payload = {
        "url": "http://test-ipl.com",
        "domain": "test-ipl.com",
        "title": "The Indian Premier League (IPL)",
        "content": "The first season of the Indian Premier League (IPL) was held in the year 2008. Rajasthan Royals won the first season."
    }
    print("Ingesting page...")
    ingest_res = requests.post(ingest_url, json=ingest_payload)
    print("Ingest status:", ingest_res.status_code)
    print("Ingest response:", ingest_res.json())

    # 2. Chat
    chat_url = "http://127.0.0.1:8000/api/chat"
    chat_payload = {
        "url": "http://test-ipl.com",
        "domain": "test-ipl.com",
        "question": "when was the first season of ipl held?",
        "mode": "page",
        "chat_history": []
    }
    print("Sending chat question...")
    chat_res = requests.post(chat_url, json=chat_payload)
    print("Chat status:", chat_res.status_code)
    print("Chat response headers:", chat_res.headers)
    try:
        print("Chat response:", chat_res.json())
    except Exception as e:
        print("Error parsing chat response:", e)
        print("Raw text:", chat_res.text)

if __name__ == "__main__":
    test_full_flow()
