# دليل التدريب — autoresearch على AMD ROCm (WSL2)

> تاريخ الإنشاء: 2026-04-10
> المسار: WSL2 Ubuntu-22.04 → `/home/saleh/autoresearch`

---

## نظرة عامة

مشروع autoresearch هو نظام بحث ذاتي مبني على nanochat (Karpathy) يقوم بتدريب نموذج GPT صغير (~11.5M معامل) وتعديل المعاملات الفائقة تلقائياً لتحسين الأداء.

**العلاقة بين المشاريع:**
```
nanochat (karpathy)        ← المطبخ الكامل: tokenizer + pretraining + SFT + RL + Chat UI
     └── autoresearch      ← طاهٍ ذكي: يغيّر الوصفة كل 5 دقائق ويقيس النتيجة
```

---

## العتاد والبرمجيات

| المكوّن | القيمة |
|---------|--------|
| GPU | AMD Radeon 8060S |
| Driver Framework | AMD ROCm 6.3 |
| WSL2 DXG | librocdxg (مبني من المصدر) |
| PyTorch | 2.9.0+rocm6.3 |
| OS | WSL2 Ubuntu-22.04 |
| Python | عبر `uv` (مدير حزم سريع) |

### متغيرات البيئة المطلوبة

```bash
export HSA_ENABLE_DXG_DETECTION=1
export HSA_ENABLE_SDMA=0
export HSA_OVERRIDE_GFX_VERSION=11.0.0
export LD_LIBRARY_PATH=/opt/rocm/lib
export TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1
```

---

## بنية النموذج

```python
# GPT Architecture (~11.5M params at DEPTH=4)
MAX_SEQ_LEN = 128
n_layer = 4          # عدد طبقات Transformer (DEPTH)
n_embd = 256         # حجم التضمين
batch_size = 1
dtype = "float16"
```

| DEPTH | المعاملات | VRAM | val_bpb |
|-------|----------|------|---------|
| 4 | 11.5M | 240 MB | 3.227 |
| 6 | 26.3M | 547 MB | 3.130 |
| 8 | - | - | قيد التجربة |

---

## نظام النقاط التفتيشية (Checkpoints)

تمت إضافة منظومة حفظ تلقائي في `train_cpu.py`:

- **حفظ دوري**: كل 1000 خطوة → `checkpoints/step_{N}.pt`
- **حفظ نهائي**: عند اكتمال التدريب → `checkpoints/final.pt`
- **المسار**: `/home/saleh/autoresearch/checkpoints/`

```python
CHECKPOINT_DIR = "checkpoints"
SAVE_EVERY = 1000  # حفظ كل 1000 خطوة

# يحفظ: model state_dict, optimizer state_dict, step, loss, config
```

---

## التدريب المطوّل — النتائج

| المقياس | القيمة |
|---------|--------|
| المدة | ~10 ساعات |
| الخطوات | 183,559 |
| الحقب | 30 |
| loss (بداية) | 9.01 |
| loss (نهاية) | 3.25 |
| DEPTH | 4 |

---

## sanirejal API — إدارة التدريب عن بُعد

خدمة REST على المنفذ **8500** في WSL2 لإدارة ومراقبة التدريب.

### نقاط النهاية

| Method | Endpoint | الوصف |
|--------|----------|-------|
| GET | `/health` | فحص حالة الخدمة |
| GET | `/status` | حالة التدريب (running/stopped، الخطوة، loss) |
| GET | `/logs` | آخر سطور سجل التدريب |
| GET | `/loss_history` | سجل تاريخ قيم الخسارة |
| GET | `/gpu` | معلومات GPU |
| GET | `/config` | المعاملات الفائقة الحالية |
| POST | `/train/start` | بدء جلسة تدريب |
| POST | `/train/stop` | إيقاف التدريب |

### التكامل مع Open WebUI

- مسجّلة كأداة (Tool) مرتبطة بنموذج **Evo2**
- يستطيع Evo2 استدعاء sanirejal API مباشرة من المحادثة

---

## أوامر التشغيل

```bash
# تشغيل التدريب
cd ~/autoresearch
HSA_ENABLE_DXG_DETECTION=1 HSA_ENABLE_SDMA=0 \
HSA_OVERRIDE_GFX_VERSION=11.0.0 \
TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1 \
uv run train_cpu.py

# تشغيل sanirejal API
cd ~/researchai
python sanirejal_api.py

# فحص حالة التدريب
curl http://localhost:8500/status

# فحص GPU
curl http://localhost:8500/gpu
```

---

## خارطة المراحل

| المرحلة | الأداة | الحالة | الناتج |
|---------|--------|--------|--------|
| 1. Pretraining | autoresearch | ✅ منجز | نموذج يفهم اللغة |
| 2. SFT (Fine-tuning) | nanochat `chat_sft.py` | 📋 مخطط | نموذج يجاوب أسئلة |
| 3. RL / GRPO | nanochat `chat_rl.py` | 📋 مستقبلي | نموذج يتبع تعليمات |
| 4. Chat Web UI | nanochat `chat_web.py` | 📋 جاهز | واجهة ChatGPT كاملة |
