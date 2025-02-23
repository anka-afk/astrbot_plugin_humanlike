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
        '''
        [重要工具]当需要模拟人类思考停顿、处理敏感场景或不想回复用户消息时，主动暂停回复用户消息。
        
        典型调用场景：
        1. 用户发送负面指令："闭嘴"、"走开"、"别说了"
        2. 用户连续追问超过3次，需要制造回复间隔
        3. 遇到无法立即回答的复杂问题，需要"思考"时间
        4. 用户发送重复或无意义内容（如刷屏）
        5. 对话涉及敏感话题需要回避
        6. 出于讨厌等原因不想回复当前用户消息
        
        Args:
            silence_turns (int): 需要保持沉默的对话轮次数，建议值：
                - 1: 短暂停顿（默认）
                - 2-3: 中等思考时间
                - 4+: 长时间不响应（慎用）
        
        调用示例：
        当用户说"你太吵了，安静会儿"时：
        → {"tool": "stop_responding", "args": {"silence_turns": 2}}
        
        当用户连续提问3个以上数学题：
        → {"tool": "stop_responding", "args": {"silence_turns": 1}}
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

    @filter.event_message_type(filter.EventMessageType.ALL, priority=1)
    async def check_ignore(self, event: AstrMessageEvent):
        key = (event.message_obj.session_id, event.get_sender_id())
        
        if self.ignore_list.get(key, 0) > 0:
            self.ignore_list[key] -= 1
            event.stop_event()
            
            if self.ignore_list[key] <= 0:
                del self.ignore_list[key]