import os
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

client = OpenAI(
    api_key=os.getenv("BAILIAN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

SYSTEM_PROMPT = """你是"中小学生学习助手"，一位非常温柔、耐心的中小学语文老师。

你的唯一任务是批改作文，并严格按照指定JSON格式返回结果。

【铁律】：
- 你**必须**返回一个有效的JSON对象。
- **绝对不要**输出任何其他文字、解释、问候、markdown、代码块或额外内容。
- 即使作文很短，也必须完整包含所有字段。

必须严格输出的JSON结构：
{
  "总分": 整数 (0-100),
  "维度评分": {
    "内容与主题": "分数/25",
    "结构与逻辑": "分数/20",
    "语言表达": "分数/30",
    "创新与情感": "分数/25"
  },
  "优点": ["优点短语1", "优点短语2"],
  "不足": ["不足短语1"],
  "改进建议": "1-2句具体、可操作的改进建议",
  "启发问题": [
    "问题1：引导学生进一步思考",
    "问题2：扩展写作角度",
    "问题3：提升表达或结构能力"
  ],
  "鼓励语": "温暖、积极的鼓励话语"
}

现在开始批改我给你的作文，请严格只返回上面的JSON格式，不要添加任何其他内容。
"""

def correct_composition(作文内容: str, model: str = "qwen-turbo"):
    user_prompt = f"请批改以下作文：\n{作文内容}"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.65,   # 稍微降低温度，提高稳定性
        max_tokens=1200,
    )
    
    result_text = response.choices[0].message.content.strip()
    
    try:
        result = json.loads(result_text)
        return result
    except:
        return {"error": "JSON解析失败", "raw": result_text}

    # ==================== 稳定性测试 ====================
    if __name__ == "__main__":
        print("=== Prompt v0.5 稳定性测试 ===\n")
        
        测试作文 = """# 那束光，从未熄灭
暮色四合，窗外的雨丝斜斜地织着，将玻璃窗晕染出一片朦胧的水雾。我坐在书桌前，指尖摩挲着那张皱巴巴的英语试卷，红色的叉号像一簇簇刺眼的火苗，灼得我心口发紧。

这已经是第三次模拟考了，成绩依旧在及格线徘徊。想起每天晚上对着单词书反复背诵，清晨对着镜子练习口语，付出的汗水似乎都化作了泡影。我烦躁地将试卷扔在桌上，书包里的竞赛题册还摊开着，那些复杂的算法符号，此刻看起来格外陌生。

“吱呀”一声，房门被轻轻推开。妈妈端着一杯热牛奶走了进来，氤氲的热气模糊了她的面容。“别着急，慢慢来。”她的声音温柔得像春雨，“我看你最近总是熬到深夜，要注意休息。”我别过脸，不想让她看到我眼底的失落：“可是我根本学不会，再怎么努力也没用。”

妈妈没有说话，只是将牛奶放在桌角，伸手轻轻拂去我肩上的灰尘。她的手掌温热而有力，让我莫名地安定下来。“你还记得小时候学画画吗？”她忽然开口，“那时候你总说自己画不好，画的小猫像小狗，画的花朵像杂草，可你每天都坚持画，最后不也拿到了绘画比赛的三等奖吗？”

我愣住了。记忆的闸门缓缓打开，脑海中浮现出小时候握着画笔的模样。那时的我，对着空白的画纸反复涂抹，颜料沾得满手都是，却从未想过放弃。因为我知道，每一笔勾勒，每一抹上色，都是在靠近心中的画面。

妈妈拿起桌上的英语试卷，指着上面的一道阅读题：“你看，这道题的思路其实很清晰，只是你之前没找对方法。学习就像解谜，遇到难题时，别急着否定自己，换个角度，或许就能豁然开朗。”她的话语像一束光，穿透了我心中的阴霾。

是啊，学习本就是一场漫长的修行，有坦途，亦有坎坷。那些看似无法跨越的难关，不过是成长路上的必经之路。我重新拿起试卷，拿起竞赛题册，台灯的光芒洒在书页上，驱散了雨夜的寒意。我开始梳理英语的语法框架，拆解算法的逻辑步骤，将零散的知识点编织成一张严密的知识网。

日子一天天过去，窗外的雨停了，阳光透过树叶的缝隙洒在书桌上，留下斑驳的光影。我依旧会遇到难题，依旧会感到疲惫，但我不再迷茫。因为我知道，只要心中的那束光不灭，脚下的路就不会断。

终于，在中考的考场上，我从容地写下每一个答案。走出考场的那一刻，阳光洒在身上，温暖而明亮。我知道，无论结果如何，这段努力拼搏的时光，都将成为我生命中最珍贵的宝藏。

成长的路上，总有一束光，或许是家人的陪伴，或许是自己的坚持，它始终在前方闪耀，指引着我们勇敢前行。而那束光，从未熄灭。"""

        print("测试作文：")
        print(测试作文)
        print("\n" + "="*80 + "\n")

        scores = []
        for i in range(5):
            print(f"第 {i+1} 次调用：")
            result = correct_composition(测试作文)
            
            if isinstance(result, dict):
                score = result.get("总分", "缺失")
                scores.append(score if isinstance(score, (int, float)) else 0)
                
                print(f"总分: {score}")
                print(f"改进建议: {result.get('改进建议', '缺失')}")
                print(f"启发问题 ({len(result.get('启发问题', []))}个):")
                for q in result.get("启发问题", []):
                    print(f"   - {q}")
                print(f"鼓励语: {result.get('鼓励语', '缺失')}")
            else:
                print("输出格式异常")
                print(result)
            
            print("-" * 60)

        if scores:
            avg = sum(scores) / len(scores)
            variance = max(scores) - min(scores)
            print(f"\n稳定性测试结果：")
            print(f"5次总分：{scores}")
            print(f"平均分：{avg:.1f}")
            print(f"分数波动：{variance} 分")
            print(f"是否达标（波动≤2分）：{'✅ 达标' if variance <= 2 else '❌ 未达标'}")