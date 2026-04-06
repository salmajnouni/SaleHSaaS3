
import os

def filter_content(text):
    forbidden = ['نووي', 'بوتين', 'سلاح', 'تهديد']
    for word in forbidden:
        if word in text:
            return False, word
    return True, None

def check_current_inbox():
    inbox = '/app/knowledge_inbox'
    for f in os.listdir(inbox):
        with open(os.path.join(inbox, f), 'r', encoding='utf-8') as file:
            content = file.read()
            safe, word = filter_content(content)
            if not safe:
                print(f'[SECURITY] DELETING DANGEROUS CONTENT: {f} (Found: {word})')
                # os.remove(os.path.join(inbox, f)) # تفعيل الحذف عند التأكد

if __name__ == '__main__':
    check_current_inbox()
