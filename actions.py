import subprocess


def server_status():
    memory = subprocess.run(
        ["free", "-h"],
        capture_output=True,
        text=True
    ).stdout

    disk = subprocess.run(
        ["df", "-h", "/"],
        capture_output=True,
        text=True
    ).stdout

    uptime = subprocess.run(
        ["uptime"],
        capture_output=True,
        text=True
    ).stdout

    return f"""
=== MEMORY ===
{memory}

=== DISK ===
{disk}

=== UPTIME ===
{uptime}
"""
