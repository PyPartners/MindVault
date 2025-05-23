from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
# from mindvault.constants import ICONS_DIR # If check.png needs full path construction

# Assuming check.png and check_dark.png are in an 'icons' folder
# relative to where the application is run, or accessible via Qt's resource system.
# For simplicity, using relative paths as in the original QSS.
# If icons are packaged, their paths might need `os.path.join(ICONS_DIR, 'check.png')`
# or Qt resource paths `:/icons/check.png`.

STYLES = {
    "light": {
        "background": "#FAFAFA",
        "foreground": "#121212",
        "primary": "#2196F3", # Blue
        "primary_text": "#FFFFFF",
        "secondary": "#E0E0E0", # Light grey for borders/separators
        "list_selection": "#BBDEFB", # Lighter blue for selection
        "qss": """
            QMainWindow, QDialog {{
                background-color: {background};
                color: {foreground};
            }}
            QWidget {{ /* Catches most background widgets */
                 background-color: {background};
                 color: {foreground};
            }}
            QLabel {{
                color: {foreground};
                background-color: transparent; /* Ensure labels have transparent background */
            }}
            QLineEdit, QTextEdit, QSpinBox {{
                background-color: #FFFFFF;
                color: {foreground};
                border: 1px solid {secondary};
                border-radius: 4px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {primary};
                color: {primary_text};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #1976D2; /* Darker blue */
            }}
            QPushButton:pressed {{
                background-color: #0D47A1; /* Even darker blue */
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD; /* Grey out disabled buttons */
                color: #757575;
            }}
            QPushButton#copyButton {{ /* Specific style example */
                 background-color: #4CAF50; /* Green */
            }}
            QPushButton#copyButton:hover {{
                 background-color: #388E3C;
            }}
            QPushButton#copyButton:disabled {{
                background-color: #C8E6C9;
                color: #757575;
            }}
             QPushButton#deleteButton {{ /* Specific style example */
                 background-color: #f44336; /* Red */
            }}
            QPushButton#deleteButton:hover {{
                 background-color: #d32f2f;
            }}
            QPushButton#deleteButton:disabled {{
                background-color: #FFCDD2;
                color: #757575;
            }}
            QTableWidget {{
                background-color: #FFFFFF;
                color: {foreground};
                border: 1px solid {secondary};
                gridline-color: {secondary};
                border-radius: 4px;
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {list_selection};
                color: {foreground}; /* Keep text readable */
            }}
            QHeaderView::section {{
                background-color: {secondary};
                color: {foreground};
                padding: 4px;
                border: 1px solid {background}; /* Use main background for subtle border */
                font-weight: bold;
            }}
             QMenuBar {{
                background-color: {secondary};
                color: {foreground};
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 4px 8px;
            }}
            QMenuBar::item:selected {{
                background: {list_selection};
            }}
             QMenuBar::item:disabled {{
                color: #9E9E9E; /* Grey out disabled menu items */
            }}
            QMenu {{
                background-color: {background};
                border: 1px solid {secondary};
                color: {foreground};
            }}
            QMenu::item:selected {{
                background-color: {primary};
                color: {primary_text};
            }}
             QMenu::item:disabled {{
                color: #BDBDBD; /* Grey out disabled menu actions */
                background-color: transparent;
            }}
             QToolBar {{
                 background-color: {background};
                 border: none;
                 padding: 2px;
             }}
             QStatusBar {{
                 background-color: {secondary};
                 color: {foreground};
             }}
             QComboBox {{
                border: 1px solid {secondary};
                border-radius: 3px;
                padding: 1px 18px 1px 3px;
                min-width: 6em;
                background-color: white;
             }}
             QComboBox::drop-down {{
                 subcontrol-origin: padding;
                 subcontrol-position: top right;
                 width: 15px;
                 border-left-width: 1px;
                 border-left-color: {secondary};
                 border-left-style: solid;
                 border-top-right-radius: 3px;
                 border-bottom-right-radius: 3px;
             }}
            QComboBox QAbstractItemView {{
                border: 1px solid {secondary};
                selection-background-color: {primary};
                background-color: white;
                color: {foreground};
            }}
            QCheckBox::indicator {{
                width: 13px;
                height: 13px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 1px solid {secondary};
                background-color: white;
            }}
            QCheckBox::indicator:checked {{
                border: 1px solid {primary};
                background-color: {primary};
                image: url(icons/check.png); /* Optional: custom check image */
            }}
        """
    },
    "dark": {
        "background": "#121212",
        "foreground": "#E0E0E0", # Light grey text
        "primary": "#03DAC5", # Teal/Turquoise
        "primary_text": "#000000", # Black text on Teal
        "secondary": "#333333", # Dark grey for borders/surfaces
        "list_selection": "#03DAC5", # Use primary for selection
        "qss": """
            QMainWindow, QDialog {{
                background-color: {background};
                color: {foreground};
            }}
             QWidget {{ /* Catches most background widgets */
                 background-color: {background};
                 color: {foreground};
            }}
            QLabel {{
                color: {foreground};
                background-color: transparent;
            }}
            QLineEdit, QTextEdit, QSpinBox {{
                background-color: {secondary};
                color: {foreground};
                border: 1px solid #555555; /* Slightly lighter border */
                border-radius: 4px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {primary};
                color: {primary_text}; /* Black text */
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                 min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #018786; /* Darker Teal */
            }}
            QPushButton:pressed {{
                background-color: #005F5F; /* Even darker Teal */
            }}
            QPushButton:disabled {{
                background-color: #424242; /* Darker grey for disabled */
                color: #757575;
            }}
             QPushButton#copyButton {{ /* Specific style example */
                 background-color: #81C784; /* Light Green */
                 color: #000000;
            }}
            QPushButton#copyButton:hover {{
                 background-color: #66BB6A;
            }}
             QPushButton#copyButton:disabled {{
                background-color: #4A7C4B;
                color: #9E9E9E;
            }}
             QPushButton#deleteButton {{ /* Specific style example */
                 background-color: #E57373; /* Light Red */
                 color: #000000;
            }}
            QPushButton#deleteButton:hover {{
                 background-color: #EF5350;
            }}
            QPushButton#deleteButton:disabled {{
                background-color: #8B4D4D;
                color: #9E9E9E;
            }}
            QTableWidget {{
                background-color: {secondary};
                color: {foreground};
                border: 1px solid #555555;
                gridline-color: #555555;
                border-radius: 4px;
            }}
             QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {list_selection};
                color: {primary_text}; /* Black text for contrast on Teal */
            }}
            QHeaderView::section {{
                background-color: #424242; /* Slightly lighter dark grey */
                color: {foreground};
                padding: 4px;
                border: 1px solid {background};
                font-weight: bold;
            }}
             QMenuBar {{
                background-color: {secondary};
                color: {foreground};
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 4px 8px;
            }}
            QMenuBar::item:selected {{
                background: #555555;
            }}
            QMenuBar::item:disabled {{
                color: #757575; /* Grey out disabled menu items */
            }}
            QMenu {{
                background-color: {secondary};
                border: 1px solid #555555;
                color: {foreground};
            }}
            QMenu::item:selected {{
                background-color: {primary};
                color: {primary_text};
            }}
            QMenu::item:disabled {{
                color: #757575; /* Grey out disabled menu actions */
                background-color: transparent;
            }}
             QToolBar {{
                 background-color: {background};
                 border: none;
                 padding: 2px;
             }}
             QStatusBar {{
                 background-color: {secondary};
                 color: {foreground};
             }}
             QComboBox {{
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 1px 18px 1px 3px;
                min-width: 6em;
                background-color: {secondary};
                color: {foreground};
             }}
              QComboBox::drop-down {{
                 subcontrol-origin: padding;
                 subcontrol-position: top right;
                 width: 15px;
                 border-left-width: 1px;
                 border-left-color: #555555;
                 border-left-style: solid;
                 border-top-right-radius: 3px;
                 border-bottom-right-radius: 3px;
             }}
            QComboBox QAbstractItemView {{ /* Style the dropdown list */
                border: 1px solid #555555;
                selection-background-color: {primary};
                selection-color: {primary_text};
                background-color: {secondary}; /* Background of the dropdown list */
                color: {foreground}; /* Text color in the dropdown list */
            }}
            QCheckBox::indicator {{
                width: 13px;
                height: 13px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 1px solid #555555;
                background-color: {secondary};
            }}
            QCheckBox::indicator:checked {{
                border: 1px solid {primary};
                background-color: {primary};
                 image: url(icons/check_dark.png); /* Optional: custom check image for dark theme */
            }}
        """
    }
}

