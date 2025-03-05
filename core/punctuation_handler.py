from ..main import (
    AstrMessageEvent, ResultContentType, HumanLike, Plain, MessageChain
)

async def handle_punctuation(self: HumanLike, event: AstrMessageEvent):
    result = event.get_result()
    if not result:
        return

    try:
        chains = []
        original_chain = result.chain
        print(original_chain)
        
        text_result = event.make_result().set_result_content_type(
            ResultContentType.LLM_RESULT
        )
        
        # 去除指定的标点符号
        punctuation_config = self.config.get("Punctuation", {})
        delete_punctuation = punctuation_config.get("Delete_Punctuation", True)
        punctuation_list = punctuation_config.get("Punctuation_List", ["。", "！", "？", "；"])
        
        if original_chain:
            if isinstance(original_chain, str):
                # 纯文本
                text = original_chain
                if delete_punctuation:
                    for punct in punctuation_list:
                        text = text.replace(punct, "")
                text_result = text_result.message(text)
            elif isinstance(original_chain, MessageChain):
                for component in original_chain:
                    if isinstance(component, Plain):
                        # 文本消息
                        text = component.text
                        if delete_punctuation:
                            for punct in punctuation_list:
                                text = text.replace(punct, "")
                        text_result = text_result.message(text)
                    else:
                        # 非文本消息
                        text_result = text_result.message(component)
            elif isinstance(original_chain, list):
                # 列表消息
                for component in original_chain:
                    if isinstance(component, Plain):
                        text = component.text
                        if delete_punctuation:
                            for punct in punctuation_list:
                                text = text.replace(punct, "")
                        text_result = text_result.message(text)
                    else:
                        text_result = text_result.message(component)

        if text_result.get_plain_text().strip() or len(text_result.chain) > 0:
            event.set_result(text_result)
        else:
            await self.after_message_sent(event)
            event.stop_event()

    except Exception as e:
        self.logger.error(f"处理文本失败: {str(e)}")
        import traceback
        self.logger.error(traceback.format_exc())
