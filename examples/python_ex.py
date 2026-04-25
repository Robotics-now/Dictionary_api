import requests

user_input = input("Enter a word to look up: ")

api_url = f"http://localhost:8000/api/{user_input}"
response = requests.get(api_url)
data = response.json()

if response.status_code == 200:
    data = response.json()
    print(f"The definition of the '{data['word']}' is: {data['def']}")
