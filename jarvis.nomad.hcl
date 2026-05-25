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
          "cd /app && python -m pip install --no-cache-dir -r requirements.txt && uvicorn app:app --host 0.0.0.0 --port 8000"
        ]
        port_map {
          http = 8000
        }
      }

      env {
        PIP_NO_CACHE_DIR = "1"
      }

      volume_mount {
        volume      = "jarvis-code"
        destination = "/app"
        read_only   = false
      }

      resources {
        cpu      = 500
        memory   = 512
        network {
          mbits = 10
          port "http" {}
        }
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
    }
  }
}
