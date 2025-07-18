import os
import cv2
import numpy as np
from func.align_func import ffhq_align

def align_face(image_path, output_crop_face_dir, mp_face_mesh):
    # ตรวจสอบว่าโฟลเดอร์สำหรับบันทึกมีอยู่หรือไม่ ถ้าไม่ให้สร้างใหม่
    if not os.path.exists(output_crop_face_dir):
        os.makedirs(output_crop_face_dir)

    # ตรวจสอบว่า image_path เป็น string และไฟล์มีอยู่จริง
    if not isinstance(image_path, str) or not os.path.exists(image_path):
        return False, f"Error: Invalid or non-existent image path: {image_path}"

    # ตรวจสอบนามสกุลไฟล์
    if not image_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        return False, f"Error: Skipping non-image file: {image_path}"

    # อ่านภาพจาก path
    frame = cv2.imread(image_path)
    if frame is None:
        return False, f"Error: Could not read image from {image_path}"

    # ตรวจหาใบหน้าภายในภาพ
    results = mp_face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    # ตรวจสอบว่าพบใบหน้าหรือไม่
    if not results.multi_face_landmarks:
        return False, f"Error: No face detected in {image_path}"

    # ควรมีใบหน้าเดียว ดึง landmarks จากใบหน้าแรก
    face_landmarks = results.multi_face_landmarks[0]
    points = []
    for landmark in face_landmarks.landmark:
        points.append([int(landmark.x * frame.shape[1]), int(landmark.y * frame.shape[0])])

    # แปลง points เป็น array 2D
    points = np.array(points)

    # แปลงภาพเป็น RGB เพื่อส่งให้ ffhq_align
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # เรียก ffhq_align โดยส่ง landmarks เข้าไป
    aligned_face = ffhq_align(frame_rgb, points)

    # ตรวจสอบว่ามีการ align ได้หรือไม่
    if aligned_face is None:
        return False, f"Error: Alignment failed for {image_path}"

    # สร้างชื่อไฟล์สำหรับบันทึก
    image_filename = f"{os.path.basename(image_path).split('.')[0]}_aligned.png"
    image_save_path = os.path.join(output_crop_face_dir, image_filename)

    # แปลง aligned_face กลับเป็น BGR เพื่อบันทึกด้วย cv2
    aligned_face_bgr = cv2.cvtColor(aligned_face, cv2.COLOR_RGB2BGR)
    cv2.imwrite(image_save_path, aligned_face_bgr)

    return True, f"Success: Aligned face saved to {image_save_path}"