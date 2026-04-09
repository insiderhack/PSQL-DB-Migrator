import PyInstaller.__main__
import os
import platform

def build():
    """Build the application using PyInstaller."""
    print(f"Building for {platform.system()}...")
    
    params = [
        'src/pg_migrator/main.py',
        '--name=pg-migrator',
        '--onefile',
        '--clean',
        '--add-data=src/pg_migrator/ui/theme:pg_migrator/ui/theme',
    ]
    
    # Add icon if available
    # if os.path.exists('assets/icon.ico'):
    #     params.append('--icon=assets/icon.ico')
        
    PyInstaller.__main__.run(params)

if __name__ == "__main__":
    build()
