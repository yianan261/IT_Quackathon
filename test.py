import requests

response = requests.get("http://localhost:8000/")
print("Root endpoint:", response.status_code)

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "messages": [{
            "role":
            "user",
            "content":
            "What are my upcoming assignments for probability class?"
        }]
    })

if response.status_code != 200:
    print(f"Status Code: {response.status_code}")
    print(f"Error: {response.text}")
else:
    print(response.json())
