from collections import defaultdict
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Plain, Image
from astrbot.api.all import *

@register("astrbot_humanlike", "anka", "让ai更像真人", "1.0.0")
class HumanLike(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.ignore_list = defaultdict(int)

    def _set_ignore(self, session_id: str, user_id: str, num: int):
        key = (session_id, user_id)
        self.ignore_list[key] = num + 1

    @filter.command("ignore")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def cmd_ignore(self, event: AstrMessageEvent, num: int):
        '''(管理员)忽略当前用户消息 /ignore <数量>'''
        self._set_ignore(
            event.message_obj.session_id,
            event.get_sender_id(),
            num
        )
        yield event.plain_result(f"🤖 已忽略该用户接下来的 {num} 条消息")

    @filter.llm_tool(name="stop_responding")
    async def llm_ignore_tool(
        self, 
        event: AstrMessageEvent,
        silence_turns: int
    ) -> filter.MessageEventResult:
        '''
        允许AI主动选择不回应当前用户的后续消息
        
        Args:
            silence_turns(int): 需要保持沉默的对话轮次数
        '''
        current_user = event.get_sender_id()
        
        self._set_ignore(
            event.message_obj.session_id,
            current_user,
            silence_turns
        )
        
        # 可以选择不返回任何提示，更符合真人行为
        # 或者返回一个自然的中性响应
        yield event.plain_result(
            f"（暂时保持沉默）"
        )

    # 消息拦截检查（保持高优先级）
    @filter.event_message_type(filter.EventMessageType.ALL, priority=99999)
    async def check_ignore(self, event: AstrMessageEvent):
        key = (event.message_obj.session_id, event.get_sender_id())
        
        if self.ignore_list.get(key, 0) > 0:
            self.ignore_list[key] -= 1
            event.stop_event()  # 阻止后续处理
            
            # 可选：在最后一次沉默时给出提示
            if self.ignore_list[key] == 1:
                yield event.plain_result("（恢复交流）").set(send_before_stop=True)
            
            if self.ignore_list[key] <= 0:
                del self.ignore_list[key]