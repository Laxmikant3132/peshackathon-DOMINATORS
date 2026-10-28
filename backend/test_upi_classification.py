
import requests

def test_email_classification(email_body):
    url = "http://127.0.0.1:8001/api/classify-email"
    payload = {"emailBody": email_body}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}, {response.text}"

# Test cases
upi_safe = """
Dear User, 
Your UPI transaction of Rs. 500 to John Doe was successful. 
Transaction ID: 123456789012. 
Bank: State Bank of India.
"""

upi_dangerous = """
URGENT: Your UPI account is suspended. 
To reactivate, click here: http://suspicious-upi-verify.com/login 
Enter your UPI PIN to verify your identity and receive Rs. 10000 refund.
"""

if __name__ == "__main__":
    # Note: Need to start the server first
    try:
        print("Testing Safe UPI Email:")
        print(test_email_classification(upi_safe))
        print("\nTesting Dangerous UPI Email:")
        print(test_email_classification(upi_dangerous))
    except Exception as e:
        print(f"Error connecting to server: {e}")
