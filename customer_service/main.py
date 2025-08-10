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
            console.print(f"[bold blue][CONFIG][/bold blue] Loading config from: {config_path}")
            with open(config_path, "r") as file:
                self.config = yaml.safe_load(file)
            
            console.print("[bold green][CONFIG] ✅ Config loaded successfully![/bold green]")
            console.print("[bold blue][CONFIG] 📋 Full config content:[/bold blue]")
            console.print(f"[cyan][CONFIG]   {self.config}[/cyan]")
            
            # แสดงค่า MediaPipe config
            if 'mediapipe' in self.config:
                console.print("[bold yellow][CONFIG] 🎥 MediaPipe settings:[/bold yellow]")
                for key, value in self.config['mediapipe'].items():
                    console.print(f"[green][CONFIG]   - {key}: {value}[/green]")
            
            # แสดงค่า threshold config
            if 'threshold' in self.config:
                console.print("[bold yellow][CONFIG] 🎯 Threshold settings:[/bold yellow]")
                for key, value in self.config['threshold'].items():
                    console.print(f"[green][CONFIG]   - {key}: {value}[/green]")
            
        except FileNotFoundError:
            console.print(f"[bold red][CONFIG] ❌ Config file not found at {config_path}[/bold red]")
            raise FileNotFoundError(f"Required config file not found: {config_path}")
        except Exception as e:
            console.print(f"[bold red][CONFIG] ❌ Error loading config: {e}[/bold red]")
            raise

    def load_model(self):
        os.environ['GLOG_minloglevel'] = '2'
        
        # Set MediaPipe GPU mode based on gpu_mode parameter
        if self.gpu_mode:
            # Enable GPU acceleration for MediaPipe
            os.environ['MEDIAPIPE_GPU'] = '1'
            console.print("[bold green]MediaPipe configured to use GPU acceleration[/bold green]")
        else:
            # Force CPU mode for MediaPipe
            os.environ['MEDIAPIPE_GPU'] = '0'
            console.print("[bold yellow]MediaPipe configured to use CPU only[/bold yellow]")
        
        self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=self.static_image_mode,
            max_num_faces=self.max_num_faces,
            min_detection_confidence=self.min_detection_confidence
        )

    def process_image(self, file_path: str):
        import json

        output_crop_face_dir = os.path.dirname(file_path)
        result = { "message": None, "align_face": None, "bbox": None }
        success, msg, landmarks, bbox, norm_box = get_lm(file_path)

        if not success:
            result["message"] = msg
        else:
            console.print(f"[bold cyan][PROCESS] 🖼️  Processing image:[/bold cyan] [green]{os.path.basename(file_path)}[/green]")
            console.print("[bold blue][PROCESS] 📊 Using threshold values from config:[/bold blue]")
            console.print(f"[yellow][PROCESS]   - face_size: {self.config['threshold']['face_size']}[/yellow]")
            console.print(f"[yellow][PROCESS]   - blur: {self.config['threshold']['blur']}[/yellow]")
            console.print(f"[yellow][PROCESS]   - dark_threshold: {self.config['threshold']['dark_threshold']}[/yellow]")
            console.print(f"[yellow][PROCESS]   - bright_threshold: {self.config['threshold']['bright_threshold']}[/yellow]")
            console.print(f"[yellow][PROCESS]   - diff_threshold: {self.config['threshold']['diff_threshold']}[/yellow]")
            console.print(f"[yellow][PROCESS]   - margin: {self.config['threshold']['margin']}[/yellow]")
            console.print(f"[yellow][PROCESS]   - head_fully_th: {self.config['threshold']['head_fully_th']}[/yellow]")
            console.print(f"[yellow][PROCESS]   - EAR_THRESHOLD: {self.config['threshold']['EAR_THRESHOLD']}[/yellow]")
            console.print(f"[yellow][PROCESS]   - left_th: {self.config['threshold']['left_th']}[/yellow]")
            console.print(f"[yellow][PROCESS]   - right_th: {self.config['threshold']['right_th']}[/yellow]")
            console.print(f"[yellow][PROCESS]   - down_th: {self.config['threshold']['down_th']}[/yellow]")
            console.print(f"[yellow][PROCESS]   - up_th: {self.config['threshold']['up_th']}[/yellow]")
            console.print(f"[yellow][PROCESS]   - til_left_th: {self.config['threshold']['til_left_th']}[/yellow]")
            console.print(f"[yellow][PROCESS]   - til_right_th: {self.config['threshold']['til_right_th']}[/yellow]")
            
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
                if name == "check_face_min_size":
                    console.print(f"[bold magenta][PROCESS] 🔍 {name}:[/bold magenta] [cyan]checking bbox={args[0]} with min_size={args[1]}[/cyan]")
                elif name == "check_lightpol":
                    console.print(f"[bold magenta][PROCESS] 🔍 {name}:[/bold magenta] [cyan]checking file={os.path.basename(args[0])} with dark_th={args[1]}, bright_th={args[2]}, diff_th={args[3]}, margin={args[4]}[/cyan]")
                elif name == "check_face_blur":
                    console.print(f"[bold magenta][PROCESS] 🔍 {name}:[/bold magenta] [cyan]checking file={os.path.basename(args[0])} with blur_threshold={args[1]}[/cyan]")
                elif name == "check_head_fully":
                    console.print(f"[bold magenta][PROCESS] 🔍 {name}:[/bold magenta] [cyan]checking file={os.path.basename(args[0])} with head_fully_th={args[1]}[/cyan]")
                elif name == "check_head_pose":
                    console.print(f"[bold magenta][PROCESS] 🔍 {name}:[/bold magenta] [cyan]checking file={os.path.basename(args[0])} with left_th={args[1]}, right_th={args[2]}, down_th={args[3]}, up_th={args[4]}, til_left_th={args[5]}, til_right_th={args[6]}[/cyan]")
                elif name == "check_eye":
                    console.print(f"[bold magenta][PROCESS] 🔍 {name}:[/bold magenta] [cyan]checking landmarks with EAR_THRESHOLD={args[3]}[/cyan]")
                else:
                    console.print(f"[bold magenta][PROCESS] 🔍 {name}:[/bold magenta] [cyan]args={args[1:] if len(args) > 1 else 'no params'}[/cyan]")
                
                try:
                    success, msg = func(*args, **kwargs)
                    status_icon = '✅' if success else '❌'
                    status_color = 'green' if success else 'red'
                    console.print(f"[bold {status_color}][PROCESS] {status_icon} {name} result:[/bold {status_color}] [white]success={success}, message='{msg}'[/white]")
                except Exception as e:
                    console.print(f"[bold red][PROCESS] 💥 {name} ERROR:[/bold red] [red]{str(e)}[/red]")
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
    console.print("\n[bold yellow]Received shutdown signal. Closing connection...[/bold yellow]")
    try:
        if 'queue_handler' in globals():
            queue_handler.close()
    except Exception as e:
        console.print(f"[bold red]Error closing connection: {e}[/bold red]")
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
    console.print("[bold blue]Starting model handler...[/bold blue]")
    console.print(f"[bold green]GPU Mode: {gpu_mode}[/bold green]")
    model_handler = ModelHandler(gpu_mode=gpu_mode)
    global queue_handler
    queue_handler = QueueHandler(model_handler)
    console.print("[bold blue]Connecting to RabbitMQ...[/bold blue]")
    queue_handler.connect()
    art.tprint("N. Face Verification")
    console.print(f"[bold green]{time.strftime('%Y-%m-%d %H:%M:%S')} - Face Verification node started.[/bold green]")
    console.print("[bold blue]Starting to consume messages...[/bold blue]")
    queue_handler.start_consuming()
