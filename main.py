import os
from nicegui import ui, app
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from PIL import Image
import numpy as np
from skimage import color
import io
import base64

# Initialize FastAPI and NiceGUI
fastapi_app = FastAPI()
ui.run_with(fastapi_app)

# Global variables to store the uploaded image and its path
uploaded_image = None
uploaded_image_path = None

def analyze_skin_tone(image):
    # Convert image to LAB color space
    lab_image = color.rgb2lab(np.array(image))
    
    # Extract the average L*, a*, and b* values
    l, a, b = np.mean(lab_image, axis=(0, 1))
    
    # Determine skin tone based on L* value
    if l < 50:
        return "Dark"
    elif 50 <= l < 60:
        return "Medium"
    else:
        return "Light"

def get_color_recommendations(skin_tone):
    recommendations = {
        "Dark": ["Deep purple", "Emerald green", "Coral", "Mustard yellow", "Royal blue"],
        "Medium": ["Teal", "Burgundy", "Olive green", "Dusty rose", "Navy blue"],
        "Light": ["Pastel pink", "Sky blue", "Mint green", "Lavender", "Peach"]
    }
    return recommendations.get(skin_tone, [])

def change_skin_tone(image, factor):
    # Convert image to LAB color space
    lab_image = color.rgb2lab(np.array(image))
    
    # Modify the L* channel
    lab_image[:,:,0] = np.clip(lab_image[:,:,0] * factor, 0, 100)
    
    # Convert back to RGB
    rgb_image = color.lab2rgb(lab_image)
    
    return Image.fromarray((rgb_image * 255).astype(np.uint8))

@ui.page('/')
def home():
    ui.label('Skin Tone Color Analyzer').classes('text-h3 text-center q-my-md')
    
    async def handle_upload(file: UploadFile):
        global uploaded_image, uploaded_image_path
        contents = await file.read()
        uploaded_image = Image.open(io.BytesIO(contents)).convert('RGB')
        uploaded_image_path = f'uploaded_image.jpg'
        uploaded_image.save(uploaded_image_path)
        ui.notify('Image uploaded successfully!')
        analyze_button.enable()
        image_display.set_source(uploaded_image_path)
        
    ui.upload(on_upload=handle_upload).classes('q-my-md')
    
    image_display = ui.image('').classes('q-my-md')
    
    with ui.row():
        analyze_button = ui.button('Analyze Skin Tone', on_click=lambda: analyze_skin_tone_ui()).classes('q-mx-md').disable()
        change_tone_button = ui.button('Change Skin Tone', on_click=lambda: change_skin_tone_ui()).classes('q-mx-md').disable()
    
    result_label = ui.label().classes('text-h6 q-my-md')
    recommendations_label = ui.label().classes('text-body1 q-my-md')
    
    def analyze_skin_tone_ui():
        if uploaded_image:
            skin_tone = analyze_skin_tone(uploaded_image)
            result_label.set_text(f'Detected Skin Tone: {skin_tone}')
            
            recommendations = get_color_recommendations(skin_tone)
            recommendations_text = "Recommended colors: " + ", ".join(recommendations)
            recommendations_label.set_text(recommendations_text)
            
            change_tone_button.enable()
    
    def change_skin_tone_ui():
        if uploaded_image:
            lighter_image = change_skin_tone(uploaded_image, 1.2)
            darker_image = change_skin_tone(uploaded_image, 0.8)
            
            buffered = io.BytesIO()
            lighter_image.save(buffered, format="PNG")
            lighter_image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            buffered = io.BytesIO()
            darker_image.save(buffered, format="PNG")
            darker_image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            ui.image(f'data:image/png;base64,{lighter_image_base64}').classes('q-my-md')
            ui.label('Lighter Skin Tone').classes('text-subtitle1')
            ui.image(f'data:image/png;base64,{darker_image_base64}').classes('q-my-md')
            ui.label('Darker Skin Tone').classes('text-subtitle1')

if __name__ == '__main__':
    ui.run(port=8080)