import streamlit as st
import cv2
import numpy as np
import os
import joblib
from skimage.feature import hog, local_binary_pattern
import mysql.connector
import bcrypt
import base64

# --- Function to Set Advanced Styling & Background ---
def set_styling(image_file):
    """
    Sets a background image and applies advanced CSS for a Glassmorphism UI.
    """
    if not os.path.exists(image_file):
        st.error(f"Background image not found at {image_file}")
        return
        
    with open(image_file, "rb") as f:
        img_bytes = f.read()
    
    encoded_img = base64.b64encode(img_bytes).decode()
    
    # Advanced CSS styling
    page_style = f"""
    <style>
    /* Import Fonts: Dancing Script (Headers) & Poppins (Body) */
    @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&family=Poppins:wght@300;400;600&display=swap');

    /* --- Global Styles --- */
    .stApp {{
        background-image: url("data:image/avif;base64,{encoded_img}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* --- Animations --- */
    @keyframes slideUpFade {{
        0% {{
            opacity: 0;
            transform: translateY(50px);
        }}
        100% {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes pulseGlow {{
        0% {{ box-shadow: 0 0 15px rgba(118, 75, 162, 0.3); }}
        50% {{ box-shadow: 0 0 25px rgba(118, 75, 162, 0.6); }}
        100% {{ box-shadow: 0 0 15px rgba(118, 75, 162, 0.3); }}
    }}

    /* --- Glassmorphism Main Container --- */
    .main .block-container {{
        background: rgba(0, 0, 0, 0.65);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 25px;
        padding: 3rem !important;
        /* Neon Glow Border */
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        max-width: 1100px;
        margin-top: 2rem;
        /* Apply Entrance Animation */
        animation: slideUpFade 1s ease-out forwards;
    }}

    /* --- Typography --- */
    h1, h2, h3 {{
        font-family: 'Dancing Script', cursive !important;
        font-weight: 700 !important;
    }}
    
    /* Gradient Title */
    h1 {{ 
        font-size: 4.5rem !important; 
        margin-bottom: 0.5rem !important; 
        background: linear-gradient(to right, #ffffff, #a8c0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 0px 20px rgba(168, 192, 255, 0.3);
    }}

    h2 {{ font-size: 2.8rem !important; color: #ffffff !important; }}
    h3 {{ font-size: 2rem !important; color: #e0e0e0 !important; }}

    p, label, .stMarkdown {{
        font-family: 'Poppins', sans-serif !important;
        color: #d1d1d1 !important;
        font-size: 1.1rem !important;
        line-height: 1.6;
    }}

    /* --- Interactive Input Fields --- */
    .stTextInput > div > div > input {{
        background-color: rgba(255, 255, 255, 0.9);
        color: #333 !important;
        border-radius: 12px;
        border: 2px solid transparent;
        padding: 12px 15px;
        font-size: 1rem;
        transition: all 0.3s ease;
    }}
    
    /* Focus Effect: Glows and expands slightly */
    .stTextInput > div > div > input:focus {{
        border-color: #764ba2;
        box-shadow: 0 0 15px rgba(118, 75, 162, 0.5);
        transform: scale(1.02);
        background-color: #ffffff;
    }}

    .stTextInput label {{
        font-weight: 600 !important;
        color: #ffffff !important;
        letter-spacing: 0.5px;
    }}

    /* --- Buttons --- */
    .stButton > button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-radius: 50px;
        border: none;
        padding: 0.7rem 2.5rem;
        font-size: 1.2rem !important;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 10px 25px rgba(118, 75, 162, 0.6);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }}

    /* --- Tabs --- */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        border-bottom: none;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: rgba(255,255,255,0.05);
        border-radius: 30px;
        color: #aaa;
        border: 1px solid rgba(255,255,255,0.1);
        padding: 10px 25px;
        transition: all 0.3s;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #764ba2 !important;
        color: white !important;
        border: 1px solid #764ba2;
        font-weight: bold;
        box-shadow: 0 0 15px rgba(118, 75, 162, 0.4);
    }}
    
    /* --- Sidebar --- */
    [data-testid="stSidebar"] {{
        background-color: rgba(15, 15, 20, 0.98);
        border-right: 1px solid rgba(255,255,255,0.05);
    }}
    </style>
    """
    st.markdown(page_style, unsafe_allow_html=True)

