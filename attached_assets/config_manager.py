import os
import json

class ConfigManager:
    """
    Manages application configuration, including settings and position presets.
    """
    def __init__(self, config_file="config.json"):
        """Initialize the configuration manager."""
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from file or create default if not exists."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self._get_default_config()
        else:
            # Create default config
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config
    
    def _get_default_config(self):
        """Get default configuration."""
        return {
            "settings": {
                "photos_dir": "photos",
                "infografika_dir": "infografika",
                "output_dir": "output",
                "excel_file": "data.xlsx",
                "canvas_width": 900,
                "canvas_height": 1200,
                "margin": 30
            },
            "positions": {}
        }
    
    def _save_config(self, config=None):
        """Save configuration to file."""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_settings(self):
        """Get application settings."""
        return self.config.get("settings", {})
    
    def update_settings(self, **kwargs):
        """Update settings with provided values."""
        self.config.setdefault("settings", {})
        for key, value in kwargs.items():
            self.config["settings"][key] = value
        self._save_config()
    
    def get_positions(self):
        """Get position configurations."""
        return self.config.get("positions", {})
    
    def add_position(self, position_id, x_formula, y_formula, anchor="top-left"):
        """Add a new position configuration."""
        self.config.setdefault("positions", {})
        self.config["positions"][position_id] = {
            "x": x_formula,
            "y": y_formula,
            "anchor": anchor
        }
        self._save_config()
    
    def update_position(self, position_id, x_formula, y_formula, anchor=None):
        """Update an existing position configuration."""
        if position_id not in self.config.get("positions", {}):
            return False
        
        self.config["positions"][position_id]["x"] = x_formula
        self.config["positions"][position_id]["y"] = y_formula
        
        if anchor is not None:
            self.config["positions"][position_id]["anchor"] = anchor
            
        self._save_config()
        return True
    
    def delete_position(self, position_id):
        """Delete a position configuration."""
        if position_id in self.config.get("positions", {}):
            del self.config["positions"][position_id]
            self._save_config()
            return True
        return False
    
    def calculate_position(self, position_id, canvas_width, canvas_height, 
                           infografika_width, infografika_height, margin):
        """
        Calculate the actual pixel position for an infographic based on the position formula.
        Applies appropriate anchor point adjustments.
        """
        positions = self.get_positions()
        if str(position_id) not in positions:
            # Default to top-left if position not found
            return margin, margin
        
        position = positions[str(position_id)]
        
        # Prepare context for formula evaluation
        context = {
            "canvas_width": canvas_width,
            "canvas_height": canvas_height,
            "infografika_width": infografika_width,
            "infografika_height": infografika_height,
            "MARGIN": margin
        }
        
        # Evaluate position formulas
        try:
            x = eval(position["x"], {"__builtins__": {}}, context)
            y = eval(position["y"], {"__builtins__": {}}, context)
        except Exception as e:
            print(f"Error evaluating position formula: {e}")
            return margin, margin
        
        # Adjust for anchor point
        anchor = position.get("anchor", "top-left")
        
        # Adjust X based on anchor
        if "center" in anchor:
            x -= infografika_width // 2
        elif "right" in anchor:
            x -= infografika_width
        
        # Adjust Y based on anchor
        if "middle" in anchor:
            y -= infografika_height // 2
        elif "bottom" in anchor:
            y -= infografika_height
        
        return int(x), int(y)
        
    def get_anchor_offset(self, anchor, width, height):
        """
        Рассчитывает смещение для заданной якорной точки.
        Возвращает смещение по X и Y относительно левого верхнего угла.
        """
        x_offset = 0
        y_offset = 0
        
        # Расчет смещения по X
        if "center" in anchor:
            x_offset = width // 2
        elif "right" in anchor:
            x_offset = width
            
        # Расчет смещения по Y
        if "middle" in anchor:
            y_offset = height // 2
        elif "bottom" in anchor:
            y_offset = height
            
        return x_offset, y_offset
