import json
from django.core.management.base import BaseCommand
from django_redis import get_redis_connection


class Command(BaseCommand):
    help = "Subscribe to Redis channel 'comments' and print incoming messages."

    def handle(self, *args, **options):
        conn = get_redis_connection('default')
        pubsub = conn.pubsub()
        pubsub.subscribe('comments')

        for message in pubsub.listen():
            if message.get('type') != 'message':
                continue

            data = message.get("data")
            # пришли биты
            if isinstance(data, (bytes, bytearray)):
                data = data.decode('utf-8')

            try:
                obj = json.loads(data)
                self.stdout.write(json.dumps(obj, ensure_ascii= False))

            except Exception:
                continue
