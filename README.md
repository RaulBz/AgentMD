# AgentMD
An LLM-powered assistant for medical queries. Find top doctors by specialty and city, explore patient reviews, and get tailored answers. Uses agentic tool selection and retrieval-augmented responses. Built with LangGraph, Python, and Google Gemini—flexible for future healthcare tools.

## Setup
1. Clone the repo: `git clone git@github.com:yourusername/AgentMD.git`
2. Create a virtual env: `python -m venv venv && source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and add your API keys (see [docs/api_keys.md](docs/api_keys.md)).
5. Run: `python agent_md.py`

## 🚧 **Work in Progress** 🚧

This project is currently under active development and at it's infancy. Features, API endpoints, and functionality may change frequently.  
Expect changes in the comming days.

## Data Disclaimer
AgentMD is a proof-of-concept chatbot for educational purposes. Any web scraping functionality (e.g., fetching doctor data or reviews) is provided as-is. Users are responsible for complying with the terms of service, privacy policies, and applicable laws of any websites accessed. The author is not liable for misuse, data accuracy, or legal consequences arising from scraping or use of this code.

This chatbot retrieves publicly available doctor information from RateMDs. The data is for informational purposes only and does not constitute medical advice or an endorsement of any specific doctor or medical practice. 

The chatbot does not store or modify doctor reviews but simply presents publicly accessible information. Users should verify details directly from official sources.

If you are the owner of any listed information and would like it updated or removed, please contact the appropriate data provider.

## Requirements
- Python 3.8+
- See `requirements.txt`

## License
GNU Affero General Public License v3.0 (see `LICENSE`)

## Disclaimer
AgentMD is a proof-of-concept chatbot for educational purposes. Any web scraping functionality (e.g., fetching doctor data or reviews) is provided as-is. Users are responsible for complying with the terms of service, privacy policies, and applicable laws of any websites accessed. The author is not liable for misuse, data accuracy, or legal consequences arising from scraping or use of this code.
