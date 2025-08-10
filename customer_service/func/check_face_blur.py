import cv2
import numpy as np
import mediapipe as mp
from rich.console import Console

# Initialize Rich Console
console = Console()

def _patch_from_contour(img, contour):
    mask = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
    cv2.fillPoly(mask, [contour.astype(np.int32)], 255)

    xmin = max(0, int(np.min(contour[:, 0])))
    xmax = min(img.shape[1], int(np.max(contour[:, 0])))
    ymin = max(0, int(np.min(contour[:, 1])))
    ymax = min(img.shape[0], int(np.max(contour[:, 1])))

    if xmax <= xmin or ymax <= ymin:
        return None, (0, 0)

    out = img.copy()
    out[mask == 0] = (255, 255, 255)

    cropped_img = out[ymin:ymax, xmin:xmax]
    if cropped_img.size == 0:
        return None, (0, 0)
    if len(cropped_img.shape) == 3:
        cropped_img = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)

    return cropped_img, (xmin, ymin)


def check_face_blur(image, threshold):
    """
    ตรวจสอบว่าบริเวณใบหน้าในภาพเบลอหรือไม่ โดยใช้ MediaPipe และ Laplacian variance
    
    Parameters
    ----------
    image : str หรือ numpy.ndarray
        path ของภาพ หรืออาเรย์ภาพแบบ BGR
    threshold : float
        ค่า threshold ที่ใช้ตัดสินความเบลอ
    
    Returns
    -------
    variance : float หรือ None
        ค่าความแปรปรวนของ Laplacian หรือ None ถ้ามีปัญหา
    message : str
        ข้อความแจ้งผลลัพธ์
    """
    console.print(f"[bold cyan][BLUR] 🔍 Checking blur:[/bold cyan] [white]image={image if isinstance(image, str) else 'numpy_array'}, threshold={threshold}[/white]")
    
    if threshold <= 0:
        console.print("[bold red][BLUR] ❌ Threshold must be positive[/bold red]")
        return None, "Threshold must be positive"

    if isinstance(image, str):
        console.print(f"[bold blue][BLUR] 📸 Loading image from file:[/bold blue] [yellow]{image}[/yellow]")
        img = cv2.imread(image)
        if img is None:
            console.print("[bold red][BLUR] ❌ Cannot read image[/bold red]")
            return None, "Cannot read image"
    else:
        console.print("[bold blue][BLUR] 📸 Using provided numpy array[/bold blue]")
        img = image

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # ย้ายการสร้าง face_detection เข้าในฟังก์ชัน
    console.print("[bold blue][BLUR] 🔍 Processing face detection...[/bold blue]")
    with mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
        results = face_detection.process(img_rgb)

        if not results.detections:
            console.print("[bold red][BLUR] ❌ No face detected[/bold red]")
            return None, "No face detected"

        console.print("[bold green][BLUR] ✅ Face detected, analyzing blur...[/bold green]")
        detection = results.detections[0]
        bbox = detection.location_data.relative_bounding_box
        h, w, _ = img.shape

        xmin = int(bbox.xmin * w)
        ymin = int(bbox.ymin * h)
        width = int(bbox.width * w)
        height = int(bbox.height * h)
        
        console.print(f"[bold cyan][BLUR] 📦 Face bounding box:[/bold cyan] [yellow]({xmin}, {ymin}, {width}, {height})[/yellow]")

        contour = np.array([
            [xmin, ymin],
            [xmin + width, ymin],
            [xmin + width, ymin + height],
            [xmin, ymin + height]
        ], dtype=np.int32)

        face_img, _ = _patch_from_contour(img, contour)
        if face_img is None:
            console.print("[bold red][BLUR] ❌ Invalid face region[/bold red]")
            return None, "Invalid face region"

        variance = cv2.Laplacian(face_img, cv2.CV_64F).var()
        console.print(f"[bold cyan][BLUR] 📊 Laplacian variance:[/bold cyan] [yellow]{variance:.2f}[/yellow] [white](threshold: {threshold})[/white]")

        if variance < threshold:
            console.print(f"[bold red][BLUR] ❌ Image is blurry ({variance:.2f} < {threshold})[/bold red]")
            return False, "Image is blurry"
        console.print(f"[bold green][BLUR] ✅ Image is not blurry ({variance:.2f} >= {threshold})[/bold green]")
        return True, "Image isn't blurry"