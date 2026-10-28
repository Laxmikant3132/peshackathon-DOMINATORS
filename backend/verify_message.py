import requests

def test_message(body):
    url = "https://humanfirewall-backend.onrender.com/api/classify-email"
    payload = {"emailBody": body}
    response = requests.post(url, json=payload)
    print(f"Body: {body[:50]}...")
    print(f"Response: {response.json()}\n")

# Test cases
test_message("Your bank account has been suspended. Please login to verify: http://bit.ly/fakebank")
test_message("Dear customer, you have won a lottery of $1,000,000! Share OTP to claim.")
test_message("Your transaction of Rs. 500 to John was successful. Transaction ID: 12345.")
test_message("Hey, can we meet for lunch today?")
