"""Upload a demo's generated contract PDFs to the S3 bucket Wisdom's S3 connection reads.

`demo s3 <name> [--apply]`. Bucket, region, prefix and the uploader key come from `.env`
(the variable names are set in demo.yaml `s3:` — bucket_env / region_env / prefix_env — so
one bucket can serve several demos under different prefixes). Idempotent: an object whose
size already matches is skipped. Secrets are never printed.
"""
from __future__ import annotations

import os
from pathlib import Path

from .spec import DemoSpec


def s3_settings(spec: DemoSpec) -> dict:
    from . import config
    config.load_env()   # `demo s3` can be the first command of a session: read .env like every other command
    cfg = dict(spec.raw.get("s3") or {})
    bucket = os.getenv(cfg.get("bucket_env", "S3_BUCKET"), "")
    region = os.getenv(cfg.get("region_env", "S3_REGION"), "us-east-1")
    prefix = os.getenv(cfg.get("prefix_env", "S3_PREFIX"), "").strip("/")
    sub = str(cfg.get("subfolder") or "contracts").strip("/")
    key_prefix = "/".join(p for p in (prefix, sub) if p)
    return {"bucket": bucket, "region": region, "prefix": prefix, "key_prefix": key_prefix,
            "local_dir": spec.dir / str((spec.raw.get("generated_documents") or {}).get("out") or "build/contracts")}


def _client(region: str):
    import boto3

    return boto3.client("s3", region_name=region, aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"))


def sync(spec: DemoSpec, *, apply: bool, echo: bool = True) -> dict:
    s = s3_settings(spec)
    if not s["bucket"]:
        return {"ok": False, "error": "S3 bucket not configured (set S3_BUCKET in .env)"}
    if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
        return {"ok": False, "error": "AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY not set in .env"}
    files = sorted(Path(s["local_dir"]).glob("*.pdf"))
    if not files:
        return {"ok": False, "error": f"no PDFs in {s['local_dir']} — run `demo docs` first"}
    c = _client(s["region"])
    existing: dict[str, int] = {}
    token = None
    while True:
        kw = {"Bucket": s["bucket"], "Prefix": s["key_prefix"] + "/"}
        if token:
            kw["ContinuationToken"] = token
        r = c.list_objects_v2(**kw)
        for o in r.get("Contents") or []:
            existing[o["Key"]] = int(o["Size"])
        token = r.get("NextContinuationToken")
        if not token:
            break
    todo = [f for f in files if existing.get(f"{s['key_prefix']}/{f.name}") != f.stat().st_size]
    if not apply:
        return {"ok": True, "dry_run": True, "bucket": s["bucket"], "prefix": s["key_prefix"], "files": len(files), "would_upload": len(todo), "already_there": len(files) - len(todo)}
    uploaded = []
    for f in todo:
        key = f"{s['key_prefix']}/{f.name}"
        c.upload_file(str(f), s["bucket"], key, ExtraArgs={"ContentType": "application/pdf"})
        uploaded.append(key)
        if echo:
            print(f"  uploaded s3://{s['bucket']}/{key}")
    # read-back
    check = c.list_objects_v2(Bucket=s["bucket"], Prefix=s["key_prefix"] + "/")
    keys = {o["Key"] for o in check.get("Contents") or []}
    missing = [f.name for f in files if f"{s['key_prefix']}/{f.name}" not in keys]
    return {"ok": not missing, "bucket": s["bucket"], "prefix": s["key_prefix"], "files": len(files), "uploaded": len(uploaded),
            "already_there": len(files) - len(todo), "missing_after_upload": missing}
