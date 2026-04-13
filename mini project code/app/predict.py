import joblib
import os

model_path = os.path.join("model","cognitive_model.pkl")

model = joblib.load(model_path)

def predict_status(memory,concentration,digit,self_report):

    prediction = model.predict([[memory,concentration,digit,self_report]])

    return prediction[0]