import copy
from typing import Dict, Iterator, List, Optional, Union

from qwen_agent import Agent
from qwen_agent.agents import Assistant
from qwen_agent.llm import BaseChatModel


class VisualStorytelling(Agent):
    """Customize an agent for writing story from pictures"""

    def __init__(self,
                 function_list: Optional[List[Union[str, Dict]]] = None,
                 llm: Optional[Union[Dict, BaseChatModel]] = None):
        super().__init__(llm=llm)

        # Nest one vl assistant for image understanding
        self.image_agent = Assistant(llm={'model': 'qwen-vl-plus'})

        # Nest one assistant for article writing
        self.writing_agent = Assistant(
            llm=self.llm,
            function_list=function_list,
            system_message='你扮演一个想象力丰富的学生，你需要先理解图片内容，根据描述图片信息以后，' +
            '参考知识库中教你的写作技巧，发挥你的想象力，写一篇800字的记叙文',
            files=['https://www.jianshu.com/p/cdf82ff33ef8'])

    def _run(self,
             messages: List[Dict],
             lang: str = 'zh',
             max_ref_token: int = 4000,
             **kwargs) -> Iterator[List[Dict]]:
        """Define the workflow"""

        assert isinstance(messages[-1]['content'], list) and any([
            'image' in item.keys() for item in messages[-1]['content']
        ]), 'This agent requires input of images'

        # image understanding
        new_messages = copy.deepcopy(messages)
        new_messages[-1]['content'].append({'text': '请详细描述这张图片的所有细节内容'})
        response = []
        for rsp in self.image_agent.run(new_messages):
            yield response + rsp
        response.extend(rsp)
        new_messages.extend(rsp)

        # writing article
        new_messages.append({'role': 'user', 'content': '开始根据以上图片内容编写你的记叙文吧！'})
        for rsp in self.writing_agent.run(new_messages,
                                          lang=lang,
                                          max_ref_token=max_ref_token,
                                          **kwargs):
            yield response + rsp


def main():
    # define a writer agent
    bot = VisualStorytelling(llm={'model': 'qwen-max'})

    # chat
    messages = []
    while True:
        query = input('user question: ')
        # image example: https://img01.sc115.com/uploads3/sc/vector/201809/51413-20180914205509.jpg
        image = input('image url: ')

        if not image:
            print('image cannot be empty！')
            continue
        messages = [{'role': 'user', 'content': [{'image': image}]}]
        if query:
            messages[-1]['content'].append({'text': query})

        response = []
        for response in bot.run(messages):
            print('bot response:', response)
        messages.extend(response)


if __name__ == '__main__':
    main()