import os
import sys
import json
import time
import urllib.request

BACKEND_URL = os.environ.get("TEST_BACKEND_URL", os.environ.get("EXPO_PUBLIC_BACKEND_URL", "http://localhost:8000"))


def http_get(path: str):
	with urllib.request.urlopen(f"{BACKEND_URL}{path}") as response:
		return response.status, json.loads(response.read().decode())


def http_post(path: str, payload: dict):
	data = json.dumps(payload).encode("utf-8")
	req = urllib.request.Request(f"{BACKEND_URL}{path}", data=data, headers={"Content-Type": "application/json"})
	with urllib.request.urlopen(req) as response:
		return response.status, json.loads(response.read().decode())


def wait_for_backend(timeout_seconds: int = 20):
	start = time.time()
	while time.time() - start < timeout_seconds:
		try:
			status, body = http_get("/api/health")
			if status == 200 and isinstance(body, dict) and body.get("status") == "healthy":
				return True
		except Exception:
			time.sleep(0.5)
	return False


def main():
	print(f"Testing backend at {BACKEND_URL}")
	ok = wait_for_backend()
	if not ok:
		print("Backend healthcheck failed or timed out", file=sys.stderr)
		sys.exit(1)
	print("Healthcheck OK")

	# If we don't have an API key for LLM, skip heavy tests
	if not os.environ.get("OPENAI_API_KEY"):
		print("OPENAI_API_KEY not set; skipping API flow tests.")
		print("All basic tests passed.")
		return

	# create-plan
	status, body = http_post("/api/create-plan", {"prompt": "Plan study session about algebra"})
	assert status == 200, f"create-plan status {status}"
	assert "session_id" in body and "plan" in body, "create-plan response keys missing"
	session_id = body["session_id"]
	print("create-plan OK")

	# execute-step (background)
	status, body = http_post("/api/execute-step", {"session_id": session_id, "step_id": 1})
	assert status == 200, f"execute-step status {status}"
	print("execute-step OK")

	# teacher
	status, body = http_post("/api/teacher", {"query": "What is Pythagorean theorem?"})
	assert status == 200, f"teacher status {status}"
	print("teacher OK")

	print("All tests passed.")


if __name__ == "__main__":
	main() 