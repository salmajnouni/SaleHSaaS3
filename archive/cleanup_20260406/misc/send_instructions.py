import urllib.request, json

token = '8631392889:AAF4jdcNrWWHsvXY_Y2pnY5C-7eJa0678Fg'
chat_id = '161458544'
text = (
    "مرحبا يا صالح! الرئيس جاهز الحين على بوت التلجرام\n\n"
    "كيف تتكلم مع الرئيس:\n"
    "- افتح البوت @SaleH3SaaSBoT\n"
    "- اكتب اي رسالة وبيرد عليك الرئيس مباشرة\n"
    "- مثال: اكتب \"ايش اخبار المشروع؟\" وبيرد عليك\n\n"
    "ملاحظات:\n"
    "- الرد ممكن ياخذ شوي وقت (10-60 ثانية) لان الموديل يفكر\n"
    "- بتشوف typing وهو يجهز الرد\n"
    "- ازرار المجلس الاستشاري تشتغل بعد على نفس البوت\n\n"
    "تصبح على خير!"
)

url = f'https://api.telegram.org/bot{token}/sendMessage'
data = json.dumps({'chat_id': chat_id, 'text': text}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req)
result = json.loads(resp.read().decode('utf-8'))
print('Sent!' if result['ok'] else 'Failed')
