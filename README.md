# ai-workflow-handbook

How one non-programmer runs several AI agents (Claude, Gemini, a chat assistant) as a small team: who gets which job, how they share rules and memory, and the failures that shaped each rule. Written in Chinese.

一个不会写代码的人，怎么把几个 AI（Claude、Gemini、一个聊天助手）当成一个小团队来用：活怎么分，规矩和记忆怎么共用，每条规矩背后翻过什么车。正文是中文。

## What's here / 内容

- `AI 协作实战手册.md`: the handbook. Five parts: dispatching work to different models; building a system that runs unattended without knowing how to code (eight real failures and their fixes); debugging prompts and skills; building a knowledge base where AI files and you think; using AI in a real small business. 手册本体，分五部分：怎么给不同的模型派活；不会写代码也能搭一套无人值守稳定跑的系统（八次真实翻车和修法）；提示词和技能怎么调；搭一个"AI 负责整理、你负责思考"的知识库；AI 在真实小生意里的用法。
- `docs/记忆规矩.md`: a shared-memory format every agent reads and writes. Each memory line carries a type (rule or state), an importance, a last-confirmed date, who wrote it and the source. 所有 AI 共用的记忆格式。每条记忆都带类型（规矩还是现状）、重要度、最后确认日期、写者和来源。
- `tools/记忆排序.py`: scores every memory line (importance × freshness; "state" lines halve every 30 days, "rule" lines never decay) and writes a `MEMORY.md` with the top 15 that every agent reads at startup, plus a list of stale lines to re-check. 给每条记忆打分（重要度 × 新鲜度；"现状"类每 30 天减半，"规矩"类不衰减），生成一份 `MEMORY.md`：分数前 15 条是每个 AI 开工都读的常驻记忆，另列出过期待复核的条目。

```
python3 tools/记忆排序.py 示例          # try it on the sample / 用示例跑一遍
```

## Related / 相关项目

- [novel-machine](https://github.com/cc-cheese-kun/novel-machine): the unattended writing pipeline from part two of the handbook. 手册第二部分讲的那条无人值守写作流水线。
- [agent-board](https://github.com/cc-cheese-kun/agent-board): the shared task board the agents use. 几个 AI 共用的任务看板。
- [video-to-notes](https://github.com/cc-cheese-kun/video-to-notes): the knowledge-base pipeline from part four. 手册第四部分讲的知识库流水线。

## License

Code: MIT. Handbook text: CC BY 4.0.

代码用 MIT，手册正文用 CC BY 4.0。
