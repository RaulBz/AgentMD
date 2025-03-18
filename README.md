<p align="center">
  <img src="images/Agent_MD_logo.png" alt="AgentMD Logo" width="200"/>
</p>

# AgentMD
An LLM-powered assistant for medical queries. Find top doctors  in Ontario by specialty and city, explore patient reviews, and get tailored answers. Uses agentic tool selection and retrieval-augmented responses. Built with LangGraph, Python, and Google Gemini—flexible for future healthcare tools.

## How to Use AgentMD (Example Interaction)

AgentMD helps you find top doctors in a city and dive into their reviews for detailed insights. Here’s an example:

---

**User**: Find the top 3 urologists in Ottawa.  
**AgentMD**:  
Here are the top 3 urologists in Ottawa, ON:  

1. **Dr. James Taylor**  
   - **Location**: Ottawa Riverside Clinic, 150 Wellness Drive  
   - **Rating**: 4.8 (30 reviews)  
   - **Profile**: [Dr. James Taylor](https://www.examplemed.com/doctor-ratings/[id]/Dr-James-Taylor-Ottawa-ON.html)  

2. **Dr. Laura Bennett**  
   - **Location**: Ottawa Riverside Clinic, 150 Wellness Drive  
   - **Rating**: 4.7 (25 reviews)  
   - **Profile**: [Dr. Laura Bennett](https://www.examplemed.com/doctor-ratings/[id]/Dr-Laura-Bennett-Ottawa-ON.html)  

3. **Dr. Robert Evans**  
   - **Location**: Capital Health Center, 300 Harmony Street  
   - **Rating**: 4.6 (20 reviews)  
   - **Profile**: [Dr. Robert Evans](https://www.examplemed.com/doctor-ratings/[id]/Dr-Robert-Evans-Ottawa-ON.html)  

---

**User**: How many reviews does Dr. James Taylor have, and do people think the post-operation is bad?  
**AgentMD**:  
- **Reviews**: Dr. James Taylor has 30 reviews.  
- **Post-Operation Feedback**:  
  - _"Dr. Taylor was excellent, but the post-operation recovery was tougher than expected—lots of swelling."_  
  - _"The surgery went well, and post-op care was great. No complaints!"_  
  - _"Post-operation was a bit painful, but Dr. Taylor’s team was supportive."_  
- **Summary**: Some patients found post-operation challenging (e.g., swelling, pain), but others had a positive experience with good support.

---

**User**: Does Dr. Laura Bennett have experience with kidney stone treatment?  
**AgentMD**:  
- **Feedback**:  
  - _"Dr. Bennett handled my kidney stone surgery with precision. Highly recommend!"_  
  - _"Had a great experience with Dr. Bennett for kidney stone removal—very knowledgeable."_  
- **Summary**: Yes, Dr. Laura Bennett has experience with kidney stone treatment, with positive patient outcomes.

---

**User**: Did Dr. Robert Evans’s surgery leave a scar?  
**AgentMD**:  
- **Feedback**:  
  - _"The surgery with Dr. Evans went well, but it did leave a small scar."_  
  - _"Minimally invasive procedure—no noticeable scarring!"_  
- **Summary**: Experiences vary; some report a small scar, while others mention minimal or no scarring.

Try it out by running `python main.py` (terminal) or `python mainFastAPI.py` (web interface at `http://localhost:8000`)!

## Setup
1. Clone the repo: `git clone git@github.com:yourusername/AgentMD.git`
2. Create a virtual env: `python -m venv venv && source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and add your API keys (see [docs/api_keys.md](docs/api_keys.md)).
5. Run: `python main.py` to use the chat on terminal or `python mainFastAPI.py` to use the chrome chat version.

## 🚧 **Work in Progress** 🚧

This project is currently under active development and at it's infancy. Features, API endpoints, and functionality may change frequently.  
Expect changes in the comming days. The project structure will change to be more organized. With separate files for tools tools.py and graph defiinintion graph.py. And the Langraph graph will be expanded to have better flow beteen states. This should give users a better to have a more natural interaction with the chat.

## Future Features
1. Extend to work in other regions.
2. Improve and expand the graph.
3. Access to clinical tryal data.
4. Feature that let's you describe the ideal specialist and will go throught reviews and match your prefference to a specialist.

## Agent MD LangGraph Architecture

Below is a diagram of the current LangGraph workflow for AgentMD, generated from the code:

![AgentMD LangGraph](images/Agent_Md_graph.png)

### Explanation
- **start**: The entry point of the graph.
- **chatbot**: Processes user input, decides if a tool is needed (via `maybe_route_to_tools`), and generates responses.
- **tools**: Executes `fetch_doctors_tool` or `retrieve_reviews_tool` when called.
- **human**: Accepts user input (terminal in `main.py`, HTTP in `mainFastAPI.py`).
- **end**: Terminates the graph when no further action is needed.
- **Edges**: 
  - `start → chatbot`: Initial entry.
  - `chatbot → tools` if a tool call is detected.
  - `chatbot → human` for user input.
  - `chatbot → end` if no tool call.
  - `tools → chatbot` after execution.
- **Note**: The FastAPI version handles "human" input via web requests.

This structure supports queries like "Find the top 3 urologists in London" and follow-up questions.

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
