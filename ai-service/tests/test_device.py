from app.core import device


def test_auto_prefers_cuda_when_available(monkeypatch):
    monkeypatch.setattr(device, "cuda_available", lambda: True)
    assert device.resolve_device("auto") == "cuda"


def test_auto_falls_back_to_cpu_without_gpu(monkeypatch):
    monkeypatch.setattr(device, "cuda_available", lambda: False)
    assert device.resolve_device("auto") == "cpu"
    assert device.resolve_device("") == "cpu"


def test_explicit_cuda_without_gpu_falls_back_to_cpu(monkeypatch):
    monkeypatch.setattr(device, "cuda_available", lambda: False)
    assert device.resolve_device("cuda:0") == "cpu"


def test_explicit_values_are_respected(monkeypatch):
    monkeypatch.setattr(device, "cuda_available", lambda: True)
    assert device.resolve_device("cpu") == "cpu"
    assert device.resolve_device("CUDA:0") == "cuda:0"
