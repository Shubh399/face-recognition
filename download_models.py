import os
import urllib.request

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(APP_DIR, "models")
MODELS = {
    "face_detection_yunet_2023mar.onnx": (
        "https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/"
        "face_detection_yunet/face_detection_yunet_2023mar.onnx"
    ),
    "face_recognition_sface_2021dec.onnx": (
        "https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/"
        "face_recognition_sface/face_recognition_sface_2021dec.onnx"
    ),
}


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    for filename, url in MODELS.items():
        destination = os.path.join(MODEL_DIR, filename)
        if os.path.isfile(destination) and os.path.getsize(destination) > 0:
            print(f"Already present: {filename}")
            continue
        temporary = destination + ".download"
        print(f"Downloading {filename}...")
        try:
            urllib.request.urlretrieve(url, temporary)
            if os.path.getsize(temporary) == 0:
                raise OSError(f"Downloaded an empty model: {filename}")
            os.replace(temporary, destination)
        except Exception:
            if os.path.exists(temporary):
                os.remove(temporary)
            raise
        print(f"Saved: {destination}")


if __name__ == "__main__":
    main()
