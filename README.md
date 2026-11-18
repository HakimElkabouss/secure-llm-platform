# Secure LLM Platform

A self-hosted Large Language Model (LLM), protected by a security gateway.
Built step by step to practice **DevSecOps**, **AI security** and **Kubernetes**.

## Why this project?

Tools like [Ollama](https://ollama.com) make it easy to run an LLM on your own machine.
But Ollama has **no authentication**: anyone who can reach it can use your GPU,
delete models, or install a modified one.

This project puts a **gateway** in front of the model. Every request must go
through it, and the gateway applies security controls before anything reaches the LLM.

```
Client ──(API key)──▶ Gateway ──▶ Ollama (LLM on GPU)
                         │
                         └──▶ Security logs (SIEM)
```

The risks and the controls are described in the [threat model](docs/threat-model.md).

## Roadmap

- [x] Run an LLM locally on GPU (Ollama + NVIDIA Container Toolkit)
- [x] Threat model (risks R1–R9, controls M1–M7)
- [x] Gateway with a single allowed route (M3)
- [x] API key authentication, fail-closed (M2)
- [ ] Rate limiting and prompt size limit (M4)
- [ ] Secret and personal data redaction (M5)
- [ ] Prompt injection detection (M6)
- [ ] Security logs in JSON for a SIEM (M7)
- [ ] Unit tests
- [ ] Docker image and Docker Compose
- [ ] CI/CD pipeline with security scans (GitHub Actions)
- [ ] Kubernetes deployment with network isolation (M1)
- [ ] Monitoring (Prometheus, Grafana) and detection rules

## Quick start

Requirements: Docker, Python 3.12, an NVIDIA GPU (optional, CPU works but is slower).

```bash
# 1. Start Ollama (only reachable from this machine)
docker run -d --name ollama --gpus=all -p 127.0.0.1:11434:11434 \
  -v ollama-data:/root/.ollama ollama/ollama
docker exec ollama ollama pull qwen2.5:1.5b

# 2. Start the gateway
cd gateway
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "API_KEYS=$(openssl rand -hex 32)" > .env
uvicorn main:app --port 8080 --env-file .env

# 3. Ask a question
KEY=$(grep API_KEYS .env | cut -d= -f2)
curl http://localhost:8080/v1/chat \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"question": "What is Kubernetes?"}'
```

## Author

Hakim El Kabouss