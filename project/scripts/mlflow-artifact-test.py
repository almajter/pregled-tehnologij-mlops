# /// script
# dependencies = ["mlflow-skinny==3.16.0"]
# ///
import os
import tempfile

import mlflow

mlflow.set_tracking_uri("https://mlflow.apps.okd.alters.si")
mlflow.set_experiment("test-s3")

with mlflow.start_run(), tempfile.TemporaryDirectory() as tmp:
    mlflow.log_param("x", 1)
    path = os.path.join(tmp, "hello.txt")
    with open(path, "w") as f:
        f.write("hello s3\n")
    mlflow.log_artifact(path)
