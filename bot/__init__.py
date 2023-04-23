import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define package-level variables
audio_dir = Path(__file__).parent / "bot/audio"

# Define package-level functions or classes
def play_audio(audio_name):
    """Play an audio file with the given name."""
    audio_path = audio_dir / f"{audio_name}.ogg"
    # code to play the audio file goes here

# Add package metadata
__version__ = "1.0.0"
__author__ = "John Doe"
__description__ = "A bot that taunts you with audio clips from Age of Empires II."

# Add port information
PORT = 8080
