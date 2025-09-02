# Signature Forgery Detection

-   Signature Forgery Detection is a computer vision project aimed at predicting the authenticity of a handwritten signature by analyzing its image.
-   This project employs image processing, feature extraction, and machine learning techniques to build a robust classification model.
-   The research explores hyperparameter tuning for Support Vector Machines (SVMs) and compares its performance against a Random Forest model.

## What the Project Does

This project is designed to:
-   Analyze scanned signature images to determine if they are genuine or forged.
-   Use machine learning algorithms to build and evaluate predictive models.
-   Compare the performance of different classification algorithms.
-   Provide a functional web application for real-time signature verification.

## Technologies Used

### Programming Tools
-   **Python** (for image processing and implementation of machine learning algorithms)
-   **NumPy** (for data manipulation and numerical operations)
-   **OpenCV** (for image loading and preprocessing)
-   **scikit-image** (for advanced feature extraction)
-   **Matplotlib, Seaborn** (for data visualization)
-   **scikit-learn** (for training and evaluating machine learning models)
-   **Streamlit** (for building the interactive web application)
-   **Joblib** (for model serialization)

### Machine Learning Algorithms
This project incorporates and compares the following algorithms:
1.  **Support Vector Machine (SVM)**
2.  **Random Forest**

## Research Section

### Hyperparameter Tuning (SVM)
-   Hyperparameter tuning was performed for the Support Vector Machine (SVM) algorithm to optimize its performance.
-   **GridSearchCV** was utilized to identify the best parameter combinations (e.g., `C`, `gamma`, and `kernel`).
-   Finding optimal hyperparameters significantly improved the model's accuracy and its ability to generalize to new, unseen signatures.

### Algorithm Comparison
-   A comparative analysis was conducted to evaluate the performance of two powerful algorithms:
    1.  **Support Vector Machine (SVM)**
    2.  **Random Forest**
-   Each algorithm was assessed using key performance metrics such as **accuracy**, **precision**, **recall**, and **F1 score**, presented in a detailed classification report.

### Feature Extraction and Analysis
-   Feature extraction is a critical component of this project, transforming raw image pixels into meaningful numerical representations.
-   The system combines two powerful techniques:
    1.  **Histogram of Oriented Gradients (HOG):** To capture the shape, strokes, and directional information of the signature.
    2.  **Local Binary Patterns (LBP):** To analyze the fine textural details and patterns within the signature's ink.
-   This combination of features provides a comprehensive profile of each signature, enabling the machine learning models to effectively distinguish between genuine and forged examples.

## Key Features

-   **Data-Driven Approach:** Utilizes a dataset of genuine and forged signatures for model training.
-   **Advanced Feature Engineering:** Combines HOG and LBP features for a detailed and robust analysis of signatures.
-   **Model Evaluation:** Includes performance metrics and confusion matrices to assess and compare model accuracy.
-   **Interactive UI:** Deployed as a Streamlit web application for easy, real-time prediction on user-uploaded images.

## Conclusion

This project serves as a practical implementation of a signature verification system. The comparative analysis of machine learning algorithms provides valuable insights into effective classification approaches, while the feature extraction process highlights the importance of shape and texture in identifying forgeries. The research can be extended for academic purposes or adapted for practical security applications.