def apply_theme(app, theme_name):
    if theme_name in STYLES:
        style_data = STYLES[theme_name]
        qss = style_data["qss"].format(**style_data)
        app.setStyleSheet(qss)
        
        palette = QPalette()
        text_color = QColor(style_data["foreground"])
        disabled_text_color = QColor("#808080") if theme_name == 'light' else QColor("#757575")
        base_color = QColor("#FFFFFF") if theme_name == 'light' else QColor(style_data["secondary"])
        button_color = QColor(style_data["primary"])
        button_text_color = QColor(style_data["primary_text"])
        highlight_color = QColor(style_data["list_selection"])
        
        # Determine highlighted text color
        highlighted_text_color = QColor(style_data.get("selected_text", style_data["foreground"]))
        if theme_name == 'dark' and highlight_color == QColor(style_data["primary"]): # Special case for dark theme if selection is primary
            highlighted_text_color = QColor(style_data["primary_text"])

        palette.setColor(QPalette.Window, QColor(style_data["background"]))
        palette.setColor(QPalette.WindowText, text_color)
        palette.setColor(QPalette.Base, base_color) # Background for text entry widgets
        palette.setColor(QPalette.AlternateBase, QColor(style_data["secondary"])) # Used in complex views
        palette.setColor(QPalette.ToolTipBase, QColor(style_data["background"]))
        palette.setColor(QPalette.ToolTipText, text_color)
        palette.setColor(QPalette.Text, text_color) # General text color
        palette.setColor(QPalette.Button, button_color)
        palette.setColor(QPalette.ButtonText, button_text_color)
        palette.setColor(QPalette.BrightText, Qt.red) # Text that stands out (e.g. for validation)
        palette.setColor(QPalette.Link, QColor(style_data["primary"]))
        palette.setColor(QPalette.Highlight, highlight_color) # Selection background
        palette.setColor(QPalette.HighlightedText, highlighted_text_color) # Selection text

        # Disabled states
        palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text_color)
        palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text_color)
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text_color)
        palette.setColor(QPalette.Disabled, QPalette.Base, QColor(style_data["secondary"]) if theme_name == 'light' else QColor("#222222"))
        palette.setColor(QPalette.Disabled, QPalette.Button, QColor("#BDBDBD") if theme_name == 'light' else QColor("#424242"))
        palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor("#D0D0D0") if theme_name == 'light' else QColor("#444444"))
        palette.setColor(QPalette.Disabled, QPalette.HighlightedText, disabled_text_color)
        
        app.setPalette(palette)
    else:
        print(f"Theme '{theme_name}' not found.")