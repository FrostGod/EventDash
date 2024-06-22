import time
from duckduckgo_search import DDGS
import json


def get_locations(service_name, city):
    results = DDGS().maps("Venues", city="Berkeley", max_results=5)
    print(results[0])
    # assert 27 <= len(results) <= 30
    formatted_results = []
    for result in results:
        temp_image = get_image(result.get("title"))
        formatted_result = {
            "name": result.get("title"),
            "address": result.get("address"),
            "rating": result.get("rating"),
            "phone": result.get("phone"),
            "website": result.get("website"),
            "email": result.get("email"),
            "images": temp_image
        }
        formatted_results.append(formatted_result)
    
    # Convert the formatted results to JSON format
    json_results = json.dumps(formatted_results, indent=4)
    print(json_results)
    return json_results

def test_text():
    results = DDGS().text("python programming", max_results=5)

def get_image(name):
  results = DDGS().images(name, max_results=2)
  images = []
  for result in results:
    images.append(result["image"])
  # print(results)
  return images
    


if __name__ == "__main__":
    get_locations("venues", "berkley")
    # get_image()
    # test_text()

