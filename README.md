# AgentMD
An LLM-powered assistant for medical queries. Find top doctors  in Ontario by specialty and city, explore patient reviews, and get tailored answers. Uses agentic tool selection and retrieval-augmented responses. Built with LangGraph, Python, and Google Gemini—flexible for future healthcare tools.

## How to use AgentMD (Example Interaction):

AgentMD helps you find top doctors in a city and dive into their reviews for detailed insights. Here’s an example of how to use it:

**User**: Find the top 3 urologists in London.  
**AgentMD**:  
Top 3 Urologists in London, Ontario:  
1. Dr. Stephen Pautler  
   Specialty: Urologist  
   Location: St. Joseph's Hospital, 268 Grosvenor Street, London, ON  
   Rating: 4.8 (30 reviews)  
   Profile: https://www.ratemds.com/doctor-ratings/[id]/Dr-Stephen-Pautler-London-ON.html/  

2. Dr. Hassan Razvi  
   Specialty: Urologist  
   Location: St. Joseph's Hospital, 268 Grosvenor Street, London, ON  
   Rating: 4.7 (25 reviews)  
   Profile: https://www.ratemds.com/doctor-ratings/[id]/Dr-Hassan-Razvi-London-ON.html/  

3. Dr. Nicholas Power  
   Specialty: Urologist  
   Location: Victoria Hospital, 800 Commissioners Road East, London, ON  
   Rating: 4.6 (20 reviews)  
   Profile: https://www.ratemds.com/doctor-ratings/[id]/Dr-Nicholas-Power-London-ON.html/

**User**: How many reviews does Dr. Stephen Pautler have, and do people think the post-operation is bad?  
**AgentMD**:  
Dr. Stephen Pautler has 30 reviews.  
Extracted Reviews:  
- Review 1: "Dr. Pautler was excellent, but the post-operation recovery was tougher than expected—lots of swelling."  
- Review 2: "The surgery went well, and post-op care was great. No complaints!"  
- Review 3: "Post-operation was a bit painful, but Dr. Pautler’s team was supportive."  
Summary: Some patients found post-operation challenging (e.g., swelling, pain), but others had a positive experience with good support.

**User**: Does Dr. Hassan Razvi have experience with kidney stone treatment?  
**AgentMD**:  
Extracted Reviews:  
- Review 1: "Dr. Razvi handled my kidney stone surgery with precision. Highly recommend!"  
- Review 2: "Had a great experience with Dr. Razvi for kidney stone removal—very knowledgeable."  
Summary: Yes, Dr. Hassan Razvi has experience with kidney stone treatment, and patients report positive outcomes.

**User**: Did Dr. Nicholas Power’s surgery leave a scar?  
**AgentMD**:  
Extracted Reviews:  
- Review 1: "The surgery with Dr. Power went well, but it did leave a small scar."  
- Review 2: "Minimally invasive procedure—no noticeable scarring!"  
Summary: Experiences vary; some patients report a small scar, while others mention minimal or no scarring.

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
