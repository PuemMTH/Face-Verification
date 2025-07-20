import os
import signal
import time
import yaml
import art # type: ignore
import mediapipe as mp
import argparse

from func.check_head_pose import check_head_pose
from func.alignfaces import align_face
from func.check_face_blur import check_face_blur
from func.check_face_size import check_face_min_size
from func.check_light_pollution import check_lightpol
from func.check_eye import check_eye_status
from func.get_landmarks import get_lm
from func.check_head_fully import analyze_single_image

from rabbitmq_handler import QueueHandler



class ModelHandler:
    def __init__(self, static_image_mode = True, max_num_faces = 10, min_detection_confidence = 0.5, gpu_mode = True):
        self.static_image_mode = static_image_mode
        self.max_num_faces = max_num_faces
        self.min_detection_confidence = min_detection_confidence
        self.gpu_mode = gpu_mode
        with open("config.yml", "r") as file:
            self.config = yaml.safe_load(file)
        self.load_model()

    def load_model(self):
        os.environ['GLOG_minloglevel'] = '2'
        
        # Set MediaPipe GPU mode based on gpu_mode parameter
        if self.gpu_mode:
            # Enable GPU acceleration for MediaPipe
            os.environ['MEDIAPIPE_GPU'] = '1'
            print(f"MediaPipe configured to use GPU acceleration")
        else:
            # Force CPU mode for MediaPipe
            os.environ['MEDIAPIPE_GPU'] = '0'
            print(f"MediaPipe configured to use CPU only")
        
        self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=self.static_image_mode,
            max_num_faces=self.max_num_faces,
            min_detection_confidence=self.min_detection_confidence
        )

    def process_image(self, file_path: str):

        output_crop_face_dir = "output"
        result = { "message": None, "align_face": None, "bbox": None }

        success, msg, landmarks, bbox = get_lm(file_path)

        if not success:
            result["message"] = msg
        else:
            funcs = [
                ("check_face_min_size", check_face_min_size, [bbox, self.config['threshold']['face_size']], {}),
                ("check_eye", check_eye_status, [landmarks, success, msg, self.config['threshold']['EAR_THRESHOLD']], {}),
                ("check_lightpol", check_lightpol, [file_path,self.config['threshold']['dark_threshold'],self.config['threshold']['bright_threshold'],self.config['threshold']['diff_threshold'],self.config['threshold']['margin']], {}),
                ("check_face_blur", check_face_blur, [file_path, self.config['threshold']['blur']], {}),
                ("check_head_fully",analyze_single_image,[file_path],{}),
                ("check_head_pose",check_head_pose,[file_path],{}),
            ]

            all_passed = True

            for name, func, args, kwargs in funcs:
                success, msg = func(*args, **kwargs)
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

def signal_handler(signum, frame):
    print("\nReceived shutdown signal. Closing connection...")
    try:
        if 'queue_handler' in globals():
            queue_handler.close()
    except Exception as e:
        print(f"Error closing connection: {e}")
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
    try:
        print("Starting model handler...")
        print(f"GPU Mode: {gpu_mode}")
        model_handler = ModelHandler(gpu_mode=gpu_mode)
        global queue_handler
        queue_handler = QueueHandler(model_handler)
        print("Connecting to RabbitMQ...")
        queue_handler.connect()
        art.tprint("N. Face Verification")
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Face Verification node started.")
        print("Starting to consume messages...")
        queue_handler.start_consuming()

    except Exception as e:
        print(f"Error: {e}")
        os._exit(1)

    finally:
        print("Connection closed. Exiting...")
        os._exit(0)