# --- Helper Functions ---
def preprocess_single_image(image_bytes, image_size=(256, 128)):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is not None:
        resized_img = cv2.resize(img, image_size)
        _, binarized_img = cv2.threshold(resized_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return binarized_img, cv2.resize(img, (400, 200))
    return None, None

def extract_single_feature(image):
    hog_features = hog(image, orientations=9, pixels_per_cell=(8, 8),
                       cells_per_block=(2, 2), block_norm='L2-Hys')
    lbp = local_binary_pattern(image, P=24, R=8, method="uniform")
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def check_credentials(username, password):
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
    conn = get_db_connection()
    if conn is None: return False, "Database connection failed."
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return False, "Username already exists."
        
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

# --- Main App Configuration ---

st.set_page_config(page_title="Signature Forgery Detection", layout="wide")

# Apply the new styling function
set_styling('wallpaper.jpg')

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- Authentication Page ---
def authentication_page():
    with st.container():
        st.markdown("<h1 style='text-align: center;'>Signature Forgery Detection System</h1>", unsafe_allow_html=True)
        st.write("") 

        left_col, right_col = st.columns([1.2, 1], gap="large")

        with left_col:
            st.markdown("<h2>Welcome to the Future of Signature Verification</h2>", unsafe_allow_html=True)
            st.markdown("""
            <div style='background-color: rgba(255,255,255,0.05); padding: 25px; border-radius: 20px; border-left: 6px solid #764ba2; box-shadow: 0 5px 15px rgba(0,0,0,0.2);'>
                This advanced system leverages a <strong>Support Vector Machine (SVM)</strong> model to provide accurate and reliable detection of signature forgeries.
                <br><br>
                It combines <em>HOG (Histogram of Oriented Gradients)</em> and <em>LBP (Local Binary Patterns)</em> to analyze unique texture and shape features.
                <br><br>
                Please sign in or create an account on the right to experience secure verification.
            </div>
            """, unsafe_allow_html=True)

        with right_col:
            st.markdown("<div style='padding: 10px;'>", unsafe_allow_html=True)
            st.write("Access your account or create a new one to begin.")
            
            tab1, tab2 = st.tabs(["Sign In", "Sign Up"])

            with tab1:
                st.write("")
                with st.form("login_form"):
                    username = st.text_input("Username", key="login_username")
                    password = st.text_input("Password", type="password", key="login_password")
                    st.write("")
                    submitted = st.form_submit_button("Sign In")
                    if submitted:
                        if check_credentials(username, password):
                            st.session_state.logged_in = True
                            st.success("Logged in successfully!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")

            with tab2:
                st.write("")
                with st.form("signup_form"):
                    new_username = st.text_input("Choose a Username", key="signup_username")
                    new_password = st.text_input("Choose a Password", type="password", key="signup_password")
                    confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
                    st.write("")
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
            st.markdown("</div>", unsafe_allow_html=True)

# --- Main Prediction Page ---
def signature_detection_app():
    with st.sidebar:
        st.markdown("<h3>About the App</h3>", unsafe_allow_html=True)
        st.write("This application uses an SVM model to distinguish between genuine and forged signatures.")
        st.info("Upload an image to get started!")
        st.markdown("---")
        st.markdown("<h3>Model Details</h3>", unsafe_allow_html=True)
        st.write("**Model:** Support Vector Machine (SVM)")
        st.write("**Features:** HOG + LBP")
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # Main Content
    st.markdown("<h1>✍️ Signature Forgery Detection</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background-color: rgba(255,255,255,0.1); padding: 15px; border-radius: 15px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1);'>
        Upload a signature image below. The AI model will analyze the strokes and texture to predict if it's <strong>Genuine</strong> or <strong>Forged</strong>.
    </div>
    """, unsafe_allow_html=True)

    MODEL_FILENAME = "signature_model.joblib"
    if not os.path.exists(MODEL_FILENAME):
        st.error(f"Error: Model file '{MODEL_FILENAME}' not found!")
    else:
        model = joblib.load(MODEL_FILENAME)
        
        uploaded_file = st.file_uploader("Choose a signature image...", type=["png", "jpg", "jpeg", "avif"], label_visibility="collapsed")

        if uploaded_file is not None:
            st.write("")
            col1, col2 = st.columns(2, gap="large")
            
            with col1:
                st.markdown("<h3>Uploaded Signature</h3>", unsafe_allow_html=True)
                st.image(uploaded_file.getvalue(), use_container_width=True)
            
            with col2:
                st.markdown("<h3>Prediction Analysis</h3>", unsafe_allow_html=True)
                with st.spinner('Analyzing signature patterns...'):
                    processed_image, _ = preprocess_single_image(uploaded_file.getvalue())
                    if processed_image is not None:
                        feature_vector = extract_single_feature(processed_image)
                        prediction = model.predict(feature_vector)
                        probabilities = model.predict_proba(feature_vector)
                        
                        if prediction[0] == 1:
                            result = "Genuine"
                            confidence = probabilities[0][1] * 100
                            st.markdown(f"""
                                <div style='background-color: rgba(0, 200, 83, 0.2); padding: 20px; border-radius: 15px; border: 2px solid #00c853; text-align: center; animation: pulseGlow 2s infinite;'>
                                    <h2 style='color: #00e676 !important; margin:0;'>Genuine</h2>
                                    <p style='margin:0;'>Confidence: <strong>{confidence:.2f}%</strong></p>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            result = "Forged"
                            confidence = probabilities[0][0] * 100
                            st.markdown(f"""
                                <div style='background-color: rgba(255, 23, 68, 0.2); padding: 20px; border-radius: 15px; border: 2px solid #ff1744; text-align: center; animation: pulseGlow 2s infinite;'>
                                    <h2 style='color: #ff5252 !important; margin:0;'>Forged</h2>
                                    <p style='margin:0;'>Confidence: <strong>{confidence:.2f}%</strong></p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        st.write("")
                        st.progress(int(confidence))

                        with st.expander("Show Preprocessed Image"):
                            st.image(processed_image, caption="Binarized & Resized Image (Model Input)", use_container_width=True)
                    else:
                        st.error("Could not process the uploaded image.")

# --- Router ---
if not st.session_state.logged_in:
    authentication_page()
else:
    signature_detection_app()