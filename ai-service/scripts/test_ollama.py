import sys
import os

# Đảm bảo có thể import module từ thư mục app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from llm_client import OllamaClient

def main():
    print("Đang khởi tạo cấu hình Ollama...")
    try:
        # Client sẽ tự động đọc từ .env
        client = OllamaClient()
        print(f"[OK] Cấu hình load thành công:")
        print(f"     - Base URL: {client.base_url}")
        print(f"     - Model:    {client.model_name}\n")
        
        test_prompt = "Xin chào, bạn là ai? Hãy trả lời ngắn gọn trong 1-2 câu."
        print(f"User: {test_prompt}")
        print("Đang chờ phản hồi từ model (quá trình này có thể mất vài giây lần đầu tiên)...\n")
        
        response = client.generate(test_prompt)
        print(f"Bot: {response}\n")
        print("[THÀNH CÔNG] - Đã kết nối và nhận phản hồi từ Ollama local.")
        
    except Exception as e:
        print(f"\n[THẤT BẠI] - Có lỗi xảy ra trong quá trình test: {e}")

if __name__ == "__main__":
    main()