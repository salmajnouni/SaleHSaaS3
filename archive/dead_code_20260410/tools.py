"""
title: Computer Use Tools Fixed
author: Saleh + Grok Fix
version: 2.4.1
license: MIT
description: Bash & file tools in Docker - Fixed socket for Windows (no internal imports)
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import docker
import logging

log = logging.getLogger(__name__)

class Valves(BaseModel):
    docker_socket: str = Field(
        default="//./pipe/dockerDesktopLinuxEngine",
        description="Docker socket path - Windows fixed (try //./pipe/docker_engine if fails)"
    )

valves = Valves()

class Tools:
    def __init__(self):
        self.valves = valves
        self.client = None
        self._connect_to_docker()

    def _connect_to_docker(self):
        try:
            self.client = docker.DockerClient(base_url=self.valves.docker_socket)
            log.info("Docker client connected successfully!")
        except Exception as e:
            log.error(f"Connection failed: {str(e)}")
            self._retry_connection()

    def _retry_connection(self):
        alternative_sockets = [
            "//./pipe/docker_engine",
            "//./pipe/dockerDesktopLinuxEngine"
        ]
        for socket in alternative_sockets:
            try:
                self.client = docker.DockerClient(base_url=socket)
                log.info(f"Docker client connected successfully using socket: {socket}")
                return
            except Exception as e:
                log.error(f"Connection failed with socket {socket}: {str(e)}")
        self.client = None

    async def inlet(self, body: Dict[str, Any], user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return body

    async def run_bash(self, command: str) -> str:
        if not self.client:
            return "Error: Docker client not initialized. Check socket path in Valves."
        try:
            containers = self.client.containers.list()
            if not containers:
                return "No running containers found."
            container = containers[0]
            result = container.exec_run(command)
            return result.output.decode()
        except Exception as e:
            return f"Bash error: {str(e)}"

    async def create_file(self, path: str, content: str) -> str:
        if not self.client:
            return "Error: Docker client not initialized. Check socket path in Valves."
        try:
            containers = self.client.containers.list()
            if not containers:
                return "No running containers found."
            container = containers[0]
            import tarfile, io
            data = content.encode('utf-8')
            tar_stream = io.BytesIO()
            info = tarfile.TarInfo(name=path.lstrip('/'))
            info.size = len(data)
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                tar.addfile(info, io.BytesIO(data))
            tar_stream.seek(0)
            container.put_archive('/', tar_stream)
            log.info(f"File {path} created inside container {container.name}")
            return f"File {path} created inside container {container.name}"
        except Exception as e:
            return f"Error creating file: {str(e)}"

    async def view_file(self, path: str) -> str:
        if not self.client:
            return "Error: Docker client not initialized. Check socket path in Valves."
        try:
            containers = self.client.containers.list()
            if not containers:
                return "No running containers found."
            container = containers[0]
            result = container.exec_run(["cat", "--", path])
            return result.output.decode()
        except Exception as e:
            return f"Error viewing file: {str(e)}"

# تجربة الاتصال يدويًا
def test_docker_connection():
    tools = Tools()
    if tools.client:
        print("Docker client connected successfully!")
    else:
        print("Failed to connect to Docker client.")

if __name__ == "__main__":
    test_docker_connection()