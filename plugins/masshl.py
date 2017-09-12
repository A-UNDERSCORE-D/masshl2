from handler import message
from parser import Message


@message
def test(msg: Message):
    msg.conn.log.info(msg)
