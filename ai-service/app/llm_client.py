import os
import requests
import logging
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self):
        """Khởi tạo client kết nối với Ollama dựa trên biến môi trường."""
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL_NAME")
        
        if not self.model_name:
            raise ValueError("LỖI: Biến môi trường 'OLLAMA_MODEL_NAME' chưa được thiết lập. Hãy kiểm tra file .env.")

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        """
        Gửi prompt tới mô hình LLM qua API của Ollama.
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False  # Đặt thành True nếu muốn handle streaming response
        }
        
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi khi kết nối tới Ollama API: {e}")
            raise