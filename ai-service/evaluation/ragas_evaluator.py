"""Chấm bằng RAGAS (Faithfulness, ...) từ file kết quả của run_eval --with-llm.

!!! CHƯA CHẠY THỬ. API của ragas thay đổi theo phiên bản: nếu báo lỗi import hoặc tên metric,
    đối chiếu https://docs.ragas.io (mục 'Evaluating Using Your Test Set') rồi sửa phần dưới.
Cài thêm:  pip install ragas datasets
Dùng:      python -m evaluation.ragas_evaluator evaluation/benchmarks_result/<file>_llm.json
Lưu ý: RAGAS dùng một LLM làm 'giám khảo' -> ghi rõ model giám khảo trong báo cáo."""
import json
import sys
from pathlib import Path

from app.core.config import settings


def main(path: str) -> None:
    from ragas import EvaluationDataset, evaluate
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import Faithfulness, LLMContextRecall
    from langchain_google_genai import ChatGoogleGenerativeAI

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    samples = [{
        "user_input": r["question"], "response": r["answer"],
        "retrieved_contexts": r["contexts"], "reference": r.get("ground_truth", ""),
    } for r in data["answerable"] if "answer" in r and not r.get("refused")]

    judge = LangchainLLMWrapper(ChatGoogleGenerativeAI(
        model=settings.gemini_chat_model, google_api_key=settings.google_api_key or None, temperature=0))
    result = evaluate(dataset=EvaluationDataset.from_list(samples),
                      metrics=[Faithfulness(llm=judge), LLMContextRecall(llm=judge)])
    print(result)


if __name__ == "__main__":
    main(sys.argv[1])
