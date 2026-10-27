# /// script
# dependencies = ["kfp==2.17.3"]
# ///
from kfp import compiler, dsl
from kfp.dsl import Dataset, Input, Model, Output


@dsl.component(packages_to_install=["datasets==5.1.0"])
def prepare_data(dataset_revision: str, n_train: int, train_data: Output[Dataset]):
    import json

    from datasets import load_dataset

    rows = load_dataset(
        "openai/gsm8k", "socratic", revision=dataset_revision, split="train"
    )

    examples = []
    skipped = 0
    for row in rows:
        # the last line holds the final answer ("#### <answer>")
        steps = row["answer"].split("\n")[:-1]
        # skip answers with a single step
        if len(steps) < 2:
            skipped += 1
            continue

        # take only the sub question from the first step, without the solution
        first_question = steps[0].split(" ** ")[0]
        examples.append(
            {
                "messages": [
                    {"role": "user", "content": row["question"]},
                    {"role": "assistant", "content": first_question},
                ]
            }
        )
        if len(examples) == n_train:
            break

    with open(train_data.path, "w") as f:
        for example in examples:
            f.write(json.dumps(example) + "\n")

    print(f"examples: {len(examples)}, skipped single step: {skipped}")
    train_data.metadata["examples"] = len(examples)
    train_data.metadata["skipped_single_step"] = skipped


@dsl.component(
    base_image="pytorch/pytorch:2.14.1-cuda13.0-cudnn9-runtime",
    packages_to_install=[
        "transformers==5.21.0",
        "peft==0.21.2",
        "trl==1.16.0",
        "datasets==5.1.0",
        "mlflow-skinny==3.16.0",
    ],
)
def train(
    model_name: str,
    model_revision: str,
    lora_rank: int,
    epochs: int,
    learning_rate: float,
    mlflow_uri: str,
    train_data: Input[Dataset],
    adapter: Output[Model],
) -> str:
    import mlflow
    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from trl import SFTConfig, SFTTrainer

    dataset = load_dataset("json", data_files=train_data.path, split="train")
    dataset = dataset.map(
        lambda row: {"prompt": row["messages"][:1], "completion": row["messages"][1:]},
        remove_columns=["messages"],
    )

    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment("socratic-tutor")
    with mlflow.start_run() as run:
        mlflow.log_params(
            {
                "model_name": model_name,
                "model_revision": model_revision,
                "train_examples": len(dataset),
            }
        )
        trainer = SFTTrainer(
            model=model_name,
            train_dataset=dataset,
            peft_config=LoraConfig(
                r=lora_rank,
                lora_alpha=lora_rank * 2,
                target_modules="all-linear",
                task_type="CAUSAL_LM",
            ),
            args=SFTConfig(
                output_dir="/tmp/output",
                num_train_epochs=epochs,
                learning_rate=learning_rate,
                model_init_kwargs={"revision": model_revision, "dtype": torch.bfloat16},
                save_strategy="no",
                report_to="mlflow",
            ),
        )
        trainer.train()

        trainer.save_model(adapter.path)
        mlflow.log_artifacts(adapter.path, artifact_path="adapter")
        return run.info.run_id


@dsl.pipeline
def socratic_tutor(
    dataset_revision: str = "740312add88f781978c0658806c59bc2815b9866",
    n_train: int = 500,
    model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
    model_revision: str = "7ae557604adf67be50417f59c2c2f167def9a775",
    lora_rank: int = 16,
    epochs: int = 3,
    learning_rate: float = 2e-4,
    mlflow_uri: str = "https://mlflow.apps.okd.alters.si",
):
    data_task = prepare_data(dataset_revision=dataset_revision, n_train=n_train)

    train_task = train(
        model_name=model_name,
        model_revision=model_revision,
        lora_rank=lora_rank,
        epochs=epochs,
        learning_rate=learning_rate,
        mlflow_uri=mlflow_uri,
        train_data=data_task.outputs["train_data"],
    )
    train_task.set_accelerator_type("nvidia.com/gpu").set_accelerator_limit(1)
    train_task.set_memory_request("8Gi").set_cpu_request("2")
    train_task.set_caching_options(False)
    # pip: externally-managed-environment
    train_task.set_env_variable("PIP_BREAK_SYSTEM_PACKAGES", "1")
    # PermissionError: '/.triton'
    train_task.set_env_variable("HOME", "/tmp")


compiler.Compiler().compile(socratic_tutor, "pipeline.yaml")
