import joblib
import os
import re

model = joblib.load(r'D:\HumanFirewall\backend\models\email_classifier.joblib')

body = "Hi Team, Just a reminder that we have our weekly project meeting tomorrow at 10 AM in the conference room. Please bring your progress updates and any blockers you are facing. Thanks, Rahul"

prediction = model.predict([body])[0]

print(f"ML Prediction: {prediction}")