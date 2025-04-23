import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw
import io

class PositionEditor:
    """
    Handles the position editor UI and logic.
    """
    
    def __init__(self, config_manager):
        """Initialize with a config manager."""
        self.config_manager = config_manager
    
    def render(self):
        """Render the position editor UI."""
        st.header("Position Editor")
        st.write("Add, edit, or delete position configurations for infographic placement.")
        
        # Get current positions
        positions = self.config_manager.get_positions()
        
        # Display positions in a table
        position_data = []
        for pos_id, pos_config in positions.items():
            position_data.append({
                "Position ID": pos_id,
                "X Formula": pos_config["x"],
                "Y Formula": pos_config["y"],
                "Anchor": pos_config.get("anchor", "top-left")
            })
        
        if position_data:
            df = pd.DataFrame(position_data)
            st.dataframe(df)
        else:
            st.info("No positions configured yet. Add a new position below.")
        
        # Add/Edit Position section
        st.subheader("Add/Edit Position")
        
        # Position ID input
        position_id = st.text_input("Position ID", key="position_id_input")
        
        # For editing, allow selecting existing position
        if position_id and position_id in positions:
            st.info(f"Editing existing position {position_id}")
            current_pos = positions[position_id]
            x_formula = st.text_input("X Formula", value=current_pos["x"], key="x_formula_input")
            y_formula = st.text_input("Y Formula", value=current_pos["y"], key="y_formula_input")
            
            # Anchor point selection
            anchor_options = [
                "top-left", "top-center", "top-right",
                "middle-left", "center", "middle-right",
                "bottom-left", "bottom-center", "bottom-right"
            ]
            current_anchor = current_pos.get("anchor", "top-left")
            anchor = st.selectbox("Anchor Point", anchor_options, 
                                index=anchor_options.index(current_anchor) if current_anchor in anchor_options else 0,
                                key="anchor_input")
        else:
            x_formula = st.text_input("X Formula", key="x_formula_input", 
                                    placeholder="e.g., MARGIN or (canvas_width - infografika_width) // 2")
            y_formula = st.text_input("Y Formula", key="y_formula_input", 
                                    placeholder="e.g., MARGIN or (canvas_height - infografika_height) // 2")
            
            # Anchor point selection
            anchor_options = [
                "top-left", "top-center", "top-right",
                "middle-left", "center", "middle-right",
                "bottom-left", "bottom-center", "bottom-right"
            ]
            anchor = st.selectbox("Anchor Point", anchor_options, key="anchor_input")
        
        # Help text with formula variables
        with st.expander("Formula Help"):
            st.markdown("""
            **Available variables for formulas:**
            - `canvas_width`: Width of the canvas
            - `canvas_height`: Height of the canvas
            - `infografika_width`: Width of the infographic
            - `infografika_height`: Height of the infographic
            - `MARGIN`: Margin value from settings
            
            **Examples:**
            - Top left: `MARGIN, MARGIN`
            - Center: `(canvas_width - infografika_width) // 2, (canvas_height - infografika_height) // 2`
            - Bottom right: `canvas_width - infografika_width - MARGIN, canvas_height - infografika_height - MARGIN`
            
            **Anchor Point:**
            The anchor point determines which part of the infographic will be positioned at the specified coordinates.
            """)
            
            # Add visual explanation of anchors
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**top-left**: ↖")
                st.write("**middle-left**: ←")
                st.write("**bottom-left**: ↙")
            with col2:
                st.write("**top-center**: ↑")
                st.write("**center**: ⦿")
                st.write("**bottom-center**: ↓")
            with col3:
                st.write("**top-right**: ↗")
                st.write("**middle-right**: →")
                st.write("**bottom-right**: ↘")
        
        # Save/Update button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Position", key="save_position_button"):
                if not position_id:
                    st.error("Position ID is required.")
                elif not x_formula or not y_formula:
                    st.error("Both X and Y formulas are required.")
                else:
                    # Validate formulas by evaluation with dummy values
                    try:
                        context = {
                            "canvas_width": 900,
                            "canvas_height": 1200,
                            "infografika_width": 300,
                            "infografika_height": 300,
                            "MARGIN": 30
                        }
                        eval(x_formula, {"__builtins__": {}}, context)
                        eval(y_formula, {"__builtins__": {}}, context)
                        
                        # Save position
                        if position_id in positions:
                            self.config_manager.update_position(position_id, x_formula, y_formula, anchor)
                            st.success(f"Updated position {position_id}.")
                        else:
                            self.config_manager.add_position(position_id, x_formula, y_formula, anchor)
                            st.success(f"Added new position {position_id}.")
                        
                        # Clear inputs
                        st.session_state.position_id_input = ""
                        st.session_state.x_formula_input = ""
                        st.session_state.y_formula_input = ""
                        st.rerun()
                    except Exception as e:
                        st.error(f"Invalid formula: {str(e)}")
        
        # Delete position
        with col2:
            if position_id in positions and st.button("Delete Position", key="delete_position_button"):
                self.config_manager.delete_position(position_id)
                st.success(f"Deleted position {position_id}.")
                
                # Clear inputs
                st.session_state.position_id_input = ""
                st.session_state.x_formula_input = ""
                st.session_state.y_formula_input = ""
                st.rerun()
        
        # Visual position editor
        st.subheader("Visual Position Preview")
        
        # Create a visual representation of positions
        settings = self.config_manager.get_settings()
        canvas_width = settings.get("canvas_width", 900)
        canvas_height = settings.get("canvas_height", 1200)
        margin = settings.get("margin", 30)
        
        # Create a blank canvas
        scale_factor = 0.3  # Scale down for display
        display_width = int(canvas_width * scale_factor)
        display_height = int(canvas_height * scale_factor)
        
        # Create image
        img = Image.new('RGB', (canvas_width, canvas_height), 'lightgray')
        draw = ImageDraw.Draw(img)
        
        # Draw margin guidelines
        draw.rectangle(
            [(margin, margin), (canvas_width - margin, canvas_height - margin)],
            outline='darkgray'
        )
        
        # Draw sample infographic size
        sample_infographic_width = 300
        sample_infographic_height = 300
        
        # Plot positions
        for pos_id, pos_config in positions.items():
            try:
                # Calculate position
                x, y = self.config_manager.calculate_position(
                    pos_id, 
                    canvas_width, 
                    canvas_height, 
                    sample_infographic_width, 
                    sample_infographic_height,
                    margin
                )
                
                # Draw position marker
                marker_size = 10
                draw.rectangle(
                    [(x - marker_size, y - marker_size), (x + marker_size, y + marker_size)],
                    fill='red',
                    outline='black'
                )
                
                # Draw sample infographic outline
                draw.rectangle(
                    [(x, y), (x + sample_infographic_width, y + sample_infographic_height)],
                    outline='blue'
                )
                
                # Add position label
                draw.text((x + 5, y + 5), str(pos_id), fill='white')
            except Exception as e:
                print(f"Error displaying position {pos_id}: {e}")
        
        # Resize for display
        img_resized = img.resize((display_width, display_height), Image.LANCZOS)
        
        # Convert to bytes for displaying
        img_bytes = io.BytesIO()
        img_resized.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Display the image
        st.image(img_bytes, caption="Visual representation of positions (with sample infographic size)", use_column_width=True)
        st.caption(f"Canvas dimensions: {canvas_width}x{canvas_height}, Margin: {margin}px, Sample infographic: {sample_infographic_width}x{sample_infographic_height}px")
        
        # Export/Import positions section
        st.subheader("Export/Import Positions")
        
        # Export positions
        if st.button("Export Positions as JSON"):
            import json
            positions_json = json.dumps(positions, indent=2)
            st.download_button(
                label="Download JSON",
                data=positions_json,
                file_name="positions.json",
                mime="application/json"
            )
        
        # Import positions
        uploaded_file = st.file_uploader("Import Positions from JSON", type=["json"])
        if uploaded_file is not None:
            try:
                import json
                positions_data = json.load(uploaded_file)
                
                # Validate positions data
                if isinstance(positions_data, dict):
                    for pos_id, pos_config in positions_data.items():
                        if isinstance(pos_config, dict) and "x" in pos_config and "y" in pos_config:
                            self.config_manager.add_position(
                                pos_id, 
                                pos_config["x"], 
                                pos_config["y"], 
                                pos_config.get("anchor", "top-left")
                            )
                    
                    st.success("Positions imported successfully!")
                    st.rerun()
                else:
                    st.error("Invalid positions data format.")
            except Exception as e:
                st.error(f"Error importing positions: {str(e)}")
