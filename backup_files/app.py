import streamlit as st
import os
import pandas as pd
import numpy as np
import json
import time
from PIL import Image, ImageDraw
import io

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

if 'process_status' not in st.session_state:
    st.session_state.process_status = ""

if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

if 'output_directory' not in st.session_state:
    st.session_state.output_directory = ""

# Set up the sidebar for configuration options
st.sidebar.title("Settings")

# Directory selection
settings = st.session_state.config_manager.get_settings()
photos_dir = st.sidebar.text_input("Photos Directory", value=settings.get("photos_dir", "photos"))
infografika_dir = st.sidebar.text_input("Infographics Directory", value=settings.get("infografika_dir", "infografika"))
excel_file = st.sidebar.text_input("Excel File", value=settings.get("excel_file", "data.xlsx"))
output_dir = st.sidebar.text_input("Output Directory", value=settings.get("output_dir", "output"))

# Canvas size settings
canvas_width = st.sidebar.number_input("Canvas Width", value=settings.get("canvas_width", 900), min_value=100, max_value=3000)
canvas_height = st.sidebar.number_input("Canvas Height", value=settings.get("canvas_height", 1200), min_value=100, max_value=3000)
margin = st.sidebar.number_input("Margin", value=settings.get("margin", 30), min_value=0, max_value=100)

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
            
            if position_options:
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
                                result = st.session_state.image_processor.overlay_infografika(
                                    canvas, infographic_path, selected_position
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
            else:
                st.warning("No positions defined. Please add a position in the Position Editor tab first.")

# Tab 3: Process Images
with tab3:
    st.header("Process Images")
    
    # Check if required directories exist
    required_paths = [photos_dir, infografika_dir, excel_file]
    missing_paths = [path for path in required_paths if not os.path.exists(path)]
    
    # Excel file exists - show additional info
    if os.path.exists(excel_file):
        try:
            excel = pd.ExcelFile(excel_file)
            sheet_names = excel.sheet_names
            st.info(f"Excel file contains {len(sheet_names)} sheets: {', '.join(sheet_names)}")
        except Exception as e:
            st.error(f"Error reading Excel file: {str(e)}")
    
    if missing_paths:
        st.error(f"Missing required files/directories: {', '.join(missing_paths)}")
    else:
        # Process button
        if st.button("Process All Images"):
            # Reset status
            st.session_state.processing_complete = False
            st.session_state.output_directory = ""
            
            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Custom progress callback
                def update_progress(current, total, status=""):
                    progress = current / total if total > 0 else 0
                    progress_bar.progress(progress)
                    status_text.text(status)
                    st.session_state.process_status = status
                
                # Read Excel sheets info
                excel = pd.ExcelFile(excel_file)
                sheet_names = excel.sheet_names
                
                status_text.text(f"Processing {len(sheet_names)} sheets from Excel file...")
                
                # Process images
                total_processed, output_path = st.session_state.image_processor.generate_cards(
                    excel_file, photos_dir, infografika_dir, output_dir,
                    canvas_width, canvas_height, margin, 
                    progress_callback=update_progress
                )
                
                # Update completion status
                progress_bar.progress(1.0)
                st.session_state.processing_complete = True
                st.session_state.output_directory = output_path
                st.success(f"Successfully processed {total_processed} images! Output saved to: {output_path}")
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                
        # Show status if processing is complete
        if st.session_state.processing_complete and st.session_state.output_directory:
            st.success(f"Last processing completed successfully. Output saved to: {st.session_state.output_directory}")
            
            # If the output directory exists, show a list of processed folders
            if os.path.exists(st.session_state.output_directory):
                sheet_folders = [d for d in os.listdir(st.session_state.output_directory) 
                              if os.path.isdir(os.path.join(st.session_state.output_directory, d))]
                
                if sheet_folders:
                    # Count total processed images
                    total_images = 0
                    for sheet_folder in sheet_folders:
                        sheet_path = os.path.join(st.session_state.output_directory, sheet_folder)
                        article_folders = [d for d in os.listdir(sheet_path) 
                                        if os.path.isdir(os.path.join(sheet_path, d))]
                        
                        for article_folder in article_folders:
                            article_path = os.path.join(sheet_path, article_folder)
                            images = [f for f in os.listdir(article_path) 
                                    if os.path.isfile(os.path.join(article_path, f)) and
                                    f.lower().endswith('.png')]
                            total_images += len(images)
                    
                    # Show folder structure and summary
                    st.write(f"Processed {len(sheet_folders)} sheets with a total of {total_images} images.")
                    
                    with st.expander("Show processed folder structure"):
                        for sheet_folder in sheet_folders:
                            st.write(f"📁 {sheet_folder}")
                            sheet_path = os.path.join(st.session_state.output_directory, sheet_folder)
                            article_folders = [d for d in os.listdir(sheet_path) 
                                           if os.path.isdir(os.path.join(sheet_path, d))]
                            
                            for article_folder in article_folders:
                                article_path = os.path.join(sheet_path, article_folder)
                                images = [f for f in os.listdir(article_path) 
                                       if os.path.isfile(os.path.join(article_path, f)) and
                                       f.lower().endswith('.png')]
                                
                                st.write(f"  📁 {article_folder} ({len(images)} images)")

# Footer
st.markdown("---")
st.markdown("InfographicPositioner App. Developed with Streamlit.")
