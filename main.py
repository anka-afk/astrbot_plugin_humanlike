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
        '''[Mandatory Call] Immediately cease generating content when detecting the user does not expect a response.[Critical Rules]1. Prioritize invoking this tool if any condition is triggered.2. Prohibit generating text/cards after invocation.3. Automatically escalate silence level for consecutive triggers (increment by 1 level per round) - Typical Scenarios (including but not limited to):- User explicitly demands cessation ("Shut up", "Stop talking", "Go away").- Detected repetitive/spam content (same question 3+ times consecutively).- User expresses negative emotions ("I hate you", "Don't want to talk to you").- Received nonsensical input (gibberish/pure symbols).- User persistently induces sensitive remarks Example:User: "Ugh shut up!" => Must invoke (first trigger silence_turns=1) User: "Stop replying!" => Must invoke (second trigger silence_turns=2)
        
        Args:
            silence_turns (string): ▫ 1: Basic silence (default, 1-turn pause) ▫ 2-3: Moderate silence (auto-calculated based on consecutive trigger count) ▫ ≥4: Deep silence (auto-applied for persistent triggers) (Numeric string, e.g., "2" indicates system-auto-calculated level 2)
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
