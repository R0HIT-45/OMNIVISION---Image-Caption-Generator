import requests, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = 'http://localhost:8001/api/v1/process-image'
images = ['test_images/heritage/heritage_3.jpg', 'test_images/heritage/heritage_5.jpg', 'test_images/heritage/heritage_8.jpg']

for img_path in images:
    with open(img_path, 'rb') as f:
        resp = requests.post(url, files={'file': (img_path.split('/')[-1], f, 'image/jpeg')}, timeout=600)
    d = resp.json()
    t = d['metadata']['processing_times']
    print(f"=== {img_path} ===")
    print(f"  Caption: {d['data']['raw_caption']}")
    print(f"  Hindi:   {d['data']['translations'].get('hindi','')}")
    print(f"  Telugu:  {d['data']['translations'].get('telugu','')}")
    print(f"  Times:   caption={t['caption_ms']:.0f}ms trans={t['translation_ms']:.0f}ms total={t['total_ms']:.0f}ms")
    print()
