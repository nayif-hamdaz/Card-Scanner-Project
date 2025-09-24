# AI Business Card Scanner Project

This project contains the complete source code for the AI Business Card Scanner, including the Python backend server and the Cordova mobile application.

## Project Structure

- `/backend`: Contains the Python Flask server that handles AI processing and saving data to Excel.
- `/MobileApp`: Contains the Apache Cordova project for the Android mobile application.

---

## How to Run the Backend Server

1.  **Navigate to the backend folder:**
    ```bash
    cd backend
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    # Create the environment (only needs to be done once)
    python -m venv venv

    # Activate the environment
    # Windows:
    .\venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file** inside the `backend` folder and add your OpenAI API key:
    ```
    OPENAI_API_KEY="sk-YourSecretKeyHere"
    ```

5.  **Run the server:**
    ```bash
    python app.py
    ```
    The server will be running at `http://127.0.0.1:5000`.

---

## How to Build and Run the Mobile App (APK)

1.  **Prerequisites:** You must have Node.js, Cordova, and a complete Android development environment (Android Studio, SDK, JDK) set up.

2.  **Navigate to the mobile app folder:**
    ```bash
    cd MobileApp
    ```

3.  **Install JavaScript dependencies:**
    ```bash
    npm install
    ```

4.  **Build the Android APK:**
    ```bash
    cordova build android
    ```
    The final `.apk` file will be located in `/MobileApp/platforms/android/app/build/outputs/apk/debug/`.