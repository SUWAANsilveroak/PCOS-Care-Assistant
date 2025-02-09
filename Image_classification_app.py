import streamlit as st
import tensorflow as tf
from tensorflow.lite.python.interpreter import Interpreter
from PIL import Image
import numpy as np
from io import BytesIO

# Set page configuration
st.set_page_config(
    page_title="PCOS Detection",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS to control width and styling
st.markdown("""
    <style>
        /* Hide streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Main container width */
        .main > div {
            max-width: 1200px;
            padding: 1rem;
        }
        
        /* Image styling */
        .stImage {
            max-width: 470px !important;
            margin: auto;
        }
        .image-container {
            background-color: #ffffff;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin: auto;
            max-width: 470px;
        }
        
        /* New title styling */
        h1 {
            text-align: center !important;
            font-size: 50px !important;
            font-weight: bold !important;
            padding: 20px !important;
        }
        
        /* Ensuring the title container is centered */
        div.element-container:has(h1) {
            width: 100% !important;
            text-align: center !important;
        }
        
        /* Custom title class */
        .big-title {
            font-size: 50px !important;
            font-weight: bold !important;
            text-align: center !important;
            padding: 20px 0px !important;
            margin: 0 auto !important;
            display: block !important;
        }
        
    </style>
""", unsafe_allow_html=True)

# Load the TFLite model
@st.cache_resource
def load_tflite_model():
    try:
        interpreter = Interpreter(model_path='pcos_detection_model.tflite')
        interpreter.allocate_tensors()
        return interpreter
    except Exception as e:
        st.error(f"Error loading TFLite model: {str(e)}")
        return None

def preprocess_image(image, target_size=(224, 224)):
    """
    Preprocess the uploaded image for model prediction
    """
    # Convert to grayscale if the image is RGB
    if image.mode != 'L':  # If not already grayscale
        image = image.convert('L')
        # Convert back to RGB (3 channels) as model expects RGB input
        image = Image.merge('RGB', (image, image, image))
    
    # Resize image
    image = image.resize(target_size)
    
    # Convert to numpy array and normalize
    img_array = np.array(image)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    
    return img_array

def predict_pcos_tflite(interpreter, image_array):
    """
    Make prediction using the TFLite model
    """
    try:
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        # Set input tensor
        interpreter.set_tensor(input_details[0]['index'], image_array.astype(np.float32))

        # Invoke the interpreter
        interpreter.invoke()

        # Get output tensor
        prediction = interpreter.get_tensor(output_details[0]['index'])
        probability = prediction[0][0]
        result = 'PCOS Negative' if probability > 0.5 else 'PCOS Positive'
        return result, probability
    except Exception as e:
        st.error(f"Error during prediction: {str(e)}")
        return None, None

def main():
    # Sidebar
    st.sidebar.title("Upload Image 🖼️")
    st.sidebar.write("Upload an ultrasound image to check for PCOS")
    
    # File uploader in sidebar
    uploaded_file = st.sidebar.file_uploader(
        "Choose an ultrasound image...", 
        type=["jpg", "jpeg", "png"],
        help="Upload an ultrasound image (max 10MB)",
        accept_multiple_files=False
    )
    
    # Check button in sidebar
    check_button = st.sidebar.button("Check for PCOS", use_container_width=True)

    # Add a note below the check button
    st.sidebar.warning("""
    **Note:** This model is still under development. 
    Please only upload ultrasound images of the ovary for analysis. 
    Uploading other types of images may result in incorrect predictions.
    """)
    
    # Add disclaimer in sidebar
    st.sidebar.markdown("---")
    st.sidebar.info("""
    Please note: This is an AI-based prediction and should not be used as a definitive 
    medical diagnosis. Always consult with a healthcare professional for proper diagnosis 
    and treatment.
    """)
    
    # Main content area
    st.markdown('<p class="big-title">🏥 PCOS Detection System 🔍</p>', unsafe_allow_html=True)
    # st.title("PCOS Detection from Ultrasound Images")
    

    # Load TFLite model
    interpreter = load_tflite_model()
    
    if interpreter is None:
        st.error("Failed to load TFLite model. Please check if the model file exists.")
        return
    
    # Main content layout
    if uploaded_file is not None:
        # Check file size
        if uploaded_file.size > 10 * 1024 * 1024:  # 10MB limit
            st.error("File size exceeds 10MB limit. Please upload a smaller file.")
            return
            
        try:
            # Display the image in Instagram-like container
            image = Image.open(uploaded_file)
            
            # Create centered columns for the image
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown('<div class="image-container">', unsafe_allow_html=True)
                st.image(image, caption="Uploaded Image", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Make prediction when button is clicked
            if check_button:
                with st.spinner("Analyzing image..."):
                    # Preprocess image
                    processed_image = preprocess_image(image)
                    
                    # Make prediction
                    result, probability = predict_pcos_tflite(interpreter, processed_image)
                    
                    if result:
                        # Create columns for centered result
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            # Display result with custom styling
                            result_color = "red" if "Positive" in result else "green"
                            st.markdown(f"""
                                <div style='text-align: center; padding: 2rem; background-color: #f0f2f6; border-radius: 10px;'>
                                    <h2 style='color: {result_color};'>{result}</h2>
                                    <p>Confidence: {abs(probability - 0.5) * 2:.2%}</p>
                                </div>
                            """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
            st.write("Please ensure you've uploaded a valid image file.")
    else:
        # Display placeholder when no image is uploaded
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div style='text-align: center; padding: 2rem; background-color: #f0f2f6; border-radius: 10px;'>
                    <p>Please upload an ultrasound image using the sidebar to begin analysis.</p>
                </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
