"""A fresh Codex app-server session with no host environments and one dynamic tool.

The authenticated transport can contact the model service. The model has no network,
filesystem, shell, plugin or connector capability. Credentials are symlinked into a
throwaway CODEX_HOME; personal configuration, memories and skills are not imported.
"""
import json
import os
from pathlib import Path
import queue
import subprocess
import tempfile
import threading
import time
from ....benchmarking.tools.sqlite_tool import TOOL_SPEC as TOOL

DISABLED_FEATURES = [
    "apps", "plugins", "shell_tool", "unified_exec", "browser_use", "browser_use_external",
    "computer_use", "image_generation", "view_image", "multi_agent", "memories", "goals",
    "hooks", "skill_search", "workspace_dependencies", "code_mode",
    "in_app_browser", "tool_suggest",
]


class CodexSession:
    def __init__(self, config, log):
        self.config = config
        self.log = log
        self.sequence = 0
        self.events = queue.Queue()
        self.process = None
        self.temporary = None
        self.stderr = None
        self.deadline = time.monotonic() + config["timeout_seconds"]
        self.usage = None
        self.resolved_model = None
        self.runtime_config = None
        self.version = subprocess.check_output(["codex", "--version"], text=True).strip()

    def __enter__(self):
        auth_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        auth = auth_home / "auth.json"
        if not auth.is_file():
            raise RuntimeError("Codex file authentication is required; run codex login first")
        self.temporary = tempfile.TemporaryDirectory(prefix="owid-vdem-sqlagent-")
        home = Path(self.temporary.name)
        (home / "auth.json").symlink_to(auth.resolve())
        config_text = 'web_search = "disabled"\nproject_doc_max_bytes = 0\n[features]\n'
        config_text += "\n".join(f"{name} = false" for name in DISABLED_FEATURES)
        config_text += '\nskip_host_skill_discovery = true\n'
        config_text += '''
[tools.update_plan]
enabled = false
[tools.experimental_request_user_input]
enabled = false
[orchestrator.skills]
enabled = false
[orchestrator.mcp]
enabled = false
[skills]
include_instructions = false
[skills.bundled]
enabled = false
'''
        self.runtime_config = config_text
        (home / "config.toml").write_text(config_text)
        env = {key: value for key, value in os.environ.items() if key in {
            "PATH", "HOME", "TMPDIR", "LANG", "SSL_CERT_FILE", "SSL_CERT_DIR",
            "HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "NO_PROXY"}}
        env["CODEX_HOME"] = str(home)
        self.stderr = tempfile.TemporaryFile(mode="w+")
        try:
            self.process = subprocess.Popen(["codex", "app-server"], cwd=home, env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr, text=True)
            threading.Thread(target=self._read, daemon=True).start()
            self.request("initialize", {"clientInfo": {"name": "owid-vdem-data-task", "version": "0.1.0"},
                                        "capabilities": {"experimentalApi": True}})
            self.send({"method": "initialized", "params": {}})
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def _read(self):
        for line in self.process.stdout:
            try:
                self.events.put(json.loads(line))
            except json.JSONDecodeError:
                self.events.put({"transport_error": "Invalid app-server JSON"})
        self.events.put({"transport_error": "Codex app-server exited"})

    def send(self, message):
        self.log("client", message)
        self.process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        self.process.stdin.flush()

    def receive(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Agent run deadline exceeded")
        try:
            message = self.events.get(timeout=remaining)
        except queue.Empty as exc:
            raise TimeoutError("Agent run deadline exceeded") from exc
        self.log("server", message)
        if "transport_error" in message:
            raise RuntimeError(message["transport_error"])
        return message

    def request(self, method, params):
        self.sequence += 1
        request_id = self.sequence
        self.send({"id": request_id, "method": method, "params": params})
        while True:
            message = self.receive()
            if message.get("id") == request_id and "method" not in message:
                if "error" in message:
                    raise RuntimeError(str(message["error"]))
                return message["result"]
            if "id" in message and "method" in message:
                raise RuntimeError(f"Unexpected server request during {method}: {message['method']}")

    def run(self, instructions, user_input, on_query, images=()):
        """`images`: data URLs (data:image/png;base64,...) attached to the user message after the text."""
        result = self.request("thread/start", {
            "model": self.config["model"], "allowProviderModelFallback": False,
            "ephemeral": True, "environments": [], "runtimeWorkspaceRoots": [],
            "selectedCapabilityRoots": [], "baseInstructions": instructions,
            "approvalPolicy": "never", "dynamicTools": [TOOL],
            "experimentalRawEvents": True,
        })
        self.resolved_model = result["model"]
        if self.resolved_model != self.config["model"]:
            raise RuntimeError("Server changed the requested model")
        thread_id = result["thread"]["id"]
        self.request("turn/start", {"threadId": thread_id,
            "environments": [], "effort": self.config["reasoning_effort"],
            "input": [{"type": "text", "text": user_input, "text_elements": []},
                      *[{"type": "image", "url": url, "detail": "high"} for url in images]]})
        final = None
        while True:
            message = self.receive()
            method = message.get("method")
            params = message.get("params", {})
            if method == "item/tool/call":
                if params["tool"] != "sqlite_query":
                    raise RuntimeError(f"Unexpected tool: {params['tool']}")
                output = on_query(params["arguments"])
                self.send({"id": message["id"], "result": {
                    "contentItems": [{"type": "inputText", "text": json.dumps(output, ensure_ascii=False)}],
                    "success": "error" not in output}})
            elif "id" in message and method:
                raise RuntimeError(f"Unexpected server capability request: {method}")
            elif method == "item/completed":
                item = params["item"]
                if item["type"] == "agentMessage":
                    final = item["text"]
                elif item["type"] in {"commandExecution", "fileChange", "webSearch", "mcpToolCall"}:
                    raise RuntimeError(f"Isolation violation: {item['type']}")
            elif method == "thread/tokenUsage/updated":
                self.usage = params["tokenUsage"]
            elif method == "turn/completed":
                turn = params["turn"]
                if turn["status"] != "completed":
                    raise RuntimeError(f"Model turn ended: {turn}")
                if final is None:
                    raise RuntimeError("Model did not return a final response")
                return final

    def __exit__(self, *_):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process.stdin.close()
            self.process.stdout.close()
        if self.stderr:
            self.stderr.close()
        if self.temporary:
            self.temporary.cleanup()
