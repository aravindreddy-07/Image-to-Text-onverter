import tkinter as tk
from tkinter import filedialog, Text, END
import cv2
import pytesseract
import numpy as np
import requests
from PIL import Image, ImageTk
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Path to Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def preprocess_image_for_ocr(image_path):
    """Preprocess the image to enhance OCR accuracy."""
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    scale_factor = 2
    height, width = thresh.shape[:2]
    resized = cv2.resize(thresh, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_CUBIC)
    denoised = cv2.medianBlur(resized, 3)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    return sharpened

def extract_text(image_path, lang="eng"):
    """Extract text from the preprocessed image."""
    processed_image = preprocess_image_for_ocr(image_path)
    custom_config = r'--oem 3 --psm 6'
    return pytesseract.image_to_string(processed_image, lang=lang, config=custom_config)

def capture_from_droidcam():
    # Capture image from webcam
    # Open webcam
    cap = cv2.VideoCapture("http://192.168.31.19:4747/video")

    if not cap.isOpened():
        raise Exception("Webcam not accessible!")

    print("Press SPACE to capture the image or ESC to exit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image.")
            break

        # Display the video feed
        cv2.imshow("Webcam - Press SPACE to Capture", frame)

        # Capture the image or exit
        key = cv2.waitKey(1)
        if key == 27:  # ESC to exit
            break
        elif key == 32:  # SPACE to capture
            # Save captured frame
            captured_image_path = "captured_image.jpg"
            cv2.imwrite(captured_image_path, frame)
            print(f"Image saved to {captured_image_path}.")
            cap.release()
            cv2.destroyAllWindows()
            return captured_image_path

    cap.release()
    cv2.destroyAllWindows()
    return None

def process_images(filenames, lang="eng"):
    """Process and extract text from selected images."""
    results = []
    for file in filenames:
        text = extract_text(file, lang)
        results.append((file, text))
    return results

def save_text_to_file(results):
    """Save extracted text to a file (either txt or pdf)."""
    output_file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("PDF Files", "*.pdf")])
    if output_file:
        if output_file.endswith('.txt'):
            with open(output_file, "w", encoding="utf-8") as f:
                for file, text in results:
                    f.write(f"File: {file}\n")
                    f.write(f"Extracted Text:\n{text}\n")
                    f.write("=" * 40 + "\n")
        elif output_file.endswith('.pdf'):
            c = canvas.Canvas(output_file, pagesize=letter)
            width, height = letter
            text_object = c.beginText(40, height - 40)
            text_object.setFont("Helvetica", 10)
            for file, text in results:
                text_object.textLine(f"File: {file}")
                text_object.textLines(f"Extracted Text:\n{text}")
                text_object.textLine("=" * 40)
            c.drawText(text_object)
            c.save()

def create_gui():
    """Create the enhanced GUI resembling an iPhone app."""
    results = []  # Stores the OCR results

    def open_file():
        nonlocal results
        filenames = filedialog.askopenfilenames(title="Select Images", filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if filenames:
            lang = language_var.get()
            results = process_images(filenames, lang=lang)
            text_area.delete(1.0, END)  # Clear previous text
            for file, text in results:
                text_area.insert(END, f"File: {file}\n{text}\n{'='*40}\n")
            save_button.config(state="normal")

    def capture_image():
        nonlocal results
        captured_image_path = capture_from_droidcam()
        if captured_image_path:
            lang = language_var.get()
            text = extract_text(captured_image_path, lang=lang)
            results.append((captured_image_path, text))
            text_area.insert(END, f"Captured Image:\n{text}\n{'='*40}\n")
            save_button.config(state="normal")

    root = tk.Tk()
    root.title("Image to Text")
    root.geometry("400x600")
    root.configure(bg="#f5f5f5")

    # Header
    header_frame = tk.Frame(root, bg="#007AFF", height=80)
    header_frame.pack(fill="x")
    header_label = tk.Label(header_frame, text="Image to Text", bg="#007AFF", fg="white", font=("Helvetica", 20))
    header_label.pack(pady=20)

    # Language Selection
    lang_label = tk.Label(root, text="Language Code:", font=("Helvetica", 14), bg="#f5f5f5")
    lang_label.pack(pady=10)
    language_var = tk.Entry(root, font=("Helvetica", 14))
    language_var.insert(0, "eng")
    language_var.pack(pady=5, ipady=5, ipadx=20)

    # Buttons
    open_button = tk.Button(root, text="Open Images", bg="#007AFF", fg="white", font=("Helvetica", 14),
                            command=open_file, relief="flat")
    open_button.pack(pady=10, ipadx=30, ipady=10)

    capture_button = tk.Button(root, text="Capture Image", bg="#007AFF", fg="white", font=("Helvetica", 14),
                               command=capture_image, relief="flat")
    capture_button.pack(pady=10, ipadx=30, ipady=10)

    # Text Area
    text_area = Text(root, wrap="word", font=("Helvetica", 12), height=15, bg="#FFFFFF", fg="#000000", bd=0)
    text_area.pack(padx=20, pady=10, fill="both", expand=True)

    # Save Button
    save_button = tk.Button(root, text="Save Output", bg="#34C759", fg="white", font=("Helvetica", 14),
                            command=lambda: save_text_to_file(results), relief="flat", state="disabled")
    save_button.pack(pady=10, ipadx=30, ipady=10)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
