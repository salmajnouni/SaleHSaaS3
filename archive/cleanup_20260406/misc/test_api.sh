#!/bin/sh
curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer sk-773169e4bcce483fb5e8268e9bf393dc" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5:7b","messages":[{"role":"user","content":"test"}],"stream":false,"max_tokens":5}' \
  "http://localhost:8080/api/chat/completions"
