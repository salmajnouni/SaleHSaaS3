import os
import datetime

# إعدادات المسارات داخل الحاوية
INBOX_DIR = '/app/knowledge_inbox'
SCRIPTS_DIR = '/app/python_agent/scripts'

def fetch_tech_articles():
    print('[PRESIDENT] Searching for High-Value Tech Insights...')
    # هنا تم تحديد مصادر نظيفة (Clean Source) - أخبار التقنية الآمنة
    sample_article = {
        'title': 'The Rise of Autonomous AI Agents 2026',
        'content': 'Strategic analysis: Moving from simple chatbots to autonomous AI agents that can manage full SaaS operations.',
        'source': 'SaleH_President_Knowledge',
        'topic': 'Technology/AI'
    }
    return [sample_article]

def save_to_inbox(articles):
    if not os.path.exists(INBOX_DIR):
        os.makedirs(INBOX_DIR)
        
    for art in articles:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'PRESIDENT_READY_{timestamp}.txt'
        filepath = os.path.join(INBOX_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"TITLE: {art['title']}\n")
            f.write(f"SOURCE: {art['source']}\n")
            f.write(f"TOPIC: {art['topic']}\n")
            f.write("---CONTENT---\n")
            f.write(art['content'])
        
        print(f'[PRESIDENT_SUCCESS] Article Secured in Inbox: {filename}')

if __name__ == "__main__":
    articles = fetch_tech_articles()
    save_to_inbox(articles)
    print('[PRESIDENT_BOT] Professional Ingestion Cycle Finished.')
