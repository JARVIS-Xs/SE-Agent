import random
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Literal
import json

from pydantic import BaseModel, ConfigDict, Field, model_validator
from swerex.deployment.config import (
    DeploymentConfig,
    DockerDeploymentConfig,
    DummyDeploymentConfig,
    LocalDeploymentConfig,
)
from typing_extensions import Self

from sweagent.agent.problem_statement import ProblemStatementConfig, TextProblemStatement
from sweagent.environment.repo import GithubRepoConfig, LocalRepoConfig, PreExistingRepoConfig
from sweagent.environment.swe_env import EnvironmentConfig
from sweagent.utils.files import load_file
from sweagent.utils.log import get_logger

logger = get_logger("swea-config", emoji="🔧")


class AbstractInstanceSource(ABC):
    """Anything that adheres to this standard can be used to load instances."""

    @abstractmethod
    def get_instance_configs(self) -> list[EnvironmentConfig]: ...


class BatchInstance(BaseModel):
    """A single instance in a batch of instances.
    This specifies both the environment configuration and the problem statement.
    """

    env: EnvironmentConfig
    problem_statement: ProblemStatementConfig


def _slice_spec_to_slice(slice_spec: str) -> slice:
    if slice_spec == "":
        return slice(None)
    parts = slice_spec.split(":")
    values = [None if p == "" else int(p) for p in parts]
    if len(parts) == 1:
        return slice(values[0])
    if len(parts) == 2:
        return slice(values[0], values[1])
    if len(parts) == 3:
        return slice(values[0], values[1], values[2])
    msg = (
        f"Invalid slice specification: {slice_spec!r}. "
        "Here's the expected format: stop or start:stop or start:stop:step "
        "(i.e., it behaves exactly like python's list slicing `list[slice]`)."
    )
    raise ValueError(msg)


def _filter_batch_items(
    instances: list[BatchInstance], *, filter_: str, slice_: str = "", shuffle: bool = False
) -> list[BatchInstance]:
    if shuffle:
        instances = sorted(instances.copy(), key=lambda x: x.problem_statement.id)
        random.seed(42)
        random.shuffle(instances)
    before_filter = len(instances)
    instances = [instance for instance in instances if re.match(filter_, instance.problem_statement.id)]
    after_filter = len(instances)
    if before_filter != after_filter:
        logger.info("Instance filter: %d -> %d instances", before_filter, after_filter)
    if slice_:
        instances = instances[_slice_spec_to_slice(slice_)]
        after_slice = len(instances)
        if before_filter != after_slice:
            logger.info("Instance slice: %d -> %d instances", before_filter, after_slice)
    return instances


