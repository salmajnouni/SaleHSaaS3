
import sys
import json
import requests
from typing import Dict, Any, List

# عنوان Ollama API - يتم الوصول إليه من داخل حاوية Docker
OLLAMA_API_URL = "http://host.docker.internal:11434/api"

def send_response(response: Dict[str, Any]):
    """إرسال استجابة JSON إلى stdout"""
    print(json.dumps(response), flush=True)

def get_tools():
    """تعريف الأدوات التي توفرها هذه الخدمة"""
    return {
        "type": "get_tools_response",
        "tools": [
            {
                "name": "list_local_models",
                "description": "الحصول على قائمة بجميع النماذج المحلية المتاحة في Ollama.",
                "input_schema": {"type": "object", "properties": {}},
            },
            {
                "name": "get_model_info",
                "description": "الحصول على معلومات تفصيلية حول نموذج معين.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "model_name": {"type": "string", "description": "اسم النموذج (e.g., 'llama3.1')"}
                    },
                    "required": ["model_name"],
                },
            },
            {
                "name": "pull_model",
                "description": "تحميل نموذج جديد من Ollama Hub.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "model_name": {"type": "string", "description": "اسم النموذج المراد تحميله (e.g., 'mistral')"}
                    },
                    "required": ["model_name"],
                },
            },
        ],
    }

def list_local_models(invocation_id: str):
    """استدعاء Ollama API للحصول على قائمة النماذج"""
    try:
        response = requests.get(f"{OLLAMA_API_URL}/tags")
        response.raise_for_status()
        models = response.json().get("models", [])
        # تنسيق المخرجات لتكون أكثر قابلية للقراءة
        formatted_models = [f"{m['name']} (Size: {m['size']/(1024**3):.2f} GB, Modified: {m['modified_at']})" for m in models]
        send_response({
            "type": "invoke_tool_response",
            "invocation_id": invocation_id,
            "tool_name": "list_local_models",
            "output": json.dumps(formatted_models, indent=2, ensure_ascii=False),
            "is_last": True,
        })
    except requests.RequestException as e:
        send_response({
            "type": "error",
            "invocation_id": invocation_id,
            "error": f"Failed to connect to Ollama: {e}",
        })

def get_model_info(invocation_id: str, inputs: Dict[str, Any]):
    """الحصول على معلومات تفصيلية لنموذج معين"""
    model_name = inputs.get("model_name")
    if not model_name:
        send_response({"type": "error", "invocation_id": invocation_id, "error": "Missing model_name"})
        return

    try:
        response = requests.post(f"{OLLAMA_API_URL}/show", json={"name": model_name})
        response.raise_for_status()
        send_response({
            "type": "invoke_tool_response",
            "invocation_id": invocation_id,
            "tool_name": "get_model_info",
            "output": json.dumps(response.json(), indent=2, ensure_ascii=False),
            "is_last": True,
        })
    except requests.RequestException as e:
        send_response({
            "type": "error",
            "invocation_id": invocation_id,
            "error": f"Failed to get info for model {model_name}: {e}",
        })

def pull_model(invocation_id: str, inputs: Dict[str, Any]):
    """تحميل نموذج من Ollama Hub"""
    model_name = inputs.get("model_name")
    if not model_name:
        send_response({"type": "error", "invocation_id": invocation_id, "error": "Missing model_name"})
        return

    try:
        # إرسال استجابة أولية بأن العملية بدأت
        send_response({
            "type": "invoke_tool_response",
            "invocation_id": invocation_id,
            "tool_name": "pull_model",
            "output": f"بدء تحميل النموذج {model_name}... هذه العملية قد تستغرق بعض الوقت.",
            "is_last": False, # المزيد من المخرجات قادمة
        })
        
        # استدعاء API مع stream=True
        with requests.post(f"{OLLAMA_API_URL}/pull", json={"name": model_name, "stream": True}, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    progress = json.loads(line)
                    if "total" in progress and "completed" in progress:
                        percentage = (progress["completed"] / progress["total"]) * 100
                        status = f"{progress['status']} - {percentage:.1f}%"
                    else:
                        status = progress.get('status', 'loading...')
                    
                    # إرسال تحديثات الحالة
                    send_response({
                        "type": "invoke_tool_response",
                        "invocation_id": invocation_id,
                        "tool_name": "pull_model",
                        "output": status,
                        "is_last": False,
                    })

        # إرسال رسالة الإكمال النهائية
        send_response({
            "type": "invoke_tool_response",
            "invocation_id": invocation_id,
            "tool_name": "pull_model",
            "output": f"اكتمل تحميل النموذج {model_name} بنجاح.",
            "is_last": True,
        })

    except requests.RequestException as e:
        send_response({
            "type": "error",
            "invocation_id": invocation_id,
            "error": f"Failed to pull model {model_name}: {e}",
        })

def main():
    """الحلقة الرئيسية لقراءة الطلبات من stdin"""
    for line in sys.stdin:
        try:
            request = json.loads(line)
            request_type = request.get("type")

            if request_type == "get_tools_request":
                send_response(get_tools())
            elif request_type == "invoke_tool_request":
                tool_name = request.get("tool_name")
                invocation_id = request.get("invocation_id")
                inputs = request.get("inputs", {})

                if tool_name == "list_local_models":
                    list_local_models(invocation_id)
                elif tool_name == "get_model_info":
                    get_model_info(invocation_id, inputs)
                elif tool_name == "pull_model":
                    pull_model(invocation_id, inputs)
                else:
                    send_response({"type": "error", "invocation_id": invocation_id, "error": f"Unknown tool: {tool_name}"})
        except json.JSONDecodeError:
            send_response({"type": "error", "error": "Invalid JSON input"})
        except Exception as e:
            send_response({"type": "error", "error": str(e)})

if __name__ == "__main__":
    main()
