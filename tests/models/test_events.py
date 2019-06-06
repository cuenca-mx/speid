from speid.models import Event, Transaction
from speid.types import EventType


def test_event():
    received = Event(type=EventType.received)
    completed = Event(type=EventType.completed)
    transaction = Transaction(events=[received, completed])
    transaction.save()
    id_trx = transaction.id
    transaction = Transaction.objects.get(id=id_trx)
    assert len(transaction.events) == 2
    assert transaction.events[0].type == received.type
    assert transaction.events[1].type == completed.type
    transaction.delete()
