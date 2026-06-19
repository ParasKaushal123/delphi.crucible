import asyncio
import json
from state.session_store import SessionStore

async def run():
    store = SessionStore()
    await store.connect()
    data = await store._redis.get('user_profile:demo_user')
    if data:
        p = json.loads(data)
        if 'MOCK' in p.get('portfolio', {}):
            print('MOCK threshold before:', p['portfolio']['MOCK'].get('threshold'))
            p['portfolio']['MOCK']['threshold'] = '10.00'
            await store._redis.set('user_profile:demo_user', json.dumps(p))
            print('MOCK threshold updated to 10.00')
        else:
            print('MOCK not in portfolio')
    else:
        print('User profile not found')
        
if __name__ == '__main__':
    asyncio.run(run())
