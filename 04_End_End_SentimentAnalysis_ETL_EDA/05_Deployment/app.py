import joblib
from utils.process_text import CleanText, LemmatizeWithPos

import numpy as np

from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# Loading preprocessing techniques and machine learning model
with open("models/01_tfidf_vectorizer_fitted.joblib", "rb") as vFile:
    vectorizer = joblib.load(vFile)

with open("models/02_chi2_250_feature_selector_fitted.joblib", "rb") as fsFile:
    feature_selector = joblib.load(fsFile)

with open("models/03_random_forest_model_fitted.joblib", "rb") as rfFile:
    random_forest_clf = joblib.load(rfFile)

# Map the machine learning output into something more friendly
map_class = {

    0:"Negative",
    1:"Other",
    2:"Positive"

}

# Initialize the cleaner of the text supplied in the front-end (by the user)
cleaner = CleanText()

@app.route("/")
def home():
    return render_template("home.html")

@app.route('/predict', methods=['POST'])
def predict():

    # Retrieving, cleaning and getting lemmas of the request
    text_received = request.get_json()["text"]
    text_cleaned = cleaner.Cleaner(text_received)
    text_lemma_str = LemmatizeWithPos(text_cleaned, as_list = False)

    # Predicting
    X = vectorizer.transform([text_lemma_str])
    X = feature_selector.transform(X)
    prediction = random_forest_clf.predict(X)[0]
    prediction = map_class[prediction]

    return jsonify({"prediction_text": f"Polarity: {prediction}"})

if __name__ == "__main__":
    app.run(debug = True)
