# Versions

## Hardware
| Component | Details |
|---|---|
| GPU | NVIDIA GeForce RTX 2060 Super, 8 GB VRAM |
| GPU driver | 595.91.07 (CUDA up to 13.2) |
| CPU | Intel Core i5-12600K (10 cores / 16 threads) |
| RAM | 32 GB + 8 GB swap |
| Disk | 256 GB NVMe SSD |
| OS | Ubuntu 24.04.5 LTS, kernel 7.0.0-34 |

## Training environment (`.venv`)
| Item | Version |
|---|---|
| Python | 3.12.3 |
| PyTorch | 2.12.1+cu130 (CUDA 13.0) |
| unsloth | 2026.9.14 |
| transformers | 5.5.0 |
| peft | 0.21.2 |
| trl | 0.24.0 |
| bitsandbytes | 0.50.2 |
| huggingface_hub | 1.33.0 |
| Full package list | see `requirements.lock` (after smoke test) |

## llama.cpp conversion environment (`.venv-llamacpp`)
| Item | Version |
|---|---|
| Installed from | `~/llama.cpp/requirements.txt` at the commit below |
| PyTorch | 2.11.0+cpu |
| transformers | 4.57.6 |
| gguf | 0.19.0 |
| Full package list | see `requirements-llamacpp.lock` (after smoke test) |

## Models and tools
| Item | Version |
|---|---|
| Base model | `Qwen/Qwen2.5-7B-Instruct` @ `a09a35458c702b33eeacc393d103063234e8bc28` |
| ollama | 0.35.1 |
| llama.cpp commit | `d7a695ef679138c13d86359b84c1731d36213d32` (6 Oct 2026, CPU build) |
| Baseline GGUF (q8_0) | `models/gguf/qwen2.5-7b-instruct-base-q8_0.gguf`, 8,098,525,792 bytes, sha256 `7c7da62742855bfe42db0890b8b8ebb8fdb47a95f969d426d963fe641a7e520f` (untouched base, converted with the llama.cpp commit above via `convert_hf_to_gguf.py --outtype q8_0`) |
| Screening model (Step 2 only) | ollama `qwen2.5:7b-instruct-q8_0` (ID `2d9500c94841`) |
| Judge model | TODO |
