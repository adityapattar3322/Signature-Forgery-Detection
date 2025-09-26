import streamlit as st
import cv2
import numpy as np
import os
import joblib
from skimage.feature import hog, local_binary_pattern
import mysql.connector
import bcrypt
import base64

# --- Function to Set Local Background Image (Corrected CSS) ---
def set_background(image_file):
    """
    Sets a background image from a local file.

    Args:
        image_file (str): The path to the image file.
    """
    if not os.path.exists(image_file):
        st.error(f"Background image not found at {image_file}")
        return
        
    with open(image_file, "rb") as f:
        img_bytes = f.read()
    
    encoded_img = base64.b64encode(img_bytes).decode()
    
    # Get the correct image type from the filename extension
    file_extension = os.path.splitext(image_file)[1].lower()
    if file_extension in [".jpg", ".jpeg"]:
        image_type = "jpeg"
    elif file_extension == ".png":
        image_type = "png"
    elif file_extension == ".avif":
        image_type = "avif"
    else:
        # Default or error
        image_type = "jpeg"

    page_bg_img_style = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&family=Poppins:wght@400;600&display=swap');

    /* --- Custom Font Styles --- */
    
    /* Default font for the entire app */
    html, body, [class*="st-"], [class*="css-"] {{
        font-family: 'Poppins', sans-serif;
        font-size: 16px;
    }}

    /* Class for the main calligraphic title */
    .calligraphic-title {{
        font-family: 'Dancing Script', cursive;
        font-size: 3rem; /* Larger font size for the main title */
        font-weight: 700;
        text-align: center; /* Center align the title */
        padding-bottom: 1rem;
    }}

    /* Class for the calligraphic subtitle */
    .calligraphic-subtitle {{
        font-family: 'Dancing Script', cursive;
        font-size: 2.2rem; /* Slightly smaller for the subtitle */
        font-weight: 700;
    }}
    /* -------------------------- */


    /* --- Existing Background Styles --- */
    .stApp {{
        background-image: url("data:image/{image_type};base64,{encoded_img}");
        background-size: cover;
        background-attachment: fixed;
    }}
    
    [data-testid="stAppViewContainer"] > .main {{
        background-color: rgba(240, 242, 246, 0.85); /* Light gray with 85% opacity */
        border-radius: 10px;
        padding: 2rem;
    }}
    </style>
    """
    st.markdown(page_bg_img_style, unsafe_allow_html=True)


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

# --- Database and Authentication Logic ---

def get_db_connection():
    """Establishes a connection to the MySQL database using Streamlit secrets."""
    try:
        db_config = st.secrets["database"]
        conn = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["db_name"],
            port=db_config["port"]
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Error connecting to database: {err}")
        return None
    except Exception as e:
        st.error(f"Configuration Error: Please check your `.streamlit/secrets.toml` file. Details: {e}")
        return None

def hash_password(password):
    """Hashes the password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(plain_password, hashed_password):
    """Verifies a plain password against a stored hashed password."""
    # Ensure hashed_password is bytes
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def check_credentials(username, password):
    """Checks if the provided username and password are correct by querying the database."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        if result:
            return verify_password(password, result[0])
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def add_user(username, password):
    """Adds a new user to the database with a hashed password."""
    conn = get_db_connection()
    if conn is None: return False, "Database connection failed."
    try:
        cursor = conn.cursor(buffered=True)
        # Check if user already exists
        cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return False, "Username already exists."
        
        # Insert new user
        hashed_pw = hash_password(password)
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_pw.decode('utf-8')))
        conn.commit()
        return True, "User registered successfully!"
    except mysql.connector.Error as err:
        return False, f"Database error: {err}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- Streamlit Application ---

st.set_page_config(page_title="Signature Forgery Detection", layout="wide")

# Set the background using your uploaded wallpaper
# <<< --- THIS IS THE CORRECTED LINE --- >>>
set_background('wallpaper.jpg')

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- Authentication Page (Sign In & Sign Up) ---
def authentication_page():
    st.markdown("<h1 class='calligraphic-title'>Signature Forgery Detection System</h1>", unsafe_allow_html=True)

    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        st.markdown("<h2 class='calligraphic-subtitle'>Welcome to the Future of Signature Verification</h2>", unsafe_allow_html=True)
        st.markdown("""
        This advanced system leverages a Machine Learning Model to provide accurate and reliable detection of Signature Forgeries.
        
        Please sign in or create an account on the right to get started.
        """)

    with right_col:
        st.write("Access your account or create a new one to begin.")
        
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])

        with tab1:
            st.subheader("Sign In")
            with st.form("login_form"):
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Sign In")
                if submitted:
                    if check_credentials(username, password):
                        st.session_state.logged_in = True
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

        with tab2:
            st.subheader("Create a New Account")
            with st.form("signup_form"):
                new_username = st.text_input("Choose a Username", key="signup_username")
                new_password = st.text_input("Choose a Password", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
                signup_submitted = st.form_submit_button("Sign Up")
                if signup_submitted:
                    if not new_username or not new_password or not confirm_password:
                        st.warning("Please fill out all fields.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        success, message = add_user(new_username, new_password)
                        if success:
                            st.success(message + " You can now sign in using the 'Sign In' tab.")
                        else:
                            st.error(message)

# --- Main Application Page ---
def signature_detection_app():
    with st.sidebar:
        st.title("About the App")
        st.write("This application uses a Machine Learning model to distinguish between genuine and forged signatures.")
        st.info("Upload an image to get started!")
        st.markdown("---")
        st.header("Model Details")
        st.write("**Model:** Support Vector Machine (SVM)")
        st.write("**Features:** HOG + LBP")
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("<h1 class='calligraphic-title'>✍️ Signature Forgery Detection</h1>", unsafe_allow_html=True)
    st.write("Upload a signature image and the model will predict if it's Genuine or Forged.")

    MODEL_FILENAME = "signature_model.joblib"
    if not os.path.exists(MODEL_FILENAME):
        st.error(f"Error: Model file '{MODEL_FILENAME}' not found!")
    else:
        model = joblib.load(MODEL_FILENAME)
        uploaded_file = st.file_uploader("Choose a signature image...", type=["png", "jpg", "jpeg", "avif"], label_visibility="collapsed")

        if uploaded_file is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Uploaded Signature")
                st.image(uploaded_file.getvalue(), use_container_width=True)
            with col2:
                st.subheader("Prediction Analysis")
                with st.spinner('Analyzing...'):
                    processed_image, _ = preprocess_single_image(uploaded_file.getvalue())
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
                        
                        st.metric(label="Confidence Score", value=f"{confidence:.2f}%")
                        st.progress(int(confidence))

                        with st.expander("Show Preprocessed Image"):
                            st.image(processed_image, caption="Binarized & Resized Image (Model Input)", use_container_width=True)
                    else:
                        st.error("Could not process the uploaded image.")

# --- Page Router ---
if not st.session_state.logged_in:
    authentication_page()
else:
    signature_detection_app()