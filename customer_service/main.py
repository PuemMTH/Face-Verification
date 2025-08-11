import os
import signal
import time
import yaml
import art # type: ignore
import mediapipe as mp
import argparse

from rich.console import Console

from func.check_head_pose import check_head_pose
from func.alignfaces import align_face
from func.check_face_blur import check_face_blur
from func.check_face_size import check_face_min_size
from func.check_light_pollution import check_lightpol
from func.check_eye import check_eye_status
from func.get_landmarks import get_lm
from func.check_head_fully import analyze_single_image

from rabbitmq_handler import QueueHandler

# Initialize Rich Console
console = Console()



class ModelHandler:
    def __init__(self, static_image_mode = True, max_num_faces = 10, min_detection_confidence = 0.5, gpu_mode = True):
        self.static_image_mode = static_image_mode
        self.max_num_faces = max_num_faces
        self.min_detection_confidence = min_detection_confidence
        self.gpu_mode = gpu_mode
        self.load_config()
        self.load_model()
    
    def load_config(self):
        """Load configuration from config.yml file"""
        config_path = os.path.join(os.path.dirname(__file__), "config.yml")
        try:
            console.print(f"[bold blue]CONFIG[/bold blue] | Loading from: [cyan]{os.path.basename(config_path)}[/cyan]")
            with open(config_path, "r") as file:
                self.config = yaml.safe_load(file)
            
            console.print("[bold green]CONFIG[/bold green] | Loaded successfully")
            
        except FileNotFoundError:
            console.print(f"[bold red]CONFIG[/bold red] | File not found: {config_path}")
            raise FileNotFoundError(f"Required config file not found: {config_path}")
        except Exception as e:
            console.print(f"[bold red]CONFIG[/bold red] | Error: {e}")
            raise

    def load_model(self):
        os.environ['GLOG_minloglevel'] = '2'
        
        # Set MediaPipe GPU mode based on gpu_mode parameter
        if self.gpu_mode:
            os.environ['MEDIAPIPE_GPU'] = '1'
            console.print("[bold green]MODEL[/bold green] | GPU acceleration enabled")
        else:
            os.environ['MEDIAPIPE_GPU'] = '0'
            console.print("[bold yellow]MODEL[/bold yellow] | CPU mode only")
        
        self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=self.static_image_mode,
            max_num_faces=self.max_num_faces,
            min_detection_confidence=self.min_detection_confidence
        )

    def process_image(self, file_path: str):
        import json

        # Reload config for each image processing
        self.load_config()

        output_crop_face_dir = os.path.dirname(file_path)
        result = { "message": None, "align_face": None, "bbox": None }
        success, msg, landmarks, bbox, norm_box = get_lm(file_path)

        if not success:
            result["message"] = msg
        else:
            console.print(f"[bold cyan]PROCESSING[/bold cyan] | {os.path.basename(file_path)}")
            
            funcs = [
                ("check_face_min_size", check_face_min_size, [bbox, self.config['threshold']['face_size']], {}),
                ("check_lightpol", check_lightpol, [file_path,self.config['threshold']['dark_threshold'],self.config['threshold']['bright_threshold'],self.config['threshold']['diff_threshold'],self.config['threshold']['margin']], {}),
                ("check_face_blur", check_face_blur, [file_path, self.config['threshold']['blur']], {}),
                ("check_head_fully",analyze_single_image,[file_path, self.config['threshold']['head_fully_th']],{}),
                ("check_head_pose",check_head_pose,[file_path, self.config['threshold']['left_th'], self.config['threshold']['right_th'], self.config['threshold']['down_th'], self.config['threshold']['up_th'], self.config['threshold']['til_left_th'], self.config['threshold']['til_right_th']],{}),
                ("check_eye", check_eye_status, [landmarks, success, msg, self.config['threshold']['EAR_THRESHOLD']], {}),
            ]

            all_passed = True

            for name, func, args, kwargs in funcs:
                try:
                    success, msg = func(*args, **kwargs)
                    status_icon = 'PASS' if success else 'FAIL'
                    status_color = 'green' if success else 'red'
                    console.print(f"\t[bold {status_color}]{status_icon}[/bold {status_color}] | {name} - {msg}")
                except Exception as e:
                    console.print(f"\t[bold red]ERROR[/bold red] | {name} - Function error: {str(e)}")
                    success, msg = False, f"Function error: {str(e)}"
                
                if not success:
                    if result["message"] is None:
                        result["message"] = msg
                    all_passed = False

            if all_passed:
                align_face(file_path, output_crop_face_dir, self.mp_face_mesh)
                image_filename = f"{os.path.basename(file_path).split('.')[0]}_aligned.png"
                image_save_path = os.path.join(output_crop_face_dir, image_filename)
                result["align_face"] = image_save_path
                result["bbox"] = bbox
                console.print(f"[bold green]PROCESSING[/bold green] | All checks passed - Face aligned")
            else:
                console.print(f"[bold red]PROCESSING[/bold red] | Failed - {result['message']}")
        
        # Return JSON response
        if result["message"] is None:
            return json.dumps({
                'OK': True,
                'align_face': result["align_face"],
                'bbox': result["bbox"],
                'norm_box': norm_box
            })
        else:
            return json.dumps({
                'OK': False,
                'error': result["message"]
            })

def signal_handler(signum, frame):
    console.print("\n[bold yellow]SYSTEM[/bold yellow] | Shutdown signal received")
    try:
        if 'queue_handler' in globals():
            queue_handler.close()
    except Exception as e:
        console.print(f"[bold red]SYSTEM[/bold red] | Error closing: {e}")
    os._exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Face Verification Service")
    parser.add_argument("--gpu_mode", action="store_true", default=True, help="Enable GPU mode")
    parser.add_argument("--cpu_mode", action="store_true", help="Force CPU mode (overrides gpu_mode)")
    args = parser.parse_args()
    
    # Determine GPU mode
    gpu_mode = True if not args.cpu_mode else False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    console.print("[bold blue]STARTUP[/bold blue] | Initializing Face Verification Service")
    console.print(f"[bold green]STARTUP[/bold green] | GPU Mode: {gpu_mode}")
    model_handler = ModelHandler(gpu_mode=gpu_mode)
    global queue_handler
    queue_handler = QueueHandler(model_handler)
    console.print("[bold blue]RABBITMQ[/bold blue] | Connecting...")
    queue_handler.connect()
    art.tprint("N. Face Verification")
    console.print(f"[bold green]RABBITMQ[/bold green] | Service started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    queue_handler.start_consuming()
