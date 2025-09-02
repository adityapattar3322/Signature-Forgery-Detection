# train_model.py (FINAL CORRECTED VERSION)

import cv2
import os
import numpy as np
import joblib
from skimage.feature import hog, local_binary_pattern
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.svm import SVC
from sklearn.metrics import classification_report, accuracy_score

# --- Function to load and prepare images ---
def load_images(folder_path, label):
    data = []
    print(f"Loading images from: {folder_path}")
    if not os.path.exists(folder_path):
        print(f"Error: Folder not found at {folder_path}")
        return data

    for filename in os.listdir(folder_path):
        img_path = os.path.join(folder_path, filename)
        image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        
        if image is not None:
            # Standardize image size to (256, 128)
            image = cv2.resize(image, (256, 128)) 
            _, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            data.append((image, label))
        else:
            print(f"Warning: Could not read image -> {filename}")
            
    return data

# --- Function to extract features from images ---
def extract_features(images):
    features_list = []
    print("\nExtracting features from images...")
    for image in images:
        hog_features = hog(image, orientations=9, pixels_per_cell=(8, 8),
                           cells_per_block=(2, 2), block_norm='L2-Hys')
        
        lbp = local_binary_pattern(image, P=24, R=8, method="uniform")
        (lbp_hist, _) = np.histogram(lbp.ravel(), bins=np.arange(0, 27), range=(0, 26))
        lbp_hist = lbp_hist.astype("float")
        lbp_hist /= (lbp_hist.sum() + 1e-7)
        
        combined_features = np.hstack([hog_features, lbp_hist])
        features_list.append(combined_features)
        
    return np.array(features_list)

# --- Main script execution ---
if __name__ == "__main__":
    genuine_folder = 'dataset/real' 
    forged_folder = 'dataset/forge'

    genuine_data = load_images(genuine_folder, label=1)
    forged_data = load_images(forged_folder, label=0)
    
    all_data = genuine_data + forged_data
    
    images, labels = zip(*all_data)

    features = extract_features(images)
    labels = np.array(labels)

    print("\nSplitting data into training and testing sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.25, random_state=42, stratify=labels
    )
    print(f"Training data: {X_train.shape[0]} samples")
    print(f"Testing data: {X_test.shape[0]} samples")

    print("\n--- Training SVM Model ---")
    param_grid = {'C': [10, 100], 'gamma': [0.01, 0.001], 'kernel': ['rbf']}
    
    grid = GridSearchCV(SVC(probability=True), param_grid, refit=True, verbose=2, cv=3)
    grid.fit(X_train, y_train)
    
    best_svm_model = grid.best_estimator_
    print(f"\nBest model parameters: {grid.best_params_}")

    print("\n--- Evaluating Model ---")
    y_pred = best_svm_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Forged', 'Genuine']))

    MODEL_FILENAME = "signature_model.joblib"
    print(f"\n--- Saving final model to '{MODEL_FILENAME}' ---")
    joblib.dump(best_svm_model, MODEL_FILENAME)
    print("✅ Model saved successfully!")