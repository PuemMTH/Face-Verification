import PIL
import cv2
import numpy as np
import scipy
import PIL.Image

import numpy as np
import PIL.Image
import scipy.ndimage

def ffhq_align(img, landmarks, output_size=1024):
    lm = landmarks
    if lm is None:
        return None

    # แยก landmarks ออกเป็นส่วนต่าง ๆ
    lm = np.array(lm)
    lm_eye_left = lm[[33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7]]
    lm_eye_right = lm[[463, 398, 384, 385, 386, 387, 388, 466, 263, 249, 390, 373, 374, 380, 381, 382, 362]]
    lm_mouth_outer   = lm[[61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185]]  # left-clockwise

    # คำนวณเวกเตอร์ช่วย
    eye_left     = np.mean(lm_eye_left, axis=0)
    eye_right    = np.mean(lm_eye_right, axis=0)
    eye_avg      = (eye_left + eye_right) * 0.5
    eye_to_eye   = eye_right - eye_left
    mouth_left   = lm_mouth_outer[0]
    mouth_right  = lm_mouth_outer[10]
    mouth_avg    = (mouth_left + mouth_right) * 0.5
    eye_to_mouth = mouth_avg - eye_avg

    # เลือกสี่เหลี่ยมครอบภาพที่ปรับทิศทาง
    x = eye_to_eye - np.flipud(eye_to_mouth) * [-1, 1]
    x /= np.hypot(*x)
    x *= max(np.hypot(*eye_to_eye) * 2.0, np.hypot(*eye_to_mouth) * 1.8)
    y = np.flipud(x) * [-1, 1]
    c = eye_avg + eye_to_mouth * 0.1
    quad = np.stack([c - x - y, c - x + y, c + x + y, c + x - y])
    qsize = np.hypot(*x) * 2

    # แปลงเป็น PIL.Image
    pil_img = PIL.Image.fromarray(img)

    transform_size = 4096
    enable_padding = True

    # Shrink
    shrink = int(np.floor(qsize / output_size * 0.5))
    if shrink > 1:
        rsize = (int(np.rint(float(pil_img.size[0]) / shrink)), int(np.rint(float(pil_img.size[1]) / shrink)))
        pil_img = pil_img.resize(rsize, PIL.Image.LANCZOS)
        quad /= shrink
        qsize /= shrink

    # Crop
    border = max(int(np.rint(qsize * 0.1)), 3)
    crop = (int(np.floor(min(quad[:,0]))), int(np.floor(min(quad[:,1]))), int(np.ceil(max(quad[:,0]))), int(np.ceil(max(quad[:,1]))))
    crop = (max(crop[0] - border, 0), max(crop[1] - border, 0), min(crop[2] + border, pil_img.size[0]), min(crop[3] + border, pil_img.size[1]))
    if crop[2] - crop[0] < pil_img.size[0] or crop[3] - crop[1] < pil_img.size[1]:
        pil_img = pil_img.crop(crop)
        quad -= crop[0:2]

    # Pad (ปรับส่วนนี้)
    pad = (int(np.floor(min(quad[:,0]))), int(np.floor(min(quad[:,1]))), int(np.ceil(max(quad[:,0]))), int(np.ceil(max(quad[:,1]))))
    pad = (max(-pad[0] + border, 0), max(-pad[1] + border, 0), max(pad[2] - pil_img.size[0] + border, 0), max(pad[3] - pil_img.size[1] + border, 0))
    if enable_padding and max(pad) > border - 4:
        # แทนที่การเติมแบบสะท้อนด้วยสีดำ
        pad = np.maximum(pad, int(np.rint(qsize * 0.3)))
        # แปลง PIL เป็น NumPy เพื่อใช้ np.pad
        img_array = np.array(pil_img)
        # เติมด้วยสีดำ (constant_values=0)
        padded_img = np.pad(img_array, ((pad[1], pad[3]), (pad[0], pad[2]), (0, 0)), mode='constant', constant_values=0)
        # แปลงกลับเป็น PIL
        pil_img = PIL.Image.fromarray(padded_img)
        quad += pad[:2]
    # ถ้าไม่เข้าเงื่อนไข padding จะไม่มีการเติม

    # Transform
    pil_img = pil_img.transform((transform_size, transform_size), PIL.Image.QUAD, (quad + 0.5).flatten(), PIL.Image.BILINEAR)
    if output_size < transform_size:
        pil_img = pil_img.resize((output_size, output_size), PIL.Image.LANCZOS)

    # คืนค่าเป็น NumPy array
    return np.array(pil_img)

# ตัวอย่างการเรียกใช้ (ถ้าต้องการทดสอบ)
# img = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)  # ตัวอย่างภาพ
# landmarks = np.random.rand(68, 2) * 512  # ตัวอย่าง landmarks
# aligned_img = ffhq_align2(img, landmarks, output_size=1024)