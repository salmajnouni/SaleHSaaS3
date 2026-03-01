# SaleH SaaS - Local AI Brain 🧠

**SaleH Smart Autonomous Agent System** is a complete, 100% private, local-first AI ecosystem designed for knowledge management, intelligent search, and automated fine-tuning. It runs entirely on your local machine using Docker, ensuring no data ever leaves your device.

---

### 🕋 النسخة العربية

**SaleH SaaS (نظام العميل الذكي)** هو نظام ذكاء اصطناعي متكامل يعمل بالكامل على جهازك المحلي، مصمم لإدارة المعرفة، البحث الذكي، وأتمتة الضبط الدقيق (Fine-Tuning) للنماذج اللغوية. النظام يضمن خصوصية 100% حيث أن جميع بياناتك لا تغادر جهازك أبداً.

[![SaleH SaaS Dashboard](https://raw.githubusercontent.com/salmajnouni/SaleHSaaS3/main/docs/assets/dashboard_v2_ar.png)](#)

## ✨ الميزات الرئيسية

- **🧠 ذكاء اصطناعي محلي 100%**: يستخدم Ollama لتشغيل نماذج لغوية كبيرة (مثل Llama 3) ونماذج embeddings (مثل nomic-embed-text) مباشرة على جهازك.
- **📚 قاعدة معرفة متكاملة**: حوّل مستنداتك (PDF, Word, TXT, MD) إلى قاعدة معرفة قابلة للبحث باستخدام ChromaDB.
- **📂 مراقبة تلقائية للمجلدات**: ضع ملفاتك في مجلد `incoming` وسيقوم النظام بمعالجتها وتخزينها تلقائياً.
- **💬 واجهة محادثة ذكية (RAG)**: اسأل النموذج أسئلة بلغتك الطبيعية وسيجيب بناءً على محتوى مستنداتك المخزنة.
- **🤖 ضبط دقيق (LoRA)**: يجمع أمثلة التدريب تلقائياً في قائمة انتظار، وعند الوصول إلى 500 مثال، يمكن بدء عملية الضبط الدقيق (Fine-Tuning) لتعليم النموذج أسلوبك ومصطلحاتك الخاصة.
- **📊 لوحة مراقبة شاملة**: واجهة ويب احترافية لمراقبة حالة جميع الخدمات، عرض إحصاءات ChromaDB، تتبع الملفات، والبحث في قاعدة المعرفة.
- **🌐 مبني على Docker**: النظام بأكمله يعمل داخل حاويات Docker معزولة، مما يسهل عملية التثبيت والتشغيل والإدارة.

## 🚀 ابدأ الآن (Quick Start)

1.  **المتطلبات**: Docker Desktop, Git.
2.  **استنساخ المستودع**:
    ```bash
    git clone https://github.com/salmajnouni/SaleHSaaS3.git
    cd SaleHSaaS3
    ```
3.  **تشغيل النظام**:
    ```bash
    docker-compose up -d --build
    ```
4.  **افتح لوحة المراقبة**: **http://localhost:8000**
5.  **ابدأ بإضافة الملفات**: ضع مستنداتك في المجلد `D:\SaleHSaaS3\data\incoming`.

---

### English Version

[![SaleH SaaS Dashboard](https://raw.githubusercontent.com/salmajnouni/SaleHSaaS3/main/docs/assets/dashboard_v2_en.png)](#)

## ✨ Key Features

- **🧠 100% Local AI**: Utilizes Ollama to run large language models (like Llama 3) and embedding models (like nomic-embed-text) directly on your machine.
- **📚 Integrated Knowledge Base**: Transform your documents (PDF, Word, TXT, MD) into a searchable knowledge base using ChromaDB.
- **📂 Automated Folder Watching**: Simply drop your files into the `incoming` folder, and the system will automatically process and store them.
- **💬 Smart Chat Interface (RAG)**: Ask the model questions in your natural language, and it will answer based on the content of your stored documents.
- **🤖 Automated Fine-Tuning (LoRA)**: Automatically collects training examples in a queue. Once 500 examples are reached, you can initiate the fine-tuning process to teach the model your specific style and terminology.
- **📊 Comprehensive Dashboard**: A professional web interface to monitor the status of all services, view ChromaDB stats, track files, and search the knowledge base.
- **🌐 Docker-Powered**: The entire system runs inside isolated Docker containers, making installation, operation, and management seamless.

## 🚀 Quick Start

1.  **Prerequisites**: Docker Desktop, Git.
2.  **Clone the Repository**:
    ```bash
    git clone https://github.com/salmajnouni/SaleHSaaS3.git
    cd SaleHSaaS3
    ```
3.  **Run the System**:
    ```bash
    docker-compose up -d --build
    ```
4.  **Open the Dashboard**: Navigate to **http://localhost:8000**
5.  **Start Adding Files**: Place your documents in the `D:\SaleHSaaS3\data\incoming` directory.
