# Hướng dẫn thiết lập Ollama và Qwen Model (Local)

Tài liệu này cung cấp các bước để cài đặt động cơ LLM local (Ollama) và tải model Qwen để làm baseline cho chatbot, phục vụ cho **Issue #10**.

## 1. Cài đặt Ollama
Tải và cài đặt Ollama tương ứng với hệ điều hành của bạn:
- **Mac/Windows:** Tải file cài đặt trực tiếp tại [Ollama Download Page](https://ollama.com/download).
- **Linux:** Chạy lệnh sau trong Terminal:
  ```bash
  curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh
Kiểm tra quá trình cài đặt bằng lệnh:

    ollama --version
Chạy Qwen2.5 3b
    
    ollama run qwen2.5:3b