class SimpleBatchInstance(BaseModel):
    """A simple way to configure a single instance in a batch of instances that all
    use similar deployment configurations.

    Predominantly used for benchmarking purposes. Assumes that the repository is already
    present in the docker container.
    """

    image_name: str
    problem_statement: str
    instance_id: str
    repo_name: str = ""
    """Specifies the repository to use. If empty, no repository is used.
    If the string does not contain a slash, it is interpreted as an already existing repository at the root
    of the docker container. If it contains the word "github", it is interpreted as a github repository.
    Else, it is interpreted as a local repository.
    """
    base_commit: str = "HEAD"
    """Used to reset repo."""
    extra_fields: dict[str, Any] = Field(default_factory=dict)
    """Any additional data to be added to the instance.
    This data will be available when formatting prompt templates.
    """

    # Ignore instead of allow because they should be added as `extra_fields`
    model_config = ConfigDict(extra="ignore")

    def to_full_batch_instance(self, deployment: DeploymentConfig) -> BatchInstance:
        """Merge the deployment options into the `SimpleBatchInstance` object to get a full `BatchInstance`."""
        # Very important: Make a copy of the deployment config because it will be shared among instances!!!
        deployment = deployment.model_copy(deep=True)
        problem_statement = TextProblemStatement(
            text=self.problem_statement, id=self.instance_id, extra_fields=self.extra_fields
        )
        if not self.repo_name:
            repo = None
        elif "github" in self.repo_name:
            repo = GithubRepoConfig(github_url=self.repo_name, base_commit=self.base_commit)
        elif "/" not in self.repo_name:
            repo = PreExistingRepoConfig(repo_name=self.repo_name, base_commit=self.base_commit)
        else:
            repo = LocalRepoConfig(path=Path(self.repo_name), base_commit=self.base_commit)
        if isinstance(deployment, LocalDeploymentConfig):
            if self.image_name:
                msg = "Local deployment does not support image_name"
                raise ValueError(msg)
            return BatchInstance(
                env=EnvironmentConfig(deployment=deployment, repo=repo), problem_statement=problem_statement
            )
        if isinstance(deployment, DummyDeploymentConfig):
            return BatchInstance(
                env=EnvironmentConfig(deployment=deployment, repo=repo), problem_statement=problem_statement
            )

        deployment.image = self.image_name  # type: ignore

        if isinstance(deployment, DockerDeploymentConfig) and deployment.python_standalone_dir is None:
            # Note: you can disable this by setting python_standalone_dir to ""
            deployment.python_standalone_dir = "/root"  # type: ignore

        return BatchInstance(
            env=EnvironmentConfig(deployment=deployment, repo=repo), problem_statement=problem_statement
        )

    @model_validator(mode="before")
    @classmethod
    def handle_legacy_id(cls, data):
        # Handling compatibility with swe-agent <= 1.0.1
        if isinstance(data, dict):
            if "id" in data and "instance_id" not in data:
                data["instance_id"] = data["id"]
                data.pop("id")
        return data

    # todo: Maybe populate extra fields?
    @classmethod
    def from_swe_bench(cls, instance: dict[str, Any]) -> Self:
        """Convert instances from the classical SWE-bench dataset to the `SimpleBatchInstance` format."""
        iid = instance["instance_id"]
        image_name = instance.get("image_name", None)
        if image_name is None:
            # Docker doesn't allow double underscore, so we replace them with a magic token
            id_docker_compatible = iid.replace("__", "_1776_")
            image_name = f"swebench/sweb.eval.x86_64.{id_docker_compatible}:latest".lower()
        return cls(
            image_name=image_name,
            problem_statement=instance["problem_statement"],
            instance_id=iid,
            repo_name="testbed",
            base_commit=instance["base_commit"],
        )


class InstancesFromFile(BaseModel, AbstractInstanceSource):
    """Load instances from a file."""

    path: Path
    filter: str = ".*"
    """Regular expression to filter the instances by instance id."""
    slice: str = ""
    """Select only a slice of the instances (after filtering by `filter`).
    Possible values are stop or start:stop or start:stop:step
    (i.e., it behaves exactly like python's list slicing `list[slice]`).
    """
    shuffle: bool = False
    """Shuffle the instances (before filtering and slicing)."""

    deployment: DeploymentConfig = Field(
        default_factory=lambda: DockerDeploymentConfig(image="python:3.11"),
        description="Deployment options.",
    )
    """Note that the image_name option is overwritten by the images specified in the task instances."""

    simple: Literal[True] = True
    """Convenience discriminator for (de)serialization/CLI. Do not change."""

    type: Literal["file"] = "file"
    """Discriminator for (de)serialization/CLI. Do not change."""

    def get_instance_configs(self) -> list[BatchInstance]:
        instance_dicts = load_file(self.path)
        simple_instances = [SimpleBatchInstance.model_validate(instance_dict) for instance_dict in instance_dicts]
        instances = [instance.to_full_batch_instance(self.deployment) for instance in simple_instances]
        return _filter_batch_items(instances, filter_=self.filter, slice_=self.slice, shuffle=self.shuffle)

    @property
    def id(self) -> str:
        return self.path.stem


