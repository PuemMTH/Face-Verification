import os
import mediapipe as mp
import yaml

from func.check_head_pose import check_head_pose
from func.alignfaces import align_face
from func.check_face_blur import check_face_blur
from func.check_face_size import check_face_min_size
from func.check_light_pollution import check_lightpol
from func.check_eye import check_eye_status
from func.get_landmarks import get_lm
from func.check_head_fully import analyze_single_image

# set path
image_path = r"C:\Users\naphatnan\Desktop\Work\NECTEC\Face-Verification\Error\other\02c33a77-379d-42ff-b7d4-13e075f11017_front.jpg"

os.environ['GLOG_minloglevel'] = '2'

# โหลดค่า config จากไฟล์ yml
with open("config.yml", "r") as file:
    config = yaml.safe_load(file)
    
output_crop_face_dir = "output"
result = {
    "message": None,
    "align_face": None,
    "bbox": None
}

mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=10,
    min_detection_confidence=0.5
)

# หา landmarks จากใบหน้า
success, msg, landmarks, bbox = get_lm(image_path)

if not success:
    result["message"] = msg
else:
    funcs = [
        ("check_face_min_size", check_face_min_size, [bbox, config['threshold']['face_size']], {}),
        ("check_eye", check_eye_status, [landmarks, success, msg, config['threshold']['EAR_THRESHOLD']], {}),
        ("check_lightpol", check_lightpol, [image_path,config['threshold']['dark_threshold'],config['threshold']['bright_threshold'],config['threshold']['diff_threshold'],config['threshold']['margin']], {}),
        ("check_face_blur", check_face_blur, [image_path, config['threshold']['blur']], {}),
        ("check_head_fully",analyze_single_image,[image_path],{}),
        ("check_head_pose",check_head_pose,[image_path],{}),
    ]

    all_passed = True

    for name, func, args, kwargs in funcs:
        success, msg = func(*args, **kwargs)
        if not success:
            if result["message"] is None:
                result["message"] = msg
            all_passed = False


    if all_passed:
        align_face(image_path, output_crop_face_dir, mp_face_mesh)
        image_filename = f"{os.path.basename(image_path).split('.')[0]}_aligned.png"
        image_save_path = os.path.join(output_crop_face_dir, image_filename)
        result["align_face"] = image_save_path
        result["bbox"] = bbox

print(result)
