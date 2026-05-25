job "jarvis-home-server" {
  datacenters = ["dc1"]
  type = "service"

  group "jarvis" {
    count = 1

    volume "jarvis-code" {
      type      = "host"
      source    = "/home/gabz-admin/apis/jarvis/jarvis-home-server"
      read_only = false
    }

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
      }

      env {
        PIP_NO_CACHE_DIR = "1"
        PYTHONUNBUFFERED = "1"
      }

      volume_mount {
        volume      = "jarvis-code"
        destination = "/app"
        read_only   = false
      }

      resources {
        cpu    = 500
        memory = 512
      }

      service {
        name = "jarvis-home-server"
        port = "http"

        check {
          type     = "tcp"
          interval = "10s"
          timeout  = "2s"
        }
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