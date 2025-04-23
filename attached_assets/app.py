import streamlit as st
import os
import pandas as pd
import json
from PIL import Image
import tempfile
import shutil

from config_manager import ConfigManager
from image_processor import ImageProcessor
from position_editor import PositionEditor

# Set page config
st.set_page_config(
    page_title="InfographicPositioner",
    page_icon="📊",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'config_manager' not in st.session_state:
    st.session_state.config_manager = ConfigManager()
    
if 'image_processor' not in st.session_state:
    st.session_state.image_processor = ImageProcessor(st.session_state.config_manager)
    
if 'position_editor' not in st.session_state:
    st.session_state.position_editor = PositionEditor(st.session_state.config_manager)

# Set up the sidebar for configuration options
st.sidebar.title("Settings")

# Directory selection
photos_dir = st.sidebar.text_input("Photos Directory", value="photos")
infografika_dir = st.sidebar.text_input("Infographics Directory", value="infografika")
excel_file = st.sidebar.text_input("Excel File", value="data.xlsx")
output_dir = st.sidebar.text_input("Output Directory", value="output")

# Canvas size settings
canvas_width = st.sidebar.number_input("Canvas Width", value=900, min_value=100, max_value=3000)
canvas_height = st.sidebar.number_input("Canvas Height", value=1200, min_value=100, max_value=3000)
margin = st.sidebar.number_input("Margin", value=30, min_value=0, max_value=100)

# Save settings
if st.sidebar.button("Save Settings"):
    st.session_state.config_manager.update_settings(
        photos_dir=photos_dir,
        infografika_dir=infografika_dir,
        excel_file=excel_file,
        output_dir=output_dir,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        margin=margin
    )
    st.sidebar.success("Settings saved successfully!")

# Main tabs
tab1, tab2, tab3 = st.tabs(["Position Editor", "Preview", "Process Images"])

# Tab 1: Position Editor
with tab1:
    st.session_state.position_editor.render()
    
# Tab 2: Preview
with tab2:
    st.header("Preview Infographic Positions")
    
    # Sample image selection
    valid_dirs = []
    if os.path.exists(photos_dir):
        valid_dirs = [d for d in os.listdir(photos_dir) if os.path.isdir(os.path.join(photos_dir, d))]
    
    if not valid_dirs:
        st.warning("No valid article directories found in the photos directory.")
    else:
        article = st.selectbox("Select Article", valid_dirs)
        
        # Get sample images from the selected article directory
        article_dir = os.path.join(photos_dir, article)
        image_files = [f for f in os.listdir(article_dir) 
                      if os.path.isfile(os.path.join(article_dir, f)) and 
                      f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        
        if not image_files:
            st.warning("No image files found in the selected article directory.")
        else:
            selected_image = st.selectbox("Select Image", image_files)
            
            # Get available infographics
            if os.path.exists(infografika_dir):
                infographic_files = [os.path.splitext(f)[0] for f in os.listdir(infografika_dir) 
                                   if f.lower().endswith('.png')]
                selected_infographic = st.selectbox("Select Infographic", ["None"] + infographic_files)
            else:
                st.warning("Infographics directory not found.")
                selected_infographic = "None"
            
            # Position selection
            positions = st.session_state.config_manager.get_positions()
            position_options = list(positions.keys())
            selected_position = st.selectbox("Select Position", position_options)
            
            # Preview button
            if st.button("Generate Preview"):
                if selected_infographic != "None":
                    # Process and display the preview
                    photo_path = os.path.join(article_dir, selected_image)
                    infographic_path = os.path.join(infografika_dir, selected_infographic + ".png")
                    
                    if os.path.exists(photo_path) and os.path.exists(infographic_path):
                        try:
                            # Process the image
                            canvas = st.session_state.image_processor.process_and_center_image(
                                photo_path, canvas_width, canvas_height
                            )
                            # Overlay infographic
                            position = int(selected_position)
                            result = st.session_state.image_processor.overlay_infografika(
                                canvas, infographic_path, position
                            )
                            
                            # Display the result
                            st.image(result, caption="Preview with infographic", use_column_width=True)
                        except Exception as e:
                            st.error(f"Error generating preview: {str(e)}")
                    else:
                        st.error("Image or infographic file not found.")
                else:
                    # Just display the processed image without infographic
                    photo_path = os.path.join(article_dir, selected_image)
                    if os.path.exists(photo_path):
                        try:
                            canvas = st.session_state.image_processor.process_and_center_image(
                                photo_path, canvas_width, canvas_height
                            )
                            st.image(canvas, caption="Processed image without infographic", use_column_width=True)
                        except Exception as e:
                            st.error(f"Error processing image: {str(e)}")
                    else:
                        st.error("Image file not found.")

# Tab 3: Process Images
with tab3:
    st.header("Process Images")
    
    # Check if required directories exist
    required_paths = [photos_dir, infografika_dir, excel_file]
    missing_paths = [path for path in required_paths if not os.path.exists(path)]
    
    if missing_paths:
        st.error(f"Missing required files/directories: {', '.join(missing_paths)}")
    else:
        if st.button("Process All Images"):
            try:
                # Create progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Read Excel file
                status_text.text("Reading Excel file...")
                try:
                    df = pd.read_excel(excel_file, dtype=str).fillna('')
                    data = df.values.tolist()
                except Exception as e:
                    st.error(f"Error reading Excel file: {str(e)}")
                    data = []
                
                if data:
                    # Create output directory
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    
                    # Process images
                    status_text.text("Processing images...")
                    try:
                        total_processed = st.session_state.image_processor.generate_cards(
                            data, photos_dir, infografika_dir, output_dir,
                            canvas_width, canvas_height, margin, 
                            progress_callback=lambda x, total: progress_bar.progress(x/total)
                        )
                        progress_bar.progress(1.0)
                        st.success(f"Successfully processed {total_processed} images!")
                    except Exception as e:
                        st.error(f"Error processing images: {str(e)}")
                else:
                    st.warning("No data found in Excel file.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown("InfographicPositioner App. Developed with Streamlit.")