class InstancesFromHuggingFace(BaseModel, AbstractInstanceSource):
    """Load instances from HuggingFace."""

    dataset_name: str
    """Name of the HuggingFace dataset. Same as when using `datasets.load_dataset`."""
    split: str = "dev"
    filter: str = ".*"
    """Regular expression to filter the instances by instance id."""
    slice: str = ""
    """Select only a slice of the instances (after filtering by `filter`).
    Possible values are stop or start:stop or start:stop:step.
    (i.e., it behaves exactly like python's list slicing `list[slice]`).
    """
    shuffle: bool = False
    """Shuffle the instances (before filtering and slicing)."""

    deployment: DeploymentConfig = Field(
        default_factory=lambda: DockerDeploymentConfig(image="python:3.11"),
    )
    """Deployment configuration. Note that the `image_name` option is overwritten by the images specified in the task instances.
    """
    type: Literal["huggingface"] = "huggingface"
    """Discriminator for (de)serialization/CLI. Do not change."""

    def get_instance_configs(self) -> list[BatchInstance]:
        from datasets import load_dataset

        ds: list[dict[str, Any]] = load_dataset(self.dataset_name, split=self.split)  # type: ignore
        simple_instances: list[SimpleBatchInstance] = [SimpleBatchInstance.model_validate(instance) for instance in ds]
        instances = [instance.to_full_batch_instance(self.deployment) for instance in simple_instances]
        return _filter_batch_items(instances, filter_=self.filter, slice_=self.slice, shuffle=self.shuffle)

    @property
    def id(self) -> str:
        ds_name = "".join(l for l in self.dataset_name if l.isalnum() or l in ["-", "_"])
        return f"{ds_name}_{self.split}"


class SWEBenchInstances(BaseModel, AbstractInstanceSource):
    """Load instances from SWE-bench."""

    subset: Literal["lite", "verified", "full", "multimodal", "multilingual"] = "lite"
    """Subset of swe-bench to use"""

    # IMPORTANT: Do not call this `path`, because then if people do not specify instance.type,
    # it might be resolved to ExpertInstancesFromFile or something like that.
    path_override: str | Path | None = None
    """Allow to specify a different huggingface dataset name or path to a huggingface
    dataset. This will override the automatic path set by `subset`.
    """

    split: Literal["dev", "test"] = "dev"

    deployment: DeploymentConfig = Field(
        default_factory=lambda: DockerDeploymentConfig(image="python:3.11"),
    )
    """Deployment configuration. Note that the image_name option is overwritten by the images specified in the task instances.
    """

    type: Literal["swe_bench"] = "swe_bench"
    """Discriminator for (de)serialization/CLI. Do not change."""

    filter: str = ".*"
    """Regular expression to filter the instances by instance id."""
    slice: str = ""
    """Select only a slice of the instances (after filtering by `filter`).
    Possible values are stop or start:stop or start:stop:step.
    (i.e., it behaves exactly like python's list slicing `list[slice]`).
    """
    shuffle: bool = False
    """Shuffle the instances (before filtering and slicing)."""

    evaluate: bool = False
    """Run sb-cli to evaluate"""

    def _get_dataset_path(self) -> str:
        if self.path_override is not None:
            return str(self.path_override)
        dataset_mapping = {
            "full": "princeton-nlp/SWE-Bench",
            "verified": "princeton-nlp/SWE-Bench_Verified",
            "lite": "princeton-nlp/SWE-Bench_Lite",
            "multimodal": "princeton-nlp/SWE-Bench_Multimodal",
            "multilingual": "swe-bench/SWE-Bench_Multilingual",
        }

        if self.subset not in dataset_mapping:
            msg = f"Unsupported subset: {self.subset}"
            raise ValueError(msg)

        return dataset_mapping[self.subset]

    def get_instance_configs(self) -> list[BatchInstance]:
        from datasets import load_dataset

        ds: list[dict[str, Any]] = load_dataset(self._get_dataset_path(), split=self.split)  # type: ignore

        if isinstance(self.deployment, DockerDeploymentConfig):
            self.deployment.platform = "linux/amd64"

        instances = [
            SimpleBatchInstance.from_swe_bench(instance).to_full_batch_instance(self.deployment) for instance in ds
        ]
        return _filter_batch_items(instances, filter_=self.filter, slice_=self.slice, shuffle=self.shuffle)

    @property
    def id(self) -> str:
        return f"swe_bench_{self.subset}_{self.split}"


class ExpertInstancesFromFile(BaseModel, AbstractInstanceSource):
    """Load instances from a file. The difference to `InstancesFromFile` is that the instances are configured as full
    `EnvironmentInstanceConfig` objects, i.e., we could specify separate deployment configurations etc.
    """

    path: Path
    filter: str = ".*"
    """Regular expression to filter the instances by instance id."""
    slice: str = ""
    """Select only a slice of the instances (after filtering by `filter`).
    Possible values are stop or start:stop or start:stop:step.
    (i.e., it behaves exactly like python's list slicing `list[slice]`).
    """
    shuffle: bool = False
    """Shuffle the instances (before filtering and slicing)."""

    type: Literal["expert_file"] = "expert_file"
    """Discriminator for (de)serialization/CLI. Do not change."""

    def get_instance_configs(self) -> list[BatchInstance]:
        instance_dicts = load_file(self.path)
        instances = [BatchInstance.model_validate(instance_dict) for instance_dict in instance_dicts]
        return _filter_batch_items(instances, filter_=self.filter, slice_=self.slice, shuffle=self.shuffle)

    @property
    def id(self) -> str:
        return self.path.stem


class SWESmithInstances(BaseModel, AbstractInstanceSource):
    """Load instances from SWE-smith."""

    path: Path

    deployment: DeploymentConfig = Field(
        default_factory=lambda: DockerDeploymentConfig(image="python:3.11"),
    )
    """Deployment configuration. Note that the image_name option is overwritten by the images specified in the task instances.
    """

    filter: str = ".*"
    """Regular expression to filter the instances by instance id."""
    slice: str = ""
    """Select only a slice of the instances (after filtering by `filter`).
    Possible values are stop or start:stop or start:stop:step.
    (i.e., it behaves exactly like python's list slicing `list[slice]`).
    """
    shuffle: bool = False
    """Shuffle the instances (before filtering and slicing)."""

    type: Literal["swesmith"] = "swesmith"
    """Discriminator for (de)serialization/CLI. Do not change."""

    def get_instance_configs(self) -> list[BatchInstance]:
        def convert_instance_dict(instance_dict: dict[str, Any]) -> dict[str, Any]:
            instance_dict["id"] = instance_dict["instance_id"]
            # todo: The base_commit is currently incorrect
            instance_dict["base_commit"] = instance_dict["id"]
            instance_dict["problem_statement"] = instance_dict.get("problem_statement", "")
            instance_dict["repo_name"] = "testbed"
            instance_dict["extra_fields"] = {"fail_to_pass": instance_dict["FAIL_TO_PASS"]}
            return instance_dict

        instance_dicts = load_file(self.path)
        instances = [
            SimpleBatchInstance.model_validate(convert_instance_dict(instance_dict)).to_full_batch_instance(
                self.deployment
            )
            for instance_dict in instance_dicts
        ]
        return _filter_batch_items(instances, filter_=self.filter, slice_=self.slice, shuffle=self.shuffle)

    @property
    def id(self) -> str:
        return f"swesmith_{self.path.stem}"


