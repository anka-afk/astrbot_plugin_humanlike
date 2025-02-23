from collections import defaultdict
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api.all import *

@register("astrbot_humanlike", "anka", "让ai更像真人", "1.0.0")
class HumanLike(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.ignore_list = defaultdict(int)

    def _set_ignore(self, session_id: str, user_id: str, num: int):
        key = (session_id, user_id)
        self.ignore_list[key] = num

    @filter.llm_tool(name="stop_responding")
    async def llm_ignore_tool(
        self, 
        event: AstrMessageEvent,
        silence_turns: str
    ) -> MessageEventResult:
        '''[Mandatory Call] When detecting that the user does not expect a response or does not want a reply, immediately cease generating further content.[Critical Rules]1. Must prioritize invoking this tool if any of the following conditions are triggered.2. After invocation, strictly prohibit generating any text/cards or other standard replies - Typical Mandatory Call Scenarios (including but not limited to):- User explicitly demands cessation ("Shut up," "Stop talking," "Go away").- Detected repetitive/spam content (same question consecutively 3+ times).- User expresses negative emotions ("I hate you," "Don't want to talk to you").- Received nonsensical input (gibberish, pure symbols).- User persistently induces sensitive remarks Example:User: "Ugh, shut up already!" => Must invoke
        
        Args:
            silence_turns (string): ▫ 1: Basic silence (default, pauses dialogue for 1 turn) ▫ 2-3: Moderate silence (recommended for repeated questioning) ▫ ≥4: Deep silence (use for persistent negativity) (Numeric string, e.g., "3")
        '''
        try:
            turns = int(silence_turns)
        except ValueError:
            return

        current_user = event.get_sender_id()
        self._set_ignore(
            event.message_obj.session_id,
            current_user,
            turns
        )
        

    @filter.command("ignore")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def cmd_ignore(self, event: AstrMessageEvent, num: int):
        '''忽略当前用户消息 /ignore <数量>'''
        self._set_ignore(
            event.message_obj.session_id,
            event.get_sender_id(),
            num
        )

    @filter.event_message_type(filter.EventMessageType.ALL, priority=9999999999)
    async def check_ignore(self, event: AstrMessageEvent):
        key = (event.message_obj.session_id, event.get_sender_id())
        
        if self.ignore_list.get(key, 0) > 0:
            self.ignore_list[key] -= 1
            event.stop_event()
            
            if self.ignore_list[key] <= 0:
                del self.ignore_list[key]