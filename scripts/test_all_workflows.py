"""Test all 5 webhook workflows one by one."""
import requests
import json
import time
import sys

base = 'http://localhost:5678'

def test_workflow(name, webhook, payload, timeout_sec=120, extract_fn=None):
    print(f'\n{"="*60}')
    print(f'Testing: {name}')
    print(f'Webhook: {webhook}')
    print(f'Payload: {json.dumps(payload, ensure_ascii=False)[:100]}')
    print('-'*60)
    
    start = time.time()
    try:
        r = requests.post(base + webhook, json=payload, timeout=timeout_sec)
        elapsed = time.time() - start
        print(f'Status: {r.status_code} | Time: {elapsed:.0f}s')
        
        if r.status_code != 200:
            print(f'ERROR: {r.text[:300]}')
            return False
        
        d = r.json()
        
        if extract_fn:
            extract_fn(d)
        else:
            print(json.dumps(d, ensure_ascii=False, indent=2)[:500])
        
        return True
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f'TIMEOUT after {elapsed:.0f}s')
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f'ERROR after {elapsed:.0f}s: {e}')
        return False

# ============================================================
# Which test to run
# ============================================================
test_num = int(sys.argv[1]) if len(sys.argv) > 1 else 0

results = {}

# 1. Error Hunter (~30s)
if test_num in (0, 1):
    def extract_error_hunter(d):
        report = d.get('report', '')
        print(f'Report preview: {report[:300]}')
        print(f'RunId: {d.get("runId", "")}')
        print(f'Refs: {d.get("refs", 0)}')
        print(f'Status: {d.get("status", "")}')
        if report:
            print('\n>>> PASS')
        else:
            print('\n>>> FAIL - no report')
    
    ok = test_workflow(
        'صائد الأخطاء (Error Hunter)',
        '/webhook/error-hunt-v2',
        {'error': 'ConnectionRefusedError: [Errno 111] Connection refused - ChromaDB not responding'},
        timeout_sec=120,
        extract_fn=extract_error_hunter
    )
    results['error_hunter'] = ok

# 2. Legal Chat (~1-2 min)
if test_num in (0, 2):
    def extract_legal_chat(d):
        output = d.get('output', '')
        print(f'Output preview: {output[:400]}')
        if output:
            print('\n>>> PASS')
        else:
            print(f'\n>>> FAIL - no output. Full response keys: {list(d.keys())}')
    
    ok = test_workflow(
        'مساعد القوانين السعودية (Legal Chat)',
        '/webhook/saleh-legal-chat-001',
        {'question': 'ما هي شروط تأسيس شركة ذات مسؤولية محدودة في نظام الشركات السعودي؟'},
        timeout_sec=300,
        extract_fn=extract_legal_chat
    )
    results['legal_chat'] = ok

# 3. Innovation Council (~15-20 min)
if test_num in (0, 3):
    def extract_council(d):
        decision = d.get('decision', '')
        session_id = d.get('sessionId', '')
        sources = d.get('sources', {})
        web = sources.get('web', 0)
        rag = sources.get('rag', 0)
        status = d.get('status', '')
        print(f'Session: {session_id}')
        print(f'Status: {status}')
        print(f'Sources: web={web}, rag={rag}')
        print(f'Decision preview: {decision[:500]}')
        if decision:
            print('\n>>> PASS')
        else:
            print('\n>>> FAIL - no decision')
    
    ok = test_workflow(
        'مجلس الابتكار (Innovation Council)',
        '/webhook/council-innovation',
        {'question': 'هل نضيف خاصية توصيات ذكية للعملاء؟'},
        timeout_sec=1800,
        extract_fn=extract_council
    )
    results['innovation'] = ok

# 4. Tech Governance Council (~15-20 min)
if test_num in (0, 4):
    def extract_council_tg(d):
        decision = d.get('decision', '')
        session_id = d.get('sessionId', '')
        sources = d.get('sources', {})
        print(f'Session: {session_id}')
        print(f'Sources: web={sources.get("web",0)}, rag={sources.get("rag",0)}')
        print(f'Decision preview: {decision[:500]}')
        if decision:
            print('\n>>> PASS')
        else:
            print('\n>>> FAIL - no decision')
    
    ok = test_workflow(
        'مجلس الحوكمة التقنية (Tech Governance)',
        '/webhook/council-tech-governance',
        {'question': 'هل نستخدم PostgreSQL أو MongoDB للمنصة؟'},
        timeout_sec=1800,
        extract_fn=extract_council_tg
    )
    results['tech_governance'] = ok

# 5. Legal Review Council (~15-20 min)
if test_num in (0, 5):
    def extract_council_lr(d):
        decision = d.get('decision', '')
        session_id = d.get('sessionId', '')
        sources = d.get('sources', {})
        print(f'Session: {session_id}')
        print(f'Sources: web={sources.get("web",0)}, rag={sources.get("rag",0)}')
        print(f'Decision preview: {decision[:500]}')
        if decision:
            print('\n>>> PASS')
        else:
            print('\n>>> FAIL - no decision')
    
    ok = test_workflow(
        'مجلس المراجعة القانونية (Legal Review)',
        '/webhook/council-legal-review',
        {'question': 'هل شروط الاستخدام الحالية متوافقة مع نظام حماية البيانات الشخصية؟'},
        timeout_sec=1800,
        extract_fn=extract_council_lr
    )
    results['legal_review'] = ok

# ============================================================
# Summary
# ============================================================
if results:
    print(f'\n{"="*60}')
    print('SUMMARY')
    print('='*60)
    for name, ok in results.items():
        status = 'PASS' if ok else 'FAIL'
        print(f'  {name}: {status}')
