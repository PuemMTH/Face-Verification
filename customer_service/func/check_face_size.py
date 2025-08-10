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
    console.print(f"[bold cyan][SIZE] 📏 Checking face size:[/bold cyan] [white]bbox={bbox}, min_size={min_size}[/white]")
    
    if bbox is None:
        console.print("[bold red][SIZE] ❌ No bounding box provided[/bold red]")
        return (False, "No bounding box provided")

    x, y, w, h = bbox
    console.print(f"[bold blue][SIZE] 📐 Face dimensions:[/bold blue] [yellow]w={w}, h={h}[/yellow] [white](required min_size={min_size})[/white]")
    
    if w > min_size and h > min_size:
        console.print(f"[bold green][SIZE] ✅ Face size passes criteria ({w}x{h} > {min_size})[/bold green]")
        return (True, "The face size passes the specified criteria.")
    else:
        console.print(f"[bold red][SIZE] ❌ Face size does not meet criteria ({w}x{h} <= {min_size})[/bold red]")
        return (False, "The face size does not meet the specified criteria.")