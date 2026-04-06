"""
title: ComfyUI Image & Video Generator
author: Saleh Custom
version: 1.0
description: توليد صور وفيديو باستخدام ComfyUI على AMD GPU محلياً
"""

import json
import uuid
import time
import base64
import requests
from typing import Optional


class Tools:
    def __init__(self):
        self.comfyui_url = "http://host.docker.internal:8188"
        self.output_dir = "C:/ComfyUI_windows/ComfyUI/output"

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "ugly, blurry, low quality, deformed",
        width: int = 768,
        height: int = 768,
        steps: int = 28,
        cfg: float = 7.0,
        model_name: str = "dreamshaper_8.safetensors",
    ) -> str:
        """
        يولد صورة من نص باستخدام ComfyUI على AMD GPU محلياً.
        استخدم هذه الأداة عندما يطلب المستخدم توليد صورة أو رسم شيء.
        :param prompt: وصف الصورة بالإنجليزية (أو ترجمها تلقائياً)
        :param negative_prompt: ما لا تريده في الصورة
        :param width: عرض الصورة (افتراضي 512)
        :param height: ارتفاع الصورة (افتراضي 512)
        :param steps: عدد خطوات التوليد (افتراضي 20)
        :param cfg: قوة الالتزام بالنص (افتراضي 7.0)
        :return: رابط الصورة أو رسالة النتيجة
        """
        try:
            # بناء workflow بسيط text-to-image
            client_id = str(uuid.uuid4())
            seed = int(time.time()) % 2147483647

            workflow = {
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "seed": seed,
                        "steps": steps,
                        "cfg": cfg,
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "denoise": 1.0,
                        "model": ["4", 0],
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "latent_image": ["5", 0],
                    },
                },
                "4": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {"ckpt_name": model_name},
                },
                "5": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {"width": width, "height": height, "batch_size": 1},
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "text": prompt,
                        "clip": ["4", 1],
                    },
                },
                "7": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "text": negative_prompt,
                        "clip": ["4", 1],
                    },
                },
                "8": {
                    "class_type": "VAEDecode",
                    "inputs": {
                        "samples": ["3", 0],
                        "vae": ["4", 2],
                    },
                },
                "9": {
                    "class_type": "SaveImage",
                    "inputs": {
                        "filename_prefix": "saleh_gen",
                        "images": ["8", 0],
                    },
                },
            }

            # إرسال الطلب
            payload = {"prompt": workflow, "client_id": client_id}
            resp = requests.post(
                f"{self.comfyui_url}/prompt",
                json=payload,
                timeout=10,
            )
            resp.raise_for_status()
            prompt_id = resp.json()["prompt_id"]

            # انتظار اكتمال التوليد (max 3 دقائق)
            for _ in range(180):
                time.sleep(1)
                history_resp = requests.get(
                    f"{self.comfyui_url}/history/{prompt_id}", timeout=5
                )
                history = history_resp.json()
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    for node_id, node_output in outputs.items():
                        if "images" in node_output:
                            img = node_output["images"][0]
                            filename = img["filename"]
                            subfolder = img.get("subfolder", "")
                            img_url = f"{self.comfyui_url}/view?filename={filename}&subfolder={subfolder}&type=output"
                            return (
                                f"✅ تم توليد الصورة بنجاح!\n\n"
                                f"**الوصف:** {prompt}\n"
                                f"**الأبعاد:** {width}×{height}\n"
                                f"**الخطوات:** {steps}\n\n"
                                f"🖼️ الصورة: {img_url}\n\n"
                                f"يمكنك فتحها على: http://127.0.0.1:8188/view?filename={filename}&type=output"
                            )
                    return f"❌ لم يتم العثور على صورة في المخرجات."

            return "⏱️ انتهت مهلة الانتظار (3 دقائق). ComfyUI ما زال يعمل، جرب لاحقاً."

        except requests.exceptions.ConnectionError:
            return (
                "❌ ComfyUI غير متاح.\n"
                "تأكد أن ComfyUI يعمل على http://127.0.0.1:8188\n"
                "شغّله بـ: C:\\ComfyUI_windows\\run_amd_gpu.bat"
            )
        except Exception as e:
            return f"❌ خطأ: {str(e)}"

    def get_image_as_base64(self, filename: str, subfolder: str = "", image_type: str = "output") -> str:
        """
        جلب صورة من ComfyUI وتحويلها إلى base64 للعرض المباشر في المحادثة.
        :param filename: اسم ملف الصورة
        :param subfolder: مجلد الصورة (اختياري)
        :param image_type: نوع الصورة (output أو input أو temp)
        :return: الصورة بصيغة base64
        """
        try:
            # جلب الصورة من ComfyUI
            img_url = f"{self.comfyui_url}/view?filename={filename}&subfolder={subfolder}&type={image_type}"
            response = requests.get(img_url, timeout=10)
            response.raise_for_status()
            
            # تحويل الصورة إلى base64
            image_data = response.content
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            return f"data:image/png;base64,{base64_image}"
        except Exception as e:
            return f"❌ خطأ في جلب الصورة: {str(e)}"

    def comfyui_status(self) -> str:
        """
        يتحقق من حالة ComfyUI ويعرض معلومات GPU والموديلات المتاحة.
        استخدم هذه الأداة إذا سأل المستخدم عن حالة نظام توليد الصور.
        :return: معلومات النظام
        """
        try:
            stats = requests.get(f"{self.comfyui_url}/system_stats", timeout=5).json()
            models = requests.get(f"{self.comfyui_url}/object_info/CheckpointLoaderSimple", timeout=5).json()

            gpu_name = "غير معروف"
            vram_total = 0
            vram_free = 0
            if stats.get("devices"):
                dev = stats["devices"][0]
                gpu_name = dev.get("name", "غير معروف")
                vram_total = round(dev.get("vram_total", 0) / 1024**3, 1)
                vram_free = round(dev.get("vram_free", 0) / 1024**3, 1)

            available_models = []
            try:
                ckpts = models["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
                available_models = ckpts
            except Exception:
                pass

            models_str = "\n".join(f"  - {m}" for m in available_models) if available_models else "  لا يوجد موديل"

            return (
                f"✅ ComfyUI يعمل — v{stats['system'].get('comfyui_version', '?')}\n\n"
                f"**GPU:** {gpu_name}\n"
                f"**VRAM:** {vram_free}GB متاح / {vram_total}GB إجمالي\n\n"
                f"**الموديلات المتاحة:**\n{models_str}"
            )
        except requests.exceptions.ConnectionError:
            return "❌ ComfyUI غير متاح حالياً. شغّله من: C:\\ComfyUI_windows\\run_amd_gpu.bat"
        except Exception as e:
            return f"❌ خطأ: {str(e)}"
