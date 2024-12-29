import requests

# URL API
url = "https://Kociebor.pythonanywhere.com/history"

# Dane do wysłania
data = {
  "login": "beta",
  "password": "1234"
}

# Wysyłanie żądania POST
response = requests.post(url, json=data)

# Wyświetlenie odpowiedzi
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")