import base64
import cv2

def extract_gif_frames(path: str, n: int = 3, size: int = 240) -> list[str]:
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    margin = int(total * 0.05)
    start, end = margin, total - margin
    indices = [int(start + (end - start) * i / (n - 1)) for i in range(n)] if n > 1 else [total // 2]
    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue
        h, w = frame.shape[:2]
        scale = size / max(h, w)
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frames.append(base64.b64encode(buf).decode())
    cap.release()
    return frames