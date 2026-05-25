job "jarvis-home-server" {
  datacenters = ["dc1"]
  type = "service"

  group "jarvis" {
    count = 1

    network {
      mode = "bridge"

      port "http" {
        static = 8000
      }
    }

    task "jarvis-api" {
      driver = "docker"

      config {
        image = "python:3.12-slim"

        command = "bash"

        args = [
          "-lc",
          <<EOF
cd /app && \
python -m pip install --no-cache-dir -r requirements.txt && \
python -m uvicorn app:app --host 0.0.0.0 --port 8000
EOF
        ]

        ports = ["http"]

        volumes = [
          "/home/gabz-admin/apis/jarvis/jarvis-home-server:/app"
        ]
      }

      env {
        PIP_NO_CACHE_DIR = "1"
        PYTHONUNBUFFERED = "1"
        OLLAMA_URL = "http://192.168.0.211:11434/api/generate"
      }

      resources {
        cpu    = 500
        memory = 512
      }

      restart {
        attempts = 5
        interval = "30m"
        delay    = "15s"
        mode     = "delay"
      }
    }
  }
}