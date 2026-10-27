# /// script
# dependencies = ["kfp==2.17.3"]
# ///
from kfp import compiler, dsl
from kfp.dsl import Dataset, Output


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


@dsl.pipeline
def socratic_tutor(
    dataset_revision: str = "740312add88f781978c0658806c59bc2815b9866",
    n_train: int = 500,
):
    prepare_data(dataset_revision=dataset_revision, n_train=n_train)


compiler.Compiler().compile(socratic_tutor, "pipeline.yaml")
