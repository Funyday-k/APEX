#!/usr/bin/env python3
"""本地 VLM 模型下载（HuggingFace / ModelScope）。"""
import argparse
import os


MODEL_MAP = {
    "qwen2-vl-7b": {
        "ms": "qwen/Qwen2-VL-7B-Instruct",
        "hf": "Qwen/Qwen2-VL-7B-Instruct",
    },
    "qwen2-vl-2b": {
        "ms": "qwen/Qwen2-VL-2B-Instruct",
        "hf": "Qwen/Qwen2-VL-2B-Instruct",
    },
}


def download_from_modelscope(model_id: str, local_dir: str):
    from modelscope import snapshot_download

    snapshot_download(model_id, local_dir=local_dir)
    print(f"模型已下载到 {local_dir}")


def download_from_hf(model_id: str, local_dir: str):
    from huggingface_hub import snapshot_download

    snapshot_download(repo_id=model_id, local_dir=local_dir)
    print(f"模型已下载到 {local_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2-vl-7b", choices=list(MODEL_MAP.keys()))
    parser.add_argument("--source", default="ms", choices=["ms", "hf"])
    parser.add_argument("--output", default="./models")
    args = parser.parse_args()

    model_ids = MODEL_MAP[args.model]
    local_dir = os.path.join(args.output, args.model)
    os.makedirs(os.path.dirname(local_dir) or ".", exist_ok=True)

    if args.source == "ms":
        download_from_modelscope(model_ids["ms"], local_dir)
    else:
        download_from_hf(model_ids["hf"], local_dir)


if __name__ == "__main__":
    main()
