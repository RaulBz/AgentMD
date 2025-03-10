# tools.py
from langchain_core.tools import tool
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from config import Config
from langchain_core.messages.ai import AIMessage
import requests
import time


class ChatBioGPT:
    def __init__(self, api_token, model="microsoft/biogpt"):
        self.url = f"https://api-inference.huggingface.co/models/{model}"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.tools = None  # Placeholder for tool binding compatibility

    def invoke(self, messages):
        # Convert message history to a single prompt
        prompt = ""
        for msg in messages:
            if isinstance(msg, tuple) and msg[0] == "system":
                prompt += f"System: {msg[1]}\n"
            elif isinstance(msg, tuple) and msg[0] == "user":
                prompt += f"User: {msg[1]}\n"
            elif hasattr(msg, "content"):
                prompt += f"{msg.content}\n"
        
        payload = {
            "inputs": prompt,
            "parameters": {"max_length": 200, "temperature": 0.7}
        }
        response = requests.post(self.url, headers=self.headers, json=payload)
        if response.status_code == 200:
            text = response.json()[0]["generated_text"]
            return AIMessage(content=text)  # Return in LangChain-compatible format
        else:
            return AIMessage(content=f"Error: API call failed ({response.status_code})")

    def bind_tools(self, tools):
        # Minimal tool-binding shim
        self.tools = tools
        return self


@tool
def fetch_doctors_tool(specialty: str, city: str, max_results: int = 3) -> str:
    """
    Uses Selenium to fetch top doctors for a specialty and city.
    Returns a formatted string with doctor information.
    """
    base_url = "https://www.ratemds.com"
    search_url = f"{base_url}/best-doctors/on/{city}/{specialty}/"
    print(f"Fetching data from: {search_url}")

    # Set up Selenium WebDriver options
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    # Initialize WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Load the webpage
        driver.get(search_url)

        # Wait for doctor listings to load
        doctor_containers = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "doctor-container"))
        )

        # Extract information about the top doctors
        doctors = []
        for doctor in doctor_containers[:max_results]:
            try:
                name = doctor.find_element(By.CLASS_NAME, "search-item-doctor-name").text
                specialty = doctor.find_element(By.CLASS_NAME, "search-item-specialty-text").text
                
                # Handle location
                try:
                    location = doctor.find_element(By.CLASS_NAME, "doctor-address").text
                except:
                    location = "Location not provided"

                # Handle profile URL
                try:
                    profile_url = doctor.find_element(By.CLASS_NAME, "search-item-doctor-name").get_attribute("href")
                    if not profile_url.startswith("https://"):
                        profile_url = f"https://www.ratemds.com{profile_url}"
                except:
                    profile_url = "No profile URL"

                # Handle rating
                try:
                    rating_element = doctor.find_element(By.CLASS_NAME, "star-rating")
                    rating = rating_element.get_attribute("title")
                except:
                    rating = "No rating"

                # Handle reviews
                try:
                    reviews_element = doctor.find_element(By.CLASS_NAME, "reviews")
                    reviews = reviews_element.text.strip("()")
                except:
                    reviews = "No reviews"

                doctors.append({
                    "name": name,
                    "specialty": specialty,
                    "location": location,
                    "rating": rating,
                    "reviews": reviews,
                    "profile_url": profile_url,
                })
            except Exception as e:
                print(f"Error extracting data: {e}")
                continue

        # If no doctors were found, return a message
        if not doctors:
            return f"No doctors found for the specialty '{specialty}' in {city}."

        # Format the response
        response = f"Top {max_results} {specialty.capitalize()}s in {city.capitalize()}, Ontario:\n"
        for idx, doc in enumerate(doctors, start=1):
            response += (
                f"{idx}. {doc['name']}\n"
                f"   Specialty: {doc['specialty']}\n"
                f"   Location: {doc['location']}\n"
                f"   Rating: {doc['rating']} ({doc['reviews']} reviews)\n"
                f"   Profile: {doc['profile_url']}\n\n"
            )

        return response.strip()

    except Exception as e:
        return f"Error fetching doctors: {e}"

    finally:
        driver.quit()


@tool
def retrieve_reviews_tool(search_url: str) -> str:
    """
    The input is a string containing the url as a stringcorresponding to a doctor's profile to find all the reviews 
    about the doctor on the website combine them and return them as a string
    """
    print(f"Fetching data from: {search_url}")
    # Set up Selenium WebDriver options
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")


    # Initialize WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(search_url)
        
        # Wait for at least one rating comment body to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "rating-comment-body"))
        )

        # Small delay to ensure all elements are loaded
        time.sleep(2)

        reviews = []
        # Get all review containers fresh each time
        rating_containers = driver.find_elements(By.CLASS_NAME, "rating-comment-body")

        print(f"Found {len(rating_containers)} review containers")
        
        for i, container in enumerate(rating_containers, 1):

            try:

                # Get the paragraph text from the current container
                review_text = container.find_element(By.TAG_NAME, "p").text
                if review_text:  # Only append non-empty reviews
                    reviews.append(review_text)
                    #print(f"Successfully extracted review {i}") # Implement a counter in the future for a one time less verbose output that mentions how many reviews were retrieved in total.
                else:
                    print(f"Review {i} was empty")
            except Exception as e:
                print(f"Error extracting review {i}: {str(e)}")
                continue

    finally:
        driver.quit()

    # Create formatted string for all_reviews
    all_reviews = "\nExtracted Reviews:\n" + "=" * 50 + "\n"
    for i, review in enumerate(reviews, 1):
        all_reviews += f"Review {i}:\n{review}\n" + "-" * 50 + "\n"
    all_reviews += f"Total reviews extracted: {len(reviews)}"

    return all_reviews