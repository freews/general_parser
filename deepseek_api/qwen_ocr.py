import requests
import base64
import json
import logger
from deepseek_api.deepseek_ocr import DeepSeekOCR

class QwenOCR(DeepSeekOCR):
    def __init__(self, base_url="http://localhost:11434", model="qwend"):
        super().__init__(base_url, model)
        self.model = model

    def with_layout(self, image_path, stream=False):
        """
        Qwen-specific layout extraction.
        Qwen-VL typically needs a specific prompt to output bounding boxes.
        We will try a standard prompt for layout detection.
        """
        # Prompt engineering for Qwen-VL to get bounding boxes
        # This might need adjustment based on the specific Qwen model version
        prompt = "Detect the layout of this document image. Identify tables, figures, titles, and text blocks. Provide bounding boxes for each element."
        # Or if it's fine-tuned like DeepSeek, maybe the same prompt works?
        # Let's try a generic detailed prompt first.
        
        return self._call_api(image_path, prompt, stream)
