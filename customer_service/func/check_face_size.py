import os
import cv2
from rich.console import Console

# Initialize Rich Console
console = Console()

def check_face_min_size(bbox, min_size):
    """
    Checks if the face bounding box meets the minimum size criteria.
    Args:
        bbox: Tuple of (x, y, w, h) representing the bounding box
        min_size: Minimum size (in pixels) for width and height
    Returns:
        (success, message)
        - success: Boolean indicating if the face size meets the criteria
        - message: String with status message
    """
    
    if bbox is None:
        console.print("[bold red]\t- SIZE[/bold red] | No bounding box")
        return (False, "No bounding box provided")

    x, y, w, h = bbox
    
    if w > min_size and h > min_size:
        return (True, "The face size passes the specified criteria.")
    else:
        console.print(f"[bold red]\t- SIZE[/bold red] | Too small ({w}x{h} <= {min_size})")
        return (False, "The face size does not meet the specified criteria.")