class InstancesFromIdList(BaseModel, AbstractInstanceSource):
    """Load instances from SWE-bench, but filter by a list of instance IDs from a JSON file."""

    path: Path
    """Path to the JSON file containing the list of instance IDs."""
    
    key: str = "difference_ids"
    """Key in the JSON file that contains the list of instance IDs."""
    
    subset: Literal["full", "verified", "lite", "multimodal", "multilingual"] = "verified"
    """Subset of swe-bench to use"""

    # IMPORTANT: Do not call this `path`, because then if people do not specify instance.type,
    # it might be resolved to ExpertInstancesFromFile or something like that.
    path_override: str | Path | None = None
    """Allow to specify a different huggingface dataset name or path to a huggingface
    dataset. This will override the automatic path set by `subset`.
    """

    split: Literal["dev", "test"] = "test"

    deployment: DeploymentConfig = Field(
        default_factory=lambda: DockerDeploymentConfig(image="python:3.11"),
    )
    """Deployment configuration. Note that the image_name option is overwritten by the images specified in the task instances.
    """

    type: Literal["id_list"] = "id_list"
    """Discriminator for (de)serialization/CLI. Do not change."""

    shuffle: bool = False
    """Shuffle the instances (before filtering and slicing)."""

    evaluate: bool = False
    """Whether to evaluate the results using SWE-bench CLI."""

    def _get_dataset_path(self) -> str:
        if self.path_override is not None:
            return str(self.path_override)
        dataset_mapping = {
            "full": "princeton-nlp/SWE-Bench",
            "verified": "princeton-nlp/SWE-Bench_Verified",
            "lite": "princeton-nlp/SWE-Bench_Lite",
            "multimodal": "princeton-nlp/SWE-Bench_Multimodal",
            "multilingual": "swe-bench/SWE-Bench_Multilingual",
        }

        if self.subset not in dataset_mapping:
            msg = f"Unsupported subset: {self.subset}"
            raise ValueError(msg)

        return dataset_mapping[self.subset]

    def get_instance_configs(self) -> list[BatchInstance]:
        from datasets import load_dataset

        # 确保文件路径是绝对路径
        path = Path(self.path).resolve()
        logger.info(f"Loading instance IDs from {path}")
        
        # 加载JSON文件中的实例ID列表
        try:
            if not path.exists():
                msg = f"JSON file not found: {path}"
                logger.error(msg)
                raise FileNotFoundError(msg)
                
            with open(path, 'r') as f:
                id_list_data = json.load(f)
                
            if self.key not in id_list_data:
                msg = f"Key '{self.key}' not found in JSON file {path}"
                logger.error(msg)
                raise ValueError(msg)
                
            instance_ids = id_list_data[self.key]
            if not instance_ids:
                msg = f"No instance IDs found in key '{self.key}' in JSON file {path}"
                logger.error(msg)
                raise ValueError(msg)
                
            logger.info(f"Loaded {len(instance_ids)} instance IDs from {path}")
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON format in {path}: {e}"
            logger.error(msg)
            raise ValueError(msg)
        except Exception as e:
            msg = f"Failed to load instance IDs from {path}: {e}"
            logger.error(msg)
            raise ValueError(msg)

        # 创建正则表达式来匹配指定的实例ID
        filter_regex = "|".join(instance_ids)
        logger.info(f"Created filter regex for {len(instance_ids)} instance IDs")
        
        # 加载数据集
        dataset_path = self._get_dataset_path()
        logger.info(f"Loading dataset from {dataset_path}, split={self.split}")
        ds: list[dict[str, Any]] = load_dataset(dataset_path, split=self.split)  # type: ignore
        logger.info(f"Loaded {len(ds)} instances from dataset")

        if isinstance(self.deployment, DockerDeploymentConfig):
            self.deployment.platform = "linux/amd64"

        # 创建所有实例
        logger.info("Creating instances...")
        all_instances = [
            SimpleBatchInstance.from_swe_bench(instance).to_full_batch_instance(self.deployment) for instance in ds
        ]
        logger.info(f"Created {len(all_instances)} instances")
        
        # 过滤实例
        logger.info(f"Filtering instances with regex: {filter_regex[:100]}..." if len(filter_regex) > 100 else f"Filtering instances with regex: {filter_regex}")
        instances = _filter_batch_items(all_instances, filter_=filter_regex, shuffle=self.shuffle)
        logger.info(f"Found {len(instances)} matching instances")
        
        # 检查是否找到了所有指定的实例
        found_ids = {instance.problem_statement.id for instance in instances}
        missing_ids = [id for id in instance_ids if id not in found_ids]
        
        if missing_ids:
            logger.warning(f"Could not find {len(missing_ids)} instance IDs: {', '.join(missing_ids[:5])}" + 
                         (f"... and {len(missing_ids) - 5} more" if len(missing_ids) > 5 else ""))
        else:
            logger.info("All specified instance IDs were found in the dataset")
        
        return instances

    @property
    def id(self) -> str:
        return f"id_list_{self.path.stem}_{self.subset}_{self.split}"


BatchInstanceSourceConfig = (
    InstancesFromHuggingFace | InstancesFromFile | SWEBenchInstances | ExpertInstancesFromFile | SWESmithInstances | InstancesFromIdList
)
