import json
import time
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph
from ragas import evaluate
from ragas.llms import llm_factory
from ragas.metrics import context_recall, faithfulness, context_precision
from datasets import Dataset
from app.infra.embd import embed
from app.service.agent_service import initialize_agent, init_sys_prompt

def run_eval():
    print("run eval 开始")
    current_dir = Path(__file__).parent.absolute()

    t0 = time.perf_counter()
    embeddings = embed
    t1 = time.perf_counter()
    print("init embeddings耗时:", t1 - t0, "秒")
    vectorstore = FAISS.load_local(folder_path=str(current_dir), index_name="gold_chunk_vectors", embeddings=embeddings, allow_dangerous_deserialization=True)
    t2 = time.perf_counter()
    print("init vectordb耗时:", t2 - t1, "秒")
    search_contexts = []
    @tool("gold_chunk_tool", description="rag质量测试工具，根据传参，到固定向量集合中去匹配数据")
    def gold_chunk_tool(q: str) -> list[str]:
        ret = vectorstore.similarity_search(q, k=5)
        texts = [doc.page_content for doc in ret]
        global search_contexts
        search_contexts = texts
        return texts
    model = ChatOllama(model="qwen2.5:3b")

    fixed_prompt = f"""{init_sys_prompt()}
        重要指令（测试模式）：
        1. 你**必须**使用gold_chunk_tool工具来回答所有问题
        2. 即使问题看起来不适合使用gold_chunk_tool，你也要尝试用它
        3. 如果无法使用gold_chunk_tool，请明确说明但依然尝试调用它

        当前可用工具：gold_chunk_tool（其他工具已禁用）
    """
    checkpointer = InMemorySaver()
    agent: CompiledStateGraph = initialize_agent(system_prompt=fixed_prompt, model=model, tools=[gold_chunk_tool],
                                                 checkpointer=checkpointer, middlewares=[])
    t3 = time.perf_counter()
    print("init langgraph耗时:", t3 - t2, "秒")
    with open(current_dir / "gold_qa.json", encoding="utf-8-sig") as f:
        gold_qa:list = json.load(f)
    gold_qa = gold_qa[:2]
    records = []
    for row in gold_qa:
        q = row["question"]
        # 1) 检索
        config = RunnableConfig(configurable={"thread_id": row['qid']})
        answer_msgs:list[BaseMessage] = agent.invoke(input={"messages": [HumanMessage(content=q)]}, config=config)['messages']
        answer = answer_msgs[-1].content
        print(f"q:{q}")
        print(f"a:{answer}")
        time.sleep(1)
        records.append({
            "question": q,
            "answer": answer,
            "contexts": search_contexts,
            "ground_truth": row["answer"]
        })

    dataset = Dataset.from_list(records)
    def ragas_score(qa_dataset: Dataset):
        # qa_dataset 必须含 columns: question, answer, contexts, ground_truth
        result = evaluate(
            qa_dataset,
            metrics=[context_precision, context_recall, faithfulness],
            llm=model,  # 复用主项目 LLM
            embeddings=embeddings  # 复用主项目embeddings
        )
        return result   # 返回 dict
    scores = ragas_score(dataset)
    print("RAGAS 三指标:", scores)
    #open(current_dir / "last_scores.json", "w").write(json.dumps(asdict(scores), ensure_ascii=False, indent=2))
    open(current_dir / "last_scores.json", "w").write(scores.to_pandas().to_string())

run_eval()