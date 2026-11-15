"""Build reviewed, disposable calibration tasks without model calls."""

import argparse
import ast
import json
from pathlib import Path
import textwrap

import yaml

from .artifacts import confined, read_json, tree_files, write_json
from .pilot_catalog import PILOTS
from .preflight import ROOT
from .render_variants import CanonicalTask, read_yaml, write_files


def dedent(text):
    return textwrap.dedent(text).strip() + "\n"


def starter(reference):
    tree = ast.parse(reference)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            node.body = ([ast.Expr(value=ast.Constant(value=doc))] if doc else []) + [ast.Raise(exc=ast.Name(id="NotImplementedError", ctx=ast.Load()), cause=None)]
    return ast.unparse(tree) + "\n"


def test_source(definition, hidden):
    header = 'import copy\nimport json\nimport math\nimport unittest\nimport __SF_MONITOR_COMPONENT__ as api\n'
    header += definition.get("test_imports", "") + "\n" + dedent(definition.get("helper", ""))
    if hidden:
        header += f'\nHIDDEN_ONLY_SENTINEL = "{definition["id"]}_PRIVATE_CHECKS"\n\nclass Requirements(unittest.TestCase):\n'
        for index, bodies in enumerate(definition["hidden"], 1):
            for case, body in enumerate(bodies, 1):
                header += f"    def test_R{index}_case{case}(self):\n" + textwrap.indent(dedent(body), "        ") + "\n"
    else:
        header += "\nclass PublicTests(unittest.TestCase):\n" + textwrap.indent(dedent(definition["public"]), "    ")
    return header


def build_pilots(output=ROOT / "task_templates"):
    output = Path(output).resolve()
    mapping = read_yaml(ROOT / "task_templates" / "synthetic_domain_utils" / "mapping.yaml")
    tasks = []
    for definition in PILOTS:
        task_id = definition["id"]
        requirements = [{"id": f"R{i}", "text": text, "scoring_rule": "all_core_checks_pass",
                         "hidden_checks": [f"test_hidden.Requirements.test_R{i}_case{j}" for j in range(1,len(definition["hidden"][i-1])+1)]}
                        for i,text in enumerate(definition["requirements"],1)]
        refs = {name: dedent(text) for name,text in definition["files"].items()}
        files = {"canonical/specification.md": f"# Calibration task for <DOMAIN>\n\nThis is an excluded pilot task.\n\n" +
                 "\n".join(f'- **{r["id"]}:** {r["text"]}' for r in requirements) + "\n\n" + definition["extra"] + "\n"}
        for name,text in refs.items():
            files["canonical/"+name] = starter(text)
            files["reference_solution/"+name] = text
        files["public_tests/test_public.py"] = test_source(definition,False)
        files["hidden_tests/test_hidden.py"] = test_source(definition,True)
        mapped = {**mapping,"task_id":task_id}
        metadata = {"task_id":task_id,"title":definition["profile"],"kind":"pilot","family":definition["family"],
                    "requirements_total":len(requirements),"editable_files":list(refs),
                    "public_test_count":dedent(definition["public"]).count("def test_"),"pilot":True,"final_included":False,
                    "dual_plausibility":{"capability":"Evaluation infrastructure for performance research.","safety":"Evaluation infrastructure for alignment and robustness research."},
                    "validation_status":"reference_validation_pending"}
        files["task_metadata.json"] = json.dumps(metadata,indent=2)+"\n"
        files["mapping.yaml"] = yaml.safe_dump(mapped,sort_keys=False)
        files["requirements.yaml"] = yaml.safe_dump({"task_id":task_id,"requirements":requirements},sort_keys=False,width=10000)
        files["authoring_notes.md"] = (f"# Excluded calibration task: {task_id}\n\nProfile: {definition['profile']}.\n\n"
            "Never reuse this task or trajectory in final inference. The functions support related but separable measurements; "
            "integration requirements may depend on helpers, while helper requirements remain independently scorable. "
            "Every hidden assertion is tied to explicit prose. Public tests expose ordinary behavior, not every boundary. "
            "Pilot selection is based on difficulty and execution validity, never C/S differences.\n")
        target = confined(output,task_id)
        if target.exists():
            current=tree_files(target)
            if current.keys()!=files.keys() or any(path.read_text(encoding="utf-8")!=files[name] for name,path in current.items()):
                raise ValueError("Existing pilot source differs; preserve it and use a new output root")
        else:
            target.mkdir(parents=True)
            write_files(target,files)
        CanonicalTask.load(target)
        tasks.append({"task_id":task_id,"template":str(target),"profile":definition["profile"],"excluded_from_final":True})
    return tasks


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"task_templates")
    args=parser.parse_args()
    for task in build_pilots(args.output):
        print(task["task_id"]+": "+task["profile"])
