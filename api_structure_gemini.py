"""
API structure của gemini + litellm

gemini:


"""

from datetime import datetime
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("api_key"))

interaction = client.interactions.create(
    model="gemini-3.5-flash-lite", input="Hello, who are you"
)

print(interaction.model_dump_json(indent=2))


@dataclass
class GeminiResponse:
    status: str
    model: str
    id: str
    created: datetime
    updated: datetime
    usage: dict



# status='completed'
# model='gemini-3.5-flash-lite'
# agent=None 
# id='v1_ChcwbU5wYXR1RUlKWE0ycm9QaW9iRTZBNBIXMG1OcGF0dUVJSlhNMnJvUGlvYkU2QTQ' 
# created='2026-07-29T02:22:10Z' 
# updated='2026-07-29T02:22:10Z' 
# system_instruction=None 
# tools=None 
# usage=Usage(
#       cached_tokens_by_modality=None, 
#       grounding_tool_count=None, 
#       input_tokens_by_modality=[
#       ModalityTokens(modality='text', tokens=72)], 
    #       output_tokens_by_modality=None, 
    #       tool_use_tokens_by_modality=None,
    #       total_cached_tokens=0, 
    #       total_input_tokens=72, 
    #       total_output_tokens=63, 
    #       total_thought_tokens=0, 
    #       total_tokens=135, 
    #       total_tool_use_tokens=0) 
#       response_modalities=None 
#       response_mime_type=None 
#       previous_interaction_id=None 
#       environment_id=None 
#       service_tier='standard' 
#       webhook_config=None 
#       steps=[
    #       ThoughtStep(
        #       signature='EjQKMgERTTIPzDrqu0nM1Z7w8zA/6/kWhCW2OHX6h9KP2d6OUN211TPrYaXthAdn00FP327S', 
        #       summary=None, 
        #       type='thought'
#           ),
#           ModelOutputStep(
#           content=[TextContent(
#           text='Chào bạn! Tôi là một trợ lý AI (trí tuệ nhân tạo) được tạo ra để giúp bạn giải đáp thắc mắc,
#           tìm kiếm thông tin, hỗ trợ công việc, học tập, viết lách và nhiều việc khác nữa. 
#           \n\nTôi có thể giúp gì cho bạn hôm nay?', 
#           annotations=None, 
#           type='text')], 
#           error=None, 
#           type='model_output')] 
#           response_format=None 
#           environment=None 
#           generation_config=None 
#           agent_config=None 
#           safety_settings=None 
#           labels=None input=None 
#           output_text='Chào bạn! Tôi là một trợ lý AI (trí tuệ nhân tạo) được tạo ra để giúp bạn giải đáp thắc mắc, 
#           tìm kiếm thông tin, hỗ trợ công việc, học tập, viết lách và nhiều việc khác nữa. 
#           \n\nTôi có thể giúp gì cho bạn hôm nay?' 
#           output_image=None 
#           output_audio=None 
#           output_video=None 
#           object='interaction'
# AI:  Chào bạn! Tôi là một trợ lý AI (trí tuệ nhân tạo) được tạo ra để giúp bạn giải đáp thắc mắc, tìm kiếm thông tin, hỗ trợ công việc, học tập, viết lách và nhiều việc khác nữa.
