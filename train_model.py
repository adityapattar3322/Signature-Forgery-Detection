# app.py (Dynamic UI Version)

import streamlit as st
import cv2
import numpy as np
import os
import joblib
from skimage.feature import hog, local_binary_pattern

# --- Helper Functions (No changes needed here) ---

def preprocess_single_image(image_bytes, image_size=(256, 128)):
    """ Preprocesses a single image from bytes for prediction. """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is not None:
        resized_img = cv2.resize(img, image_size)
        _, binarized_img = cv2.threshold(resized_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return binarized_img, cv2.resize(img, (400, 200)) # Return original resized for display
    return None, None

def extract_single_feature(image):
    """ Extracts features from a single preprocessed image. """
    hog_features = hog(image, orientations=9, pixels_per_cell=(8, 8),
                       cells_per_block=(2, 2), block_norm='L2-Hys')
    lbp = local_binary_pattern(image, P=24, R=8, method="uniform")
    (lbp_hist, _) = np.histogram(lbp.ravel(), bins=np.arange(0, 27), range=(0, 26))
    lbp_hist = lbp_hist.astype("float")
    lbp_hist /= (lbp_hist.sum() + 1e-7)
    combined_features = np.hstack([hog_features, lbp_hist])
    return combined_features.reshape(1, -1)

# --- Streamlit Web Application Interface ---

# Set page configuration
st.set_page_config(page_title="Signature Forgery Detection", layout="wide")

# --- Sidebar ---
with st.sidebar:
    st.title("About the App")
    st.write("""
        This application uses a **Support Vector Machine (SVM)** model to distinguish between genuine and forged signatures.
        
        The model was trained on the CEDAR dataset and uses a combination of **HOG (Histogram of Oriented Gradients)** and **LBP (Local Binary Patterns)** features to analyze the signature's texture and shape.
    """)
    st.info("Upload an image to get started!")
    st.markdown("---")
    st.header("Model Details")
    st.write("**Model:** Support Vector Machine (SVM)")
    st.write("**Features:** HOG + LBP")
    st.write("**Dataset:** CEDAR (subset)")


# --- Main Page ---
st.title("✍️ Signature Forgery Detection")
st.write("Upload a signature image and the model will predict if it's Genuine or Forged.")

MODEL_FILENAME = "signature_model.joblib"

if not os.path.exists(MODEL_FILENAME):
    st.error(f"Error: Model file '{MODEL_FILENAME}' not found! Please run `train_model.py` to create it.")
else:
    model = joblib.load(MODEL_FILENAME)
    
    uploaded_file = st.file_uploader("Choose a signature image...", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

    if uploaded_file is not None:
        image_bytes = uploaded_file.getvalue()
        
        # Create columns for a side-by-side view
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Uploaded Signature")
            st.image(image_bytes, use_container_width=True)
        
        with col2:
            st.subheader("Prediction Analysis")
            with st.spinner('Analyzing...'):
                processed_image, display_image = preprocess_single_image(image_bytes)
                
                if processed_image is not None:
                    feature_vector = extract_single_feature(processed_image)
                    prediction = model.predict(feature_vector)
                    probabilities = model.predict_proba(feature_vector)
                    
                    if prediction[0] == 1:
                        result = "Genuine"
                        confidence = probabilities[0][1] * 100
                        st.success(f"**Prediction: {result}**")
                    else:
                        result = "Forged"
                        confidence = probabilities[0][0] * 100
                        st.error(f"**Prediction: {result}**")
                    
                    # Display confidence with st.metric for a nicer look
                    st.metric(label="Confidence Score", value=f"{confidence:.2f}%")
                    st.progress(int(confidence))

                    # Expander to show what the model "sees"
                    with st.expander("Show Preprocessed Image"):
                        st.image(processed_image, caption="Binarized & Resized Image (Model Input)", use_container_width=True)
                else:
                    st.error("Could not process the uploaded image.")