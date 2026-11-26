import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path
import base64
from io import BytesIO

import piexif
from PIL import Image, ExifTags
import requests

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_OLLAMA_MODEL = "qwen3-vl:2b"
OLLAMA_THUMBNAIL_SIZE = (512, 512)
PNG_EXTENSIONS = (".png",)
JPEG_EXTENSIONS = (".jpg", ".jpeg",)
PHOTO_EXTENSIONS = PNG_EXTENSIONS + JPEG_EXTENSIONS
EXIF_ORIENTATION_TAG = [k for k, v in ExifTags.TAGS.items() if v == "Orientation"][0]

log_type = dict[str, str | int | None]


class PhotoOrienter:

    def __init__(self, source_directory: Path, target_directory: Path, dry_run: bool,
                 report: Path | None = None, log_level: str = 'INFO',
                 ollama_url: str = DEFAULT_OLLAMA_URL, ollama_model: str | None = DEFAULT_OLLAMA_MODEL) -> None:
        self.source_directory = source_directory
        self.target_directory = target_directory
        self.dry_run = dry_run
        self.report = report
        self.log_level = log_level
        self.logger = logging.getLogger("PhotoOrientation")
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.processing_report: list[log_type] = []

        self._setup_logging(self.log_level)

    def _rotate_png(self, file: Path, rotation: int) -> bool:
        try:
            with Image.open(file) as orig_img:
                new_image = orig_img.rotate(-rotation, expand=True)
                exif = orig_img.getexif()
                exif[EXIF_ORIENTATION_TAG] = 1
                new_file = self.target_directory / file.name
                new_image.save(new_file, exif=exif, format="PNG")
                self.logger.debug(f"{str(file)}: Updated and exif updated: {exif}")
                return True
        except (FileNotFoundError, OSError) as e:
            self.logger.warning(f"{file}: Error rotating PNG: {e}")
            return False

    def _rotate_jpg(self, file: Path, rotation: int) -> bool:
        try:
            # -rotate <angle> -copy all preserves metadata while rotating structure
            cmd = ["jpegtran", f"-rotate", str(rotation), "-copy", "all", str(file)]
            with open(self.target_directory / file.name, "wb") as f_out:
                result = subprocess.run(cmd, stdout=f_out, stderr=subprocess.PIPE, text=True)
                if result.returncode != 0:
                    self.logger.warning(f"{str(file)}: Failed to rotate jpg file: {result.stderr}")
                    return False

            self.logger.info(f"{str(file)}: Successfully rotated jpg file")
            exif_dict = piexif.load(str(file))
            if "0th" in exif_dict and piexif.ImageIFD.Orientation in exif_dict["0th"]:
                exif_dict["0th"][piexif.ImageIFD.Orientation] = 1
                exif_bytes = piexif.dump(exif_dict)
                piexif.insert(exif_bytes, str(self.target_directory / file.name))
                self.logger.debug(f"{str(file)}: Exif updated: {exif_dict}")
            return True
        except (FileNotFoundError, OSError) as e:
            self.logger.warning(f"{str(file)}: Error rotating jpg file: {e}")
            return False

    def _rotate_file(self, file: Path, rotation: int) -> bool:
        self.logger.debug(f" {str(file)}: Rotating file")
        suffix = file.suffix.lower()
        if suffix in JPEG_EXTENSIONS:
            return self._rotate_jpg(file, rotation)
        if suffix in PNG_EXTENSIONS:
            return self._rotate_png(file, rotation)
        else:
            self.logger.warning(f"Unsupported file type: {file.suffix}")
            return False

    def _setup_logging(self, log_level: str) -> None:

        self.logger.setLevel(log_level)

        if not self.logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)

            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)

            self.logger.addHandler(console_handler)

    def _get_exif(self, file: Path) -> int | None:
        try:
            with Image.open(file) as img:
                exif = img.getexif()
                for tag, value in exif.items():
                    decoded = ExifTags.TAGS.get(tag, tag)
                    if decoded == "Orientation":
                        self.logger.info(f"{str(file)}: Orientation tag found")
                        if value == 1:
                            # 1 implies image is already upright
                            return 0
                        elif value in [3, 6, 8]:
                            # Map standard EXIF to degrees
                            return {3: 180, 6: 90, 8: 270}.get(value, 0)
                return None
        except (AttributeError, KeyError):
            self.logger.warning(f"{str(file)}: Error checking EXIF data")

    @staticmethod
    def _convert_to_base64(img) -> str:
        thumbnail = img.copy()
        thumbnail.thumbnail(OLLAMA_THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        buffered = BytesIO()
        thumbnail.convert("RGB").save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str

    def _ai_get_rotation(self, file: Path) -> int | None:

        with Image.open(file) as img:

            img_base64 = self._convert_to_base64(img)

            payload = {
                "model": self.ollama_model,  # or any local vision model loaded in Ollama
                "prompt":
                    "Analyze this image to determine its orientation. DO NOT modify teh image. DO NOT be conversational. "
                    "Reply ONLY a JSON payload of format {message: <SUCCESS or the error message>, rotation: <integer>}, "
                    "with any errors you encountered or with a single integer representing clockwise rotation required to "
                    "make it upright; Possible values are : 0, 90, 180, or 270.",
                "images": [img_base64],
                "stream": False,
                "options": {
                    "num_predict": 10,
                    "temperature": 0
                }
            }

            try:
                response = requests.post(self.ollama_url, json=payload, timeout=10)
                if response.status_code == 200:
                    text = response.json().get("response", "").strip()
                    self.logger.debug(f"{str(file)}: AI Response {text}")
                    if "SUCCESS" in text and "rotation" in text:
                        try:
                            rotation_value = int(text.split("rotation:")[1].split("}")[0].strip())
                            if rotation_value in [0, 90, 180, 270]:
                                self.logger.debug(f"{str(file)}: Got rotation {rotation_value}")
                                return rotation_value
                            else:
                                self.logger.warning(f"{str(file)}: Invalid rotation value from AI: {rotation_value}")
                        except (ValueError, IndexError) as e:
                            self.logger.warning(f"{str(file)}: Error parsing rotation from AI response: {e}")

                    else:
                        self.logger.debug(f"{str(file)}: Didn't find an angle or there's an error {text}")
                else:
                    self.logger.warning(f"{str(file)}: Error from AI call {response.status_code}: {response.text}")

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"{str(file)}: Error from AI call: {e}")

    def _process_file(self, file: Path) -> log_type:
        log_record: log_type = {
            "source_filename": str(file),
            "status": "Unchanged",
            "rotated_by": None,
            "rotation_angle": None,
        }

        rotation = self._get_exif(file)
        if rotation is not None:
            if self.dry_run:
                self.logger.debug(f"{str(file)}: Dry run, got exif but skipping")
            elif rotation != 0:
                if self._rotate_file(file, rotation):
                    log_record["status"] = "Changed"
                    log_record["rotated_by"] = "EXIF"
                    log_record["rotation_angle"] = rotation
        else:
            if self.dry_run:
                self.logger.debug(f"{str(file)}: Dry run, no EXIF but skipping")
            else:
                self.logger.debug(f"{str(file)}: No EXIF so passing to AI")
                rotation = self._ai_get_rotation(file)
                if rotation and self._rotate_file(file, rotation):
                    log_record["status"] = "Changed"
                    log_record["rotated_by"] = "AI"
                    log_record["rotation_angle"] = rotation

        return log_record

    def process_files(self) -> list[log_type]:

        for file in Path.glob(self.source_directory, "*"):
            if os.path.isfile(file) \
                    and os.path.splitext(file)[1].lower() in PHOTO_EXTENSIONS:
                self.logger.debug("Processing file: %s", file)
                file_report = self._process_file(file)
                self.processing_report.append(file_report)
            else:
                self.logger.debug("Ignoring file: %s", file)

        return self.processing_report


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_directory", type=Path, help="Directory containing photos")
    parser.add_argument("target_directory", type=Path, help="Directory to write amended photos to")
    parser.add_argument("--dry_run", action="store_true", help="Dry run - make no changes")
    parser.add_argument("--report", type=Path, help="Location for logfile")
    parser.add_argument("--log_level", choices=logging._nameToLevel.keys(), help="Log level", default='INFO')
    parser.add_argument(
        "--url",
        default=DEFAULT_OLLAMA_URL,
        help="Ollama generate API URL",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_OLLAMA_MODEL,
        help="Ollama vision model to use for orientation detection",
    )
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = get_args()
    processor = PhotoOrienter(
        cli_args.source_directory,
        cli_args.target_directory,
        cli_args.dry_run,
        cli_args.report,
        cli_args.log_level,
        cli_args.url,
        cli_args.model,
    )
    report = processor.process_files()
    pass
