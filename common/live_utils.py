from lib2to3.pytree import Base
from otree.api import BasePlayer


def live_page(pagecls):
    """Decorator to add generic live_method to a Page class

    The live page receives messages in format: `{ type: sometype, fields: ... }`
    Both incoming and outgoing messages can be batched together into lists.

    Each message is delegated to class methods `handle_sometype(player, message)` that should be defined in a page class.

    Return value from handlers should be:
    ```
    { 
        destination: {        # destination player, or 0 for broadcast
            type: {           # type of message to send back
                field: value  # data for the messages
            }
        }
    } 

    The messages send back according to return value.
    """

    def generic_live_method(player, message):
        assert isinstance(message, dict) and "type" in message

        msgtype = message["type"]
        hndname = f"handle_{msgtype}"

        if not hasattr(pagecls, hndname):
            raise NotImplementedError(f"missing method ${hndname}")

        handler = getattr(pagecls, hndname)

        response = handler(player, message)

        senddata = {}

        for rcpt, msgdict in response.items():
            if isinstance(rcpt, BasePlayer):
                rcpt = rcpt.id_in_group
            senddata[rcpt] = []
            
            for type, data in msgdict.items():
                msg = { 'type': type }
                msg.update(data)
                senddata[rcpt].append(msg)
            
        return senddata

    pagecls.live_method = staticmethod(generic_live_method)

    return pagecls
