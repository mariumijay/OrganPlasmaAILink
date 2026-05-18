import httpx, asyncio

async def test_match():
    url = 'http://127.0.0.1:8000/api/match/find'
    payload = {
        'hospital_id': 'Hospital Account',
        'required_organs': ['Kidney'],
        'patient_blood_type': 'O+',
        'patient_age': 45,
        'urgency_level': 'high',
        'donor_type': 'organ'
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, json=payload)
            print(f'Status: {r.status_code}')
            if r.status_code == 200:
                data = r.json()
                print(f"Found {len(data['matches'])} matches.")
                if data['matches']:
                    m = data['matches'][0]
                    print(f"Top Match: {m['name']} | Score: {m['ai_score']*100}%")
                    print(f"Explanation: {m['ai_explanation'][:100]}...")
            else:
                print(f'Error: {r.text}')
    except Exception as e:
        print(f'Request failed: {e}')

asyncio.run(test_